#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""股东号批量生成：按歌曲批量产出引流短视频（可编辑草稿 + 原生导出成片）。

用法：
    python guzhu_batch.py check  --template <模板.jypack>
    python guzhu_batch.py build  --batch batch.json
    python guzhu_batch.py export --batch batch.json
    python guzhu_batch.py run    --batch batch.json
    python guzhu_batch.py voices
"""
from __future__ import annotations

import argparse
import copy
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
import uuid

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from guzhu_audio import cut_to_wav, detect_chorus, probe  # noqa: E402
from guzhu_anim import (load_sticker_names, pick_animation,  # noqa: E402
                        pick_stickers, prepare_sticker_images)
from guzhu_common import EngineCrypto, GuzhuError, resolve_project  # noqa: E402
from guzhu_jypack import (Package, read_package, repair_media, seal,  # noqa: E402
                          update_metadata)
from guzhu_lyrics import (build_cues, parse_lyric_lines, read_cue_times,  # noqa: E402
                          read_plain_lines)
from guzhu_timeline import (Editor, apply_spec, dump_text_content, even_words,  # noqa: E402
                            inspect_template, new_id, parse_text_content,
                            placeholder_prefix, range_of, remap_words, retitle,
                            set_range, trim_to_chorus)
from guzhu_tts import list_voices, load_line_file, sanitize, synthesize_lines  # noqa: E402

SCHEMA = "guzhu-batch/v1"
MIN_MAIN_US = 5_000_000
SONG_ENTRY = "ImportedMaterials/Used/guzhu-song.wav"
SILENCE_ENTRY = "ImportedMaterials/Used/guzhu-silence.wav"
INTRO_ENTRY = "ImportedMaterials/Used/guzhu-intro.wav"
SONG_FILE = "guzhu-song.wav"


def log(message):
    print(message, flush=True)


def fail(message):
    raise GuzhuError(message)


# --------------------------------------------------------------------------- 清单


def load_batch(path):
    path = Path(path)
    if not path.is_file():
        fail("批次清单不存在：" + str(path))
    try:
        batch = json.loads(path.read_text(encoding="utf-8-sig"))
    except ValueError as error:
        fail("批次清单不是合法 JSON：" + str(error))
    if not isinstance(batch, dict):
        fail("批次清单顶层必须是对象")
    if not batch.get("template"):
        fail("批次清单缺少 template（股东号模板 .jypack 路径）")
    songs = batch.get("songs")
    if not isinstance(songs, list) or not songs:
        fail("批次清单缺少 songs 数组")
    for index, song in enumerate(songs, 1):
        if not isinstance(song, dict) or not song.get("file"):
            fail("第 %d 首歌缺少 file 字段" % index)
        song.setdefault("name", Path(str(song["file"])).stem)
    batch.setdefault("intro", {})
    batch.setdefault("render", {})
    base = path.resolve().parent
    batch["_base"] = str(base)
    return batch


def resolve_path(value, base):
    path = Path(str(value))
    if not path.is_absolute():
        path = Path(base) / path
    return path


def parse_start(value, window_us, duration_us, default_lead_us=5_000_000):
    """把 start 参数解释成源文件内的起点微秒。"""
    if value in (None, "", "auto"):
        return None
    if isinstance(value, (int, float)):
        start_us = int(float(value) * 1_000_000)
    else:
        text = str(value).strip()
        if ":" in text:
            parts = text.split(":")
            seconds = 0.0
            for part in parts:
                seconds = seconds * 60 + float(part)
            start_us = int(seconds * 1_000_000)
        else:
            start_us = int(float(text) * 1_000_000)
    if start_us < 0:
        fail("start 不能为负")
    if start_us + window_us > duration_us:
        fail("start=%.3fs 加窗口 %.3fs 超出歌曲总长 %.3fs"
             % (start_us / 1e6, window_us / 1e6, duration_us / 1e6))
    return start_us


# --------------------------------------------------------------------------- 配音


def _project_script(project, script, arguments, timeout=900):
    """执行核心项目的入口脚本，失败时带出尾部输出。"""
    completed = subprocess.run(
        [sys.executable, str(Path(project) / "engine" / script),
         *[str(item) for item in arguments]],
        capture_output=True, cwd=str(project), timeout=timeout)
    if completed.returncode != 0:
        detail = (completed.stderr.decode("utf-8", "replace").strip()
                  or completed.stdout.decode("utf-8", "replace").strip())[-400:]
        fail("核心项目 %s 失败：%s" % (script, detail))
    return completed.stdout.decode("utf-8", "replace")


def retime_voice(source, target, speed):
    """按倍速重采样配音。

    实测官方 `draft algo tts --speed` 会被接受但**产出时长没有任何变化**，
    因此倍速在这里用 ffmpeg atempo 落地（只改变时长，音色不变）。
    """
    speed = float(speed or 1.0)
    if abs(speed - 1.0) < 0.01:
        shutil.copyfile(source, target)
        return speed
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        fail("PATH 中找不到 ffmpeg，无法按 %.2f 倍速处理配音" % speed)
    # atempo 单次只支持 0.5~2.0，超出范围时串联多级
    filters, remain = [], speed
    while remain > 2.0:
        filters.append("atempo=2.0")
        remain /= 2.0
    while remain < 0.5:
        filters.append("atempo=0.5")
        remain /= 0.5
    filters.append("atempo=%.4f" % remain)
    completed = subprocess.run(
        [ffmpeg, "-v", "error", "-y", "-i", str(source),
         "-filter:a", ",".join(filters), str(target)],
        capture_output=True, timeout=300)
    if completed.returncode != 0 or not Path(target).is_file():
        fail("配音变速失败：" + completed.stderr.decode("utf-8", "replace")[:200])
    return speed


def official_tts_lines(project, template, template_path, root, lines, out_dir,
                       speaker=None, speed=1.3, timeout=900):
    """用剪映官方 TTS 生成话术配音，音色沿用模板里的 TTS 音色。

    官方命令只负责"合成 + 把音频落进草稿"：实测它**不改字幕文本**，也**不重排时间线**
    （替换目标段后与该段之后的原有片段直接重叠）。因此这里只把音频取回来，
    时长计算、片头重排与整条时间线平移仍交给本 skill 的离线逻辑。
    """
    engine = str(Path(project) / "engine")
    if engine not in sys.path:
        sys.path.insert(0, engine)
    import lyra_cli  # noqa: PLC0415 - 官方封装只在官方模式需要

    skeleton = inspect_template(template.timeline)
    if not skeleton.groups:
        fail("模板里没有可用于官方 TTS 的引流组")
    if len(lines) > len(skeleton.groups):
        fail("官方 TTS 只能替换模板已有的 %d 组配音，话术有 %d 句"
             % (len(skeleton.groups), len(lines)))

    if not speaker:
        for node in template.timeline.get("materials", {}).get("audios") or []:
            if node.get("type") == "text_to_audio" and node.get("tone_speaker"):
                speaker = node["tone_speaker"]
                break
    if not speaker:
        fail("模板里没有可沿用的官方音色，请用 intro.tts.speaker 指定")

    # 官方沙箱不接受非 ASCII 路径，临时草稿与工作区都必须用 ASCII 名。
    folder, _ = install_draft(template_path, root, "guzhu-tts-source")
    workspace = Path(tempfile.gettempdir()) / ("guzhu-ws-" + uuid.uuid4().hex[:10])
    if workspace.exists():
        shutil.rmtree(workspace)
    ref = "local://" + folder.name
    try:
        _project_script(project, "draftediting_runtime.py",
                        ["init", "--workspace", workspace], timeout=timeout)
        _project_script(project, "draftediting_runtime.py",
                        ["sync", "--workspace", workspace, "--ref", ref,
                         "--draft-root", root], timeout=timeout)
        id_map = json.loads((workspace / "id_map.json").read_text(encoding="utf-8"))
        by_seg = {item["seg_id"]: item["xml_id"] for item in id_map}
        segments = {}
        xml_ids = []
        for group in skeleton.groups:
            segment = group.subtitle_segment
            if segment is None:
                fail("模板的引流组缺少字幕段，不能作为官方 TTS 的目标")
            xml_id = by_seg.get(segment.get("id"))
            if not xml_id:
                fail("官方工作区里找不到字幕段 " + str(segment.get("id")))
            xml_ids.append(xml_id)
            segments[xml_id] = segment["id"]

        readings = folder / "textReading"
        out_dir.mkdir(parents=True, exist_ok=True)
        produced = []
        for index, text in enumerate(lines):
            before = {item.name for item in readings.iterdir()} if readings.is_dir() else set()
            lyra_cli.draft(["algo", "tts"], str(root), ref,
                           {"--seg-id": segments[xml_ids[index]], "--text": text,
                            "--speaker": speaker, "--speed": "1.0",
                            "--write-to-draft": "true"},
                           timeout=timeout)
            fresh = [item for item in readings.iterdir() if item.name not in before]
            if not fresh:
                fail("官方没有为第 %d 句产出音频" % (index + 1))
            fresh.sort(key=lambda item: item.stat().st_mtime_ns)
            source = fresh[-1]
            target = out_dir / ("official-line-%02d%s" % (index + 1, source.suffix or ".mp3"))
            if target.exists():
                target.unlink()
            # 保留官方原始文件；变速统一交给剪映音频段，不再用本地 atempo 加工。
            shutil.copyfile(source, target)
            source_us = probe(target)["duration_us"]
            produced.append({"text": text, "path": str(target),
                             "source_duration_us": source_us,
                             "duration_us": round(source_us / float(speed or 1.0))})
        return {"speaker": speaker, "lines": produced,
                "files": [item["path"] for item in produced]}
    finally:
        shutil.rmtree(folder, ignore_errors=True)
        shutil.rmtree(workspace, ignore_errors=True)


def prepare_tts(batch, out_dir, project=None, template=None, template_path=None):
    intro = batch.get("intro") or {}
    lines = intro.get("lines")
    if not lines and intro.get("file"):
        lines = load_line_file(resolve_path(intro["file"], batch["_base"]))
    if not lines:
        fail("批次清单的 intro.lines（或 intro.file）必须提供引流话术")
    if not isinstance(lines, list) or not all(isinstance(item, str) and item.strip()
                                              for item in lines):
        fail("intro.lines 必须是非空字符串数组")

    settings = intro.get("tts") or {}
    mode = settings.get("mode", "official")
    speed_key = float(settings.get("speed", 1.3))
    cache_dir = out_dir / "tts"
    report_path = cache_dir / "tts.json"
    text_key = json.dumps([item.strip() for item in lines], ensure_ascii=False)
    if report_path.is_file():
        try:
            cached = json.loads(report_path.read_text(encoding="utf-8"))
        except ValueError:
            cached = None
        if (isinstance(cached, dict) and cached.get("text_key") == text_key
                and cached.get("mode") == mode
                and (mode != "official" or cached.get("pipeline") == "official-raw-native-v1")
                and float(cached.get("speed") or 1.3) == speed_key
                and all(Path(item["path"]).is_file() for item in cached.get("lines", []))):
            return cached
        shutil.rmtree(cache_dir, ignore_errors=True)

    if mode == "official":
        if project is None or template is None or template_path is None:
            fail("official 配音缺少项目或模板上下文")
        produced = official_tts_lines(
            project, template, template_path, draft_root(project),
            [item.strip() for item in lines], cache_dir / "official",
            speaker=settings.get("speaker"),
            speed=float(settings.get("speed", 1.3)),
            timeout=int(settings.get("timeout", 900)))
        result = dict(produced)
        result["pipeline"] = "official-raw-native-v1"
        result["duration_us"] = sum(item["duration_us"] for item in produced["lines"])
        result["mode"] = "official"
        result["voice"] = produced["speaker"]
        result["speaker"] = produced["speaker"]
        result["speed"] = speed_key
        result["text_key"] = text_key
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                               encoding="utf-8")
        return result

    files = settings.get("files")
    if files:
        files = [str(resolve_path(item, batch["_base"])) for item in files]
    result = synthesize_lines([item.strip() for item in lines], cache_dir, mode=mode,
                              voice=settings.get("voice"), rate=int(settings.get("rate", 0)),
                              files=files, gap_ms=int(settings.get("gap_ms", 0)))
    result["text_key"] = text_key
    report_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    return result


# --------------------------------------------------------------------------- 组装


def fork_package(package):
    """克隆一个包用于改写：共享素材字节，隔离时间线与元信息。"""
    return Package(source=package.source, entries=dict(package.entries),
                   timeline=copy.deepcopy(package.timeline),
                   timeline_encrypted=package.timeline_encrypted,
                   metadata=copy.deepcopy(package.metadata),
                   metadata_encrypted=package.metadata_encrypted)


def placeholder_of(package):
    for node in (package.timeline.get("materials", {}).get("audios") or []):
        prefix = placeholder_prefix(node.get("path"))
        if prefix:
            return prefix
    for name, text in package.text_entries():
        prefix = placeholder_prefix(text)
        if prefix:
            return prefix
    fail("模板里找不到草稿占位路径前缀")


def _resolve_main_duration(song_spec, total_us, start_us, intro_us, template_main):
    """决定这首歌的主歌段时长。

    优先级：``main_seconds``（显式秒数）→ ``end``（歌曲内的结束秒数）→ 默认用满歌曲剩余。
    默认会让每首歌自然得到不同长度的主歌段，而不是被模板的固定主歌时长锁死。
    """
    remaining = int(total_us) - int(start_us) - int(intro_us)
    if song_spec.get("main_seconds") is not None:
        main_us = int(round(float(song_spec["main_seconds"]) * 1_000_000))
    elif song_spec.get("end") is not None:
        end_us = int(parse_start(song_spec["end"], 0, total_us))
        main_us = end_us - int(start_us) - int(intro_us)
    else:
        main_us = remaining
    if main_us <= 0:
        fail("主歌段时长为零或为负（歌曲 %.3fs，选段 %.3fs，片头 %.3fs）；请调整 start"
             % (total_us / 1e6, start_us / 1e6, intro_us / 1e6))
    if main_us < MIN_MAIN_US:
        fail("主歌段只剩 %.3fs，太短（歌曲 %.3fs，选段 %.3fs，片头 %.3fs）；"
             "请换更长的歌、调小 start 或减少话术"
             % (main_us / 1e6, total_us / 1e6, start_us / 1e6, intro_us / 1e6))
    return main_us


def generate_silence(path, duration_us):
    """生成一段静音 wav：整首模式下片头只讲 TTS，不再占用歌曲开头。"""
    ffmpeg = shutil.which("ffmpeg") or "ffmpeg"
    completed = subprocess.run(
        [ffmpeg, "-v", "error", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
         "-t", "%.3f" % (max(1, int(duration_us)) / 1e6), "-c:a", "pcm_s16le", str(path)],
        capture_output=True, timeout=180)
    if completed.returncode != 0 or not Path(path).is_file():
        fail("生成静音音轨失败：" + completed.stderr.decode("utf-8", "replace")[:200])
    return path


def build_one(batch, package, tts, song_spec, out_dir, project, crypto):
    base = batch["_base"]
    source = resolve_path(song_spec["file"], base)
    name = str(song_spec["name"])
    safe = sanitize(name)
    info = probe(source)

    skeleton = inspect_template(package.timeline)
    intro_us = sum(int(line["duration_us"]) for line in tts["lines"])
    # 口播说完留一段呼吸再进副歌：话刚落地音乐就砸进来会很突兀。
    intro_tail_us = int(song_spec.get("intro_tail_ms", 400)) * 1000
    intro_us += intro_tail_us
    # 主歌段时长按这首歌的实际情况定，不再套用模板的固定时长：
    #   显式 main_seconds / end 优先；否则从选段起点一路用到歌曲结尾。
    template_main = int(skeleton.main_duration)
    reference_window = intro_us + template_main

    lyrics_path = song_spec.get("lyrics")
    lyrics_file = resolve_path(lyrics_path, base) if lyrics_path else None
    lyric_times = read_cue_times(str(lyrics_file)) if lyrics_file else None
    # 纯文本歌词里单独写一行「副歌」就是在标段：那一行之后的歌词才是副歌。
    # 有了它就不必全曲盲搜起点，按行数比例估个预期位置再在附近收敛即可。
    lyric_lines, chorus_at = ([], None)
    if lyrics_file and Path(lyrics_file).suffix.lower() not in (".lrc", ".srt"):
        lyric_lines, chorus_at = parse_lyric_lines(str(lyrics_file))

    total_us = int(info["duration_us"])
    # audio_layout=full：片头只讲 TTS、不占用歌曲，主歌从歌曲第 1 秒唱到最后一秒。
    # 这样「整首歌 ↔ 整份歌词」天然一一对应，不会再出现"给了完整歌词却少了几行"。
    # 只有显式要求选段（start / main_seconds / end / audio_layout）时才回到 continue。
    # audio_layout 决定片头与主歌怎么分歌曲：
    #   chorus（有歌词时默认）—— 片头垫一段压低 8dB 的背景乐，口播一结束就进副歌(+3dB)；
    #   full   —— 片头只讲 TTS（静音垫乐），主歌从歌曲第 1 秒唱到最后一秒；
    #   continue —— 片头占用歌曲开头、主歌紧接着往下播（旧行为）。
    layout = str(song_spec.get("audio_layout") or "")
    if not layout:
        # 只有"显式指定起点/终点"才算用户要自己选段。
        # main_seconds 只是给副歌限长，不该把布局切回旧的 continue 模式。
        wants_clip = (song_spec.get("end") is not None
                      or (song_spec.get("start") and str(song_spec["start"]) != "auto"))
        if wants_clip:
            layout = "continue"
        elif chorus_at is not None:
            layout = "chorus"
        elif lyrics_file:
            layout = "chorus"
        else:
            layout = "continue"

    if layout == "full":
        start_us = 0
        picked = "full-song"
        main_us = total_us
        window_us = total_us
    elif layout == "chorus":
        # 口播完就是副歌：主歌段从副歌起点一直用到歌曲结尾。
        # 起点优先用本地 ASR 把歌词里的「副歌」标记对到真实时间上；
        # ASR 不可用时才退回"按行数比例 + 附近响度跃升"的估算。
        search = None
        start_us = None
        picked = ""
        forced = song_spec.get("chorus_start_us")
        if forced is not None:
            start_us = int(forced)
            picked = "chorus-given"
        elif chorus_at is not None and lyric_lines:
            # 首选剪映官方识别：它本来就给出每句时间，最准。
            if project is not None and not song_spec.get("_skip_locate"):
                if isinstance(crypto, EngineCrypto):
                    located, why = locate_chorus_by_official(
                        project, draft_root(project), batch, tts, song_spec,
                        package, crypto, out_dir, lyric_lines, chorus_at)
                    if located is not None:
                        start_us = int(located)
                        picked = "chorus-" + why
            if start_us is None:
                # 官方不可用（未登录/无权益/剪映没开）时退回本地 ASR
                located, why = locate_chorus_by_asr(
                    source, lyric_lines, chorus_at, out_dir,
                    model_size=str(song_spec.get("asr_model") or "small"))
                if located is not None:
                    start_us = int(located)
                    picked = "chorus-" + why
        if start_us is None:
            if chorus_at is not None and lyric_lines:
                expected = int(total_us * chorus_at / len(lyric_lines))
                span = max(int(expected * 0.05), 1_000_000)
                search = (max(0, expected - span), min(total_us - 1_000_000, expected + span))
            start_us, basis = detect_chorus(source, reference_window,
                                            min_lead_us=int(song_spec.get("min_lead_ms", 5000)) * 1000,
                                            anchors_ms=lyric_times, intro_us=intro_us,
                                            search_us=search)
            picked = ("chorus-lyrics@%d" % chorus_at if search else "chorus-") + str(basis)
        start_us = max(0, min(int(start_us), max(0, total_us - 1_000_000)))
        # 起势提前量：副歌的伴奏常在开口前就起来，往前留一点会更自然
        lead_ms = int(song_spec.get("chorus_lead_ms", 0) or 0)
        if lead_ms:
            start_us = max(0, start_us - lead_ms * 1000)
            picked += "+lead%dms" % lead_ms
        main_us = total_us - start_us
        # 限长：target_seconds 是"整条成片目标长度"（口播 + 副歌），更好用；
        # main_seconds 则直接给主歌段长度。
        limit_s = song_spec.get("main_seconds")
        target_s = song_spec.get("target_seconds")
        if target_s:
            limit_s = max(5.0, float(target_s) - intro_us / 1e6)
            picked += "+target%ss" % target_s
        if limit_s:
            main_us = min(main_us, int(round(float(limit_s) * 1_000_000)))
            if not target_s:
                picked += "+cap%ss" % limit_s
        window_us = main_us
    else:
        start_us = parse_start(song_spec.get("start"), reference_window, total_us)
        picked = "manual"
        if start_us is None:
            # 自动选段以"模板主歌时长"作参考窗口找副歌位置，避免落到前奏/间奏上。
            start_us, picked = detect_chorus(source, reference_window,
                                             min_lead_us=int(song_spec.get("min_lead_ms", 5000)) * 1000,
                                             anchors_ms=lyric_times, intro_us=intro_us)
        main_us = _resolve_main_duration(song_spec, total_us, start_us, intro_us, template_main)
        window_us = intro_us + main_us
        if start_us + window_us > total_us:
            start_us = max(0, total_us - window_us)

    songs_dir = out_dir / "songs"
    songs_dir.mkdir(parents=True, exist_ok=True)
    song_wav = songs_dir / (safe + ".wav")
    if song_wav.exists():
        song_wav.unlink()
    main_gain = float(song_spec.get("main_gain_db", 3.0 if layout == "chorus" else 0.0))
    # 副歌轻轻淡入，避免音量从口播档直接跳到 +3dB 时"嗡"地一下
    main_fade_in = (int(song_spec.get("main_fade_in_ms", 250)) * 1000
                    if layout == "chorus" else 0)
    # 结尾渐弱：歌曲是硬切的，收尾加淡出才不显得戛然而止
    main_fade_out = (int(song_spec.get("main_fade_out_ms", 900)) * 1000
                     if layout == "chorus" else 0)
    native_audio = bool((batch.get("media") or {}).get("native_audio"))
    if native_audio:
        # 原歌曲不烘焙裁切、增益或渐弱；源时间由草稿范围指定，效果由官方 CLI 添加。
        shutil.copyfile(source, song_wav)
        cut = {"duration_us": window_us}
    else:
        cut = cut_to_wav(source, song_wav, start_us, window_us, gain_db=main_gain,
                         fade_in_us=main_fade_in, fade_out_us=main_fade_out)
    clip_us = cut["duration_us"]
    # 允许一帧级的取整误差，并以实际裁剪长度为准（否则 31.062s 会被判成"短于"31.062s）
    if clip_us + 50_000 < window_us:
        fail("裁剪结果比窗口短（%.3fs < %.3fs），检查源文件是否损坏"
             % (clip_us / 1e6, window_us / 1e6))
    window_us = clip_us
    if layout in ("full", "chorus"):
        main_us = clip_us
    else:
        main_us = max(1, clip_us - intro_us)

    # 口播时**要有背景音乐**（压低 8dB，让人声占主导），口播一结束就进副歌(+3dB)。
    # 片头垫乐必须是独立素材：模板里片头与主歌共用同一个音乐素材，
    # 直接改它会把主歌一起改掉。`intro_gain_db: null` 才切成静音。
    intro_audio_wav = None
    if layout in ("chorus", "full"):
        gain = song_spec.get("intro_gain_db", -8.0)
        if native_audio:
            intro_audio_wav = songs_dir / (safe + "-intro.wav")
            shutil.copyfile(source, intro_audio_wav)
        elif gain is None:
            intro_audio_wav = songs_dir / (safe + "-silence.wav")
            if intro_audio_wav.exists():
                intro_audio_wav.unlink()
            generate_silence(intro_audio_wav, intro_us)
        else:
            intro_audio_wav = songs_dir / (safe + "-intro.wav")
            if intro_audio_wav.exists():
                intro_audio_wav.unlink()
            if layout == "chorus":
                # 片头垫乐取"副歌前的那几秒"（而不是歌曲开头），这样它和主歌首尾相接，
                # 音乐不会从开头硬跳到副歌；尾部再淡出，配合主歌淡入完成过渡。
                lead = int(intro_us)
                bgm_start = max(0, int(start_us) - lead)
                cut_to_wav(source, intro_audio_wav, bgm_start, lead, gain_db=float(gain),
                           fade_out_us=int(song_spec.get("intro_fade_out_ms", 400)) * 1000)
            else:
                cut_to_wav(source, intro_audio_wav, 0, intro_us, gain_db=float(gain))

    # 歌词走官方链路时，build 阶段不生成任何歌词段——官方识别会在 export 时
    # 生成自己的 <text> 段，两套歌词同时存在会重叠。
    official_lyrics = str((batch.get("lyrics") or {}).get("engine") or "official") == "official"
    lyrics_us = 0
    cues = []
    if lyrics_file and not official_lyrics:
        cues = build_cues(str(lyrics_file), start_us, intro_us, window_us)
        lyrics_us = len(cues)

    prefix = placeholder_of(package)
    package = fork_package(package)

    background = None
    background_entry = None
    background_file = None
    background_setting = (batch.get("media") or {}).get("background")
    if background_setting:
        background_file = resolve_path(background_setting, base)
        if not background_file.is_file():
            fail("背景图不存在：" + str(background_file))
        background_entry = "ImportedMaterials/Used/guzhu-bg" + (background_file.suffix or ".jpg")
        width, height = image_size(background_file)
        background = {"entry_path": prefix + "/" + background_entry,
                      "name": background_file.name, "width": width, "height": height}
        log("  背景图：%s（%dx%d）" % (background_file.name, width, height))

    # 片头贴纸：按每句话术的情绪从本地可用贴纸里挑（官方素材搜索需要联网，
    # 当前 lyra-cli 没给 material 命令开放网络，所以用扫草稿攒的名称词典）。
    stickers = []
    if str((batch.get("media") or {}).get("stickers", "auto")) != "off":
        stickers = pick_stickers([str(item.get("text") or "") for item in tts["lines"]],
                                 name_map=load_sticker_names())
        if stickers:
            # 统一尺寸：贴纸段里各位的 scale 是按各自素材调的，直接换图会大小失控，
            # 所以把选中的贴纸都规整到同一画布尺寸（并带上效果定义文件）。
            stickers = prepare_sticker_images(stickers, out_dir)
            log("  片头贴纸：%s" % "、".join(item["name"][:12] for item in stickers))

    line_specs = []
    for index, line in enumerate(tts["lines"]):
        entry = "textReading/guzhu-line-%02d.wav" % (index + 1)
        line_specs.append({"text": line["text"], "duration_us": line["duration_us"],
                           "entry": entry, "entry_path": prefix + "/" + entry,
                           "path": line["path"]})
    spec = {
        "intro_lines": line_specs,
        "lyrics": cues,
        "lyrics_mode": str(((batch.get("lyrics") or {}).get("mode")) or "subtitle"),
        "main_duration_us": main_us,
        "audio_layout": layout,
        "background": background,
        "stickers": stickers,
        "song": {"name": SONG_FILE, "file_name": source.name,
                 "entry_path": prefix + "/" + SONG_ENTRY,
                 "duration_us": clip_us, "start_us": 0, "source_duration_us": clip_us},
    }
    silence_wav = None
    if intro_audio_wav is not None:
        spec["intro_audio_entry"] = prefix + "/" + INTRO_ENTRY
    report = apply_spec(package.timeline, spec)
    if native_audio:
        # 编排仅保存原素材与时间范围，不进行本地音频处理。
        native_skeleton = inspect_template(package.timeline)
        native_editor = Editor(package.timeline)
        for _track, segment, material_id in native_skeleton.main_music:
            set_range(segment, "source_timerange", start_us, main_us)
            node = native_editor.node(material_id)
            if node is not None:
                node["duration"] = total_us
        for _track, segment, material_id in native_skeleton.intro_music:
            set_range(segment, "source_timerange", max(0, start_us - intro_us), intro_us)
            node = native_editor.node(material_id)
            if node is not None:
                node["duration"] = total_us
        for group, line in zip(native_skeleton.groups, tts["lines"]):
            if group.tts_segment is not None and line.get("source_duration_us"):
                set_range(group.tts_segment, "source_timerange", 0, int(line["source_duration_us"]))
    if tts.get("pipeline") == "official-raw-native-v1":
        raw_skeleton = inspect_template(package.timeline)
        raw_editor = Editor(package.timeline)
        for group, line in zip(raw_skeleton.groups, tts["lines"]):
            if group.tts_segment is not None:
                set_range(group.tts_segment, "source_timerange", 0, line["source_duration_us"])
                material = raw_editor.node(group.tts_segment.get("material_id"))
                if material is not None:
                    material["duration"] = line["source_duration_us"]
    update_metadata(package, draft_name=name, song=spec["song"])

    package.replace(SONG_ENTRY, song_wav.read_bytes())
    if intro_audio_wav is not None:
        package.replace(INTRO_ENTRY, intro_audio_wav.read_bytes())
    if background_entry and background_file:
        package.replace(background_entry, background_file.read_bytes())
    for line in line_specs:
        package.replace(line["entry"], Path(line["path"]).read_bytes())

    repair = repair_media(package, out_dir / "repair",
                          color=str((batch.get("media") or {}).get("solid_color", "black")))
    if repair["blocked"]:
        fail("包内素材不可读且无法自动修复，已停止而不是交出残缺成片："
             + json.dumps(repair["blocked"], ensure_ascii=False))

    jypack_dir = out_dir / "jypack"
    jypack_dir.mkdir(parents=True, exist_ok=True)
    target = jypack_dir / (safe + ".jypack")
    if target.exists():
        target.unlink()
    sealed = seal(package, crypto, target, timeline_id=new_id(), prune=True)

    return {
        "name": name,
        "safe_name": safe,
        "source": str(source),
        "lyrics_source": str(lyrics_file) if lyrics_file else None,
        "chorus_at": chorus_at,
        "source_duration_us": info["duration_us"],
        "start_us": start_us,
        "start_pick": picked,
        "audio_layout": layout,
        "native_audio": native_audio,
        "main_gain_db": main_gain,
        "intro_gain_db": song_spec.get("intro_gain_db", -8.0),
        "main_fade_in_us": main_fade_in,
        "main_fade_out_us": main_fade_out,
        "window_us": window_us,
        "clip_us": clip_us,
        "song_file": str(song_wav),
        "jypack": str(target),
        "jypack_bytes": target.stat().st_size,
        "pruned_assets": len(sealed["pruned"]),
        "repaired_media": repair["repaired"],
        "timeline": report,
        "lyric_cues": lyrics_us,
        "status": "built",
    }


# --------------------------------------------------------------------------- 导出


def draft_root(project):
    """剪映本地草稿根；安装草稿与原生渲染都要在这里。"""
    engine = str(Path(project) / "engine")
    if engine not in sys.path:
        sys.path.insert(0, engine)
    import windows_runtime

    root = Path(windows_runtime.DRAFT_ROOT)
    if not root.is_dir():
        fail("剪映本地草稿目录尚未初始化：" + str(root))
    return root.resolve()


def install_draft(jypack, root, name):
    """把生成的包解包成草稿根下的草稿目录（name 是完整目录名）。

    剪映主进程在运行时不会响应 `-open-draft-pack`（单实例应用把参数吞掉），
    而原生渲染只要求草稿根下存在同 id 的草稿，因此直接落盘更可靠，
    也不会打断用户正在使用的剪映。官方 CLI 沙箱不接受非 ASCII 路径，
    需要走官方歌词链路时目录名必须是 ASCII。
    """
    package = read_package(jypack, None, decrypt=False)
    folder = Path(root) / name
    if folder.exists():
        shutil.rmtree(folder)
    folder.mkdir(parents=True)
    count = 0
    for name in package.names():
        if name.endswith("/"):
            continue
        target = folder / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(package.read(name))
        count += 1
    return folder, count


LYRIC_ANIMATION_DEFAULT = "7591420714515844395"
TEXT_SEGMENT_RE = re.compile(r'<text id="([^"]+)"[^>]*>(?:(?!</text>).)*?</text>', re.S)


def _mirror_draft(folder):
    """把官方写进 Timelines/<id>/ 的时间线同步到根目录与 template-2.tmp。

    官方 CLI 只写 `Timelines/<id>/draft_content.json`，而渲染读取时优先取根文件，
    不显式同步就会出现"草稿改了、成片没变"。
    """
    timelines = sorted((Path(folder) / "Timelines").glob("*/draft_content.json"))
    if not timelines:
        fail("草稿目录里没有时间线文件：" + str(folder))
    source = max(timelines, key=lambda path: path.stat().st_mtime_ns)
    for mirror in (Path(folder) / "draft_content.json", Path(folder) / "template-2.tmp",
                   source.parent / "template-2.tmp"):
        shutil.copyfile(source, mirror)
    return source.parent.name


def _text_material_ids(folder):
    """列出草稿里现有的全部文字素材 id（用于定位官方新生成的歌词段）。"""
    engine = str(Path(folder).parent)
    import windows_runtime  # noqa: PLC0415

    timelines = sorted((Path(folder) / "Timelines").glob("*/draft_content.json"))
    if not timelines:
        return set()
    source = max(timelines, key=lambda path: path.stat().st_mtime_ns)
    timeline = windows_runtime._decrypt_metadata_in_memory(source)
    return {node.get("id") for node in (timeline.get("materials", {}).get("texts") or [])
            if isinstance(node, dict) and node.get("id")}


def _recognized_text(node):
    """取文本素材当前的纯文本（覆盖前就是官方识别结果）。"""
    raw = node.get("recognize_text")
    if isinstance(raw, str) and raw.strip():
        return raw
    content = node.get("content")
    if isinstance(content, dict):
        return str(content.get("text") or "")
    if isinstance(content, str):
        found = re.findall(r">([^<>]+)</text>", content)
        return "".join(found) if found else content
    return ""


def _similarity(left, right):
    """字符计数的 Dice 系数：对同音错字不敏感，用来判断两边是不是同一句。"""
    from collections import Counter  # noqa: PLC0415 - 只为这里的一次比较
    first = [ch for ch in str(left) if ch.strip()]
    second = [ch for ch in str(right) if ch.strip()]
    if not first or not second:
        return 0.0
    common = sum((Counter(first) & Counter(second)).values())
    return 2.0 * common / (len(first) + len(second))


def _align_lyrics(seg_texts, lines):
    """把歌词行按顺序对到官方识别段上（动态规划）。

    官方识别虽然有个别同音错字，但**句子内容和顺序**是可靠的；而纯文本歌词
    没有时间戳，只能靠"顺序 + 内容"来对。这里以「段的识别文本 ↔ 若干连续歌词行」
    的字符相似度为代价做单调对齐，等于用识别结果反过来校正分行位置：
    识别成一句话的几行会被分到同一段，识别不出的行会被自然跳过。
    返回每段用掉的行区间与平均代价。
    """
    count, total = len(seg_texts), len(lines)
    if not count or not total:
        return [], 1.0
    infinity = float("inf")
    dp = [[infinity] * (total + 1) for _ in range(count + 1)]
    back = [[None] * (total + 1) for _ in range(count + 1)]
    for column in range(total + 1):
        dp[0][column] = 0.0
    for row in range(1, count + 1):
        for column in range(0, total + 1):
            best, arg = infinity, None
            # split 允许等于 column：这一句识别文本不作数，不分配任何歌词行。
            # 唱歌的 ASR 常比歌词多切出几句（拖腔、和声），必须容忍段数多于行数。
            for split in range(0, column + 1):
                if dp[row - 1][split] == infinity:
                    continue
                span = "".join(lines[split:column])
                cost = dp[row - 1][split] + (1.0 - _similarity(seg_texts[row - 1], span))
                if cost < best:
                    best, arg = cost, split
            dp[row][column], back[row][column] = best, arg
    end = min(range(0, total + 1), key=lambda column: dp[count][column])
    plans, row, column = [], count, end
    while row > 0:
        split = back[row][column]
        if split is None:
            split = row - 1
        plans.append((split, column))
        row, column = row - 1, split
    plans.reverse()
    return plans, (dp[count][end] / count if dp[count][end] != infinity else 1.0)


def recognize_lyrics(project, root, folder, timeline, settings):
    """只跑一次剪映官方歌词识别，返回每句在草稿时间轴上的时间与文本。

    不改草稿（不覆盖文本、不套动效），专门用来"听清整首歌"，
    从而把歌词里的段落标记对到真实时间上。
    """
    engine = str(Path(project) / "engine")
    if engine not in sys.path:
        sys.path.insert(0, engine)
    import lyra_cli  # noqa: PLC0415

    skeleton = inspect_template(timeline)
    if not skeleton.main_music:
        fail("模板里没有主歌音乐段，无法限定识别范围")
    music_segment = skeleton.main_music[0][1].get("id")
    folder = Path(folder)
    ref = "local://" + folder.name
    workspace = Path(tempfile.gettempdir()) / ("guzhu-recognize-%s" % uuid.uuid4().hex[:8])
    try:
        _project_script(project, "draftediting_runtime.py", ["init", "--workspace", workspace])
        _project_script(project, "draftediting_runtime.py",
                        ["sync", "--workspace", workspace, "--ref", ref,
                         "--draft-root", root])
        id_map = json.loads((workspace / "id_map.json").read_text(encoding="utf-8"))
        if music_segment not in {item["seg_id"] for item in id_map}:
            fail("官方工作区里找不到主歌音乐段，无法限定识别范围")
        before_ids = _text_material_ids(folder)
        lyra_cli.lyrics_recognize(str(root), ref,
                                  language=str(settings.get("language") or "zh"),
                                  mode="segment", seg_id=music_segment,
                                  timeout=int(settings.get("recognize_timeout", 1800)))
        _mirror_draft(folder)
        return recognized_rows(project, folder, before_ids)
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


def chorus_time_from_rows(rows, chorus_at, lines):
    """把「副歌」标记对到识别结果上，返回草稿时间。

    取副歌**前一句的结束时间**：副歌紧接前一句唱完开始，而识别常把副歌首句
    切成两句，按内容匹配会把整行配到后半句、导致起点偏晚。
    """
    plans, _cost = _align_lyrics([str(item.get("text") or "") for item in rows], lines)
    target = int(chorus_at)
    if target > 0:
        for index, (low, high) in enumerate(plans):
            if low <= target - 1 < high:
                return int(rows[index]["start_us"]) + int(rows[index]["duration_us"])
    for index, (low, high) in enumerate(plans):
        if low <= target < high:
            return int(rows[index]["start_us"])
    return None


def locate_chorus_by_official(project, root, batch, tts, song_spec, package, crypto,
                              out_dir, lines, chorus_at):
    """用剪映官方识别整首歌来定位「副歌」的真实起点（带缓存）。

    剪映的歌词识别本来就给出每句时间，直接拿它当基准最准。做法是先用"整首"
    布局建一个探测草稿、识别一遍，再和歌词顺序对齐取副歌起唱点。
    结果按（歌曲 + 歌词 + 标记位置）缓存，同一首歌只探测一次。
    """
    import hashlib  # noqa: PLC0415

    key = hashlib.sha256(("%s|%s|%s|official"
                          % (song_spec.get("file"), "\n".join(lines), chorus_at)
                          ).encode("utf-8")).hexdigest()[:16]
    cache = Path(out_dir) / "chorus-official.json"
    if cache.is_file():
        try:
            data = json.loads(cache.read_text(encoding="utf-8"))
        except ValueError:
            data = {}
        if data.get("key") == key and data.get("chorus_us"):
            return int(data["chorus_us"]), "official-cache"

    probe_dir = Path(out_dir) / "locate"
    probe_spec = dict(song_spec, audio_layout="full", _skip_locate=True)
    probe = build_one(batch, fork_package(package), tts, probe_spec, probe_dir, project, crypto)
    folder, _count = install_draft(probe["jypack"], root, ascii_draft_name("locate", 99))
    try:
        try:
            rows = recognize_lyrics(project, root, folder, package.timeline,
                                    {"engine": "official"})
        except Exception as error:  # noqa: BLE001
            # 长歌整首识别的返回体会非常大，官方可能直接判失败；
            # 这里不该让整条流程挂掉，交给调用方回退到本地 ASR 定位。
            log("  官方识别不可用（%s），改用本地 ASR 定位副歌" % type(error).__name__)
            return None, "official-failed(%s)" % type(error).__name__
        if not rows:
            return None, "official-empty"
        chorus_abs = chorus_time_from_rows(rows, chorus_at, lines)
        if chorus_abs is None:
            return None, "official-unmatched"
        intro_us = int(probe["timeline"]["intro_after_us"])
        chorus_us = max(0, int(chorus_abs) - intro_us)
        try:
            cache.write_text(json.dumps(
                {"key": key, "chorus_us": chorus_us, "rows": rows},
                ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        except OSError:
            pass
        return chorus_us, "official"
    finally:
        shutil.rmtree(folder, ignore_errors=True)


def locate_chorus_by_asr(source, lines, chorus_at, out_dir, model_size="small"):
    """用本地 ASR 把歌词里的「副歌」标记对到歌曲时间轴上。

    唱歌的 ASR 文本会有大量同音错字，但**句子边界与先后顺序是准的**；与歌词行
    做单调对齐后，"副歌第一行"落在哪一句，那一句的开始时间就是裁剪点。
    这条路不依赖剪映、不消耗账号权益，结果按（歌曲 + 歌词 + 标记位置）缓存，
    同一首歌只算一次。返回 ``(起点微秒或 None, 依据)``。
    """
    import hashlib  # noqa: PLC0415

    source = Path(source)
    digest = hashlib.sha256()
    digest.update(source.name.encode("utf-8"))
    digest.update(str(source.stat().st_size).encode("utf-8"))
    digest.update("\n".join(lines).encode("utf-8"))
    digest.update(str(chorus_at).encode("utf-8"))
    key = digest.hexdigest()[:16]

    cache = Path(out_dir) / "chorus-locate.json"
    if cache.is_file():
        try:
            data = json.loads(cache.read_text(encoding="utf-8"))
        except ValueError:
            data = {}
        if data.get("key") == key and data.get("chorus_us"):
            return int(data["chorus_us"]), "asr-cache"

    for name in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY",
                 "http_proxy", "https_proxy", "all_proxy"):
        os.environ.pop(name, None)
    os.environ["NO_PROXY"] = "*"
    os.environ["no_proxy"] = "*"
    try:
        from faster_whisper import WhisperModel  # noqa: PLC0415 - 可选依赖
    except Exception as error:  # noqa: BLE001 - 缺依赖时回退到能量估算
        return None, "asr-missing(%s)" % type(error).__name__

    work = Path(out_dir) / "asr"
    work.mkdir(parents=True, exist_ok=True)
    mono = work / "song-16k.wav"
    if mono.exists():
        mono.unlink()
    ffmpeg = shutil.which("ffmpeg") or "ffmpeg"
    done = subprocess.run([ffmpeg, "-v", "error", "-y", "-i", str(source),
                           "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(mono)],
                          capture_output=True, timeout=600)
    if done.returncode != 0 or not mono.is_file():
        return None, "asr-decode-failed"
    try:
        # local_files_only：模型已在本机缓存，禁止联网就不会去碰那些畸形的
        # 代理环境变量（httpx 解析它们时会抛 InvalidURL）。
        model = WhisperModel(model_size, device="cpu", compute_type="int8",
                             local_files_only=True)
        segments, _info = model.transcribe(str(mono), language="zh", beam_size=1)
        rows = [(float(seg.start), float(seg.end), str(seg.text).strip()) for seg in segments]
    except Exception as error:  # noqa: BLE001
        return None, "asr-failed(%s: %s)" % (type(error).__name__, str(error)[:80])
    if not rows:
        return None, "asr-empty"

    plans, _cost = _align_lyrics([item[2] for item in rows], lines)
    target = int(chorus_at)
    chorus_us = None
    if target > 0:
        # 副歌紧接前一句唱完开始：取"副歌前一行"那一句的结束时间。
        # ASR 常把副歌首句切成两句，靠内容匹配会把整行配到后半句而偏晚；
        # 用前一句的尾时间既绕开这个问题，也正好就是副歌的起唱点。
        for index, (low, high) in enumerate(plans):
            if low <= target - 1 < high:
                chorus_us = int(round(rows[index][1] * 1e6))
                break
    if chorus_us is None:
        for index, (low, high) in enumerate(plans):
            if low <= target < high:
                chorus_us = int(round(rows[index][0] * 1e6))
                break
    if chorus_us is None:
        return None, "asr-unmatched"
    try:
        cache.write_text(json.dumps(
            {"key": key, "chorus_us": chorus_us, "model": model_size,
             "segments": [{"start": round(a, 3), "end": round(b, 3), "text": c}
                          for a, b, c in rows]},
            ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except OSError:
        pass
    return chorus_us, "asr-%s" % model_size


# 画面特效：本地有实体的才敢用（缺资源的官方会联网下载，沙箱没有网络）。
# 名称同样是扫草稿发现的——素材缓存里这些资源都没有名字。
VIDEO_EFFECTS = {
    "film": ("7631600978600480036", "富士影片"),
    "clean": ("7605630861400083763", "佳能清透感"),
}


def apply_video_effect(project, root, folder, key="film"):
    """给主歌画面段套官方画面特效。

    ``draft video effect add`` 是剪映官方的画面特效通道（富士影片、佳能清透感…），
    通过官方资源 ID 下载及套用；缓存缺失不能成为跳过的理由。
    套用后核对视频段的真实效果引用，最终仍须同帧开关对比验收。
    """
    engine = str(Path(project) / "engine")
    if engine not in sys.path:
        sys.path.insert(0, engine)
    import lyra_cli  # noqa: PLC0415
    from guzhu_anim import animation_cache_dir  # noqa: PLC0415

    selected = VIDEO_EFFECTS.get(str(key))
    if selected is None:
        if str(key).isdigit():
            selected = (str(key), "官方在线画面特效")
        else:
            raise RuntimeError("未知画面特效配置，禁止静默替换成富士影片：" + str(key))
    resource, name = selected
    if not resource_is_local(resource):
        from official_materials import execute
        downloaded = execute(project, ["material", "download", "--type", "effect",
                                       "--resource-id", resource])
        if "envelope" not in downloaded:
            raise RuntimeError("官方画面特效下载失败：" + str(downloaded.get("error")))

    timeline, _path = read_draft_timeline(project, folder)
    editor = Editor(timeline)
    skeleton = inspect_template(timeline)
    if not skeleton.main_music:
        return None
    intro_us = range_of(skeleton.main_music[0][1])[0]
    target_id = None
    if skeleton.video_track is not None:
        for segment in skeleton.video_track.get("segments") or []:
            start, _duration = range_of(segment)
            # 容差放宽到 100ms：经过官方 CLI 多轮 mirror 后，画面段与音乐段的起点
            # 会有几十毫秒的偏差（实测 5.767s vs 5.741s），卡太死就匹配不上了。
            if abs(start - int(intro_us)) <= 100_000:
                target_id = segment.get("id")
                break
    if not target_id:
        return None

    folder = Path(folder)
    ref = "local://" + folder.name
    workspace = Path(tempfile.gettempdir()) / ("guzhu-effect-%s" % uuid.uuid4().hex[:8])
    try:
        _project_script(project, "draftediting_runtime.py", ["init", "--workspace", workspace])
        _project_script(project, "draftediting_runtime.py",
                        ["sync", "--workspace", workspace, "--ref", ref,
                         "--draft-root", root])
        # --seg-id 与 --seg-type 互斥（后者用于 --target-track/--seg-index 的定位方式）
        lyra_cli.draft(["video", "effect", "add"], str(root), ref,
                       {"--seg-id": target_id, "--resource": "vimo://" + resource},
                       workspace=workspace)
        _mirror_draft(folder)
        verified, _ = read_draft_timeline(project, folder)
        effect_nodes = {node["id"]: node for node in
                        verified.get("materials", {}).get("video_effects", [])}
        verified_editor = Editor(verified)
        target = next((segment for _track, segment in verified_editor.segments()
                       if segment.get("id") == target_id), None)
        applied = [effect_nodes[ref_id] for ref_id in (target or {}).get("extra_material_refs", [])
                   if ref_id in effect_nodes and
                   str(effect_nodes[ref_id].get("resource_id")) == str(resource)]
        if not target or not applied:
            raise RuntimeError("官方返回成功但目标视频段未引用所选画面特效")
        return {"name": name, "resource": resource, "seg_id": target_id,
                "coverage_us": range_of(target), "引用已验证": True}
    except Exception as error:  # noqa: BLE001 - 特效失败不该毁掉整条流程
        log("  画面特效 %s 失败（%s）：%s" % (name, type(error).__name__,
                                             str(error).replace("\n", " ")[:300]))
        return None
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


# 转场（同样挖自本机草稿，均为本地有实体）
TRANSITIONS = {
    "dissolve": ("6724845717472416269", "叠化"),
    "fade_black": ("6724239388189921806", "闪黑"),
    "mist": ("7596980716043275526", "雾化交叠"),
    "push": ("7630762809986452790", "推镜虚化"),
}


def resource_is_local(resource_id):
    """该素材资源在本机缓存里有没有实体。

    不同类型的资源落在不同缓存子目录：转场在 ``Cache/effect/``，画面特效与歌词动效
    在 ``Cache/artistEffect/``。只查一个目录会误判成"缺资源"而白白跳过。
    """
    if not resource_id:
        return False
    base = Path(os.environ.get("LOCALAPPDATA", "")) / "JianyingPro" / "User Data" / "Cache"
    if not base.is_dir():
        return True  # 拿不到缓存根目录时不阻拦，交给官方去判断
    return any((folder / str(resource_id)).is_dir()
               for folder in base.iterdir() if folder.is_dir())


def apply_transition(project, root, folder, key="dissolve", duration_us=500000, on="intro"):
    """给主歌画面段加入场转场（官方 ``draft video transition add``）。

    片头说完话直接切进副歌本来很硬，一个叠化就顺了。转场挂在**进入该段的**
    那一条段上，所以加在主歌画面段。
    """
    engine = str(Path(project) / "engine")
    if engine not in sys.path:
        sys.path.insert(0, engine)
    import lyra_cli  # noqa: PLC0415
    from guzhu_anim import animation_cache_dir  # noqa: PLC0415

    resource, name = TRANSITIONS.get(str(key)) or TRANSITIONS["dissolve"]
    if not resource_is_local(resource):
        log("  转场 %s 本地缺资源，跳过" % name)
        return None

    timeline, _path = read_draft_timeline(project, folder)
    skeleton = inspect_template(timeline)
    if not skeleton.main_music:
        return None
    intro_us = range_of(skeleton.main_music[0][1])[0]
    target_id = None
    if skeleton.video_track is not None:
        segments = skeleton.video_track.get("segments") or []
        if on == "intro":
            # 挂在片头画面段上＝"从片头过渡进主歌"（剪映的转场挂在过渡的前一段）
            for segment in segments:
                start, _duration = range_of(segment)
                if start < 100_000:
                    target_id = segment.get("id")
                    break
        for segment in segments:
            if target_id:
                break
            start, _duration = range_of(segment)
            # 容差放宽到 100ms：经过官方 CLI 多轮 mirror 后，画面段与音乐段的起点
            # 会有几十毫秒的偏差（实测 5.767s vs 5.741s），卡太死就匹配不上了。
            if abs(start - int(intro_us)) <= 100_000:
                target_id = segment.get("id")
                break
    if not target_id:
        return None

    folder = Path(folder)
    ref = "local://" + folder.name
    workspace = Path(tempfile.gettempdir()) / ("guzhu-trans-%s" % uuid.uuid4().hex[:8])
    try:
        _project_script(project, "draftediting_runtime.py", ["init", "--workspace", workspace])
        _project_script(project, "draftediting_runtime.py",
                        ["sync", "--workspace", workspace, "--ref", ref,
                         "--draft-root", root])
        lyra_cli.draft(["video", "transition", "add"], str(root), ref,
                       {"--seg-id": target_id, "--resource": "vimo://" + resource,
                        # 官方要求显式单位（"500" 会被拒：expects an explicit unit）
                        "--duration": "%dms" % max(1, int(duration_us // 1000))},
                       workspace=workspace)
        _mirror_draft(folder)
        return {"name": name, "resource": resource, "seg_id": target_id}
    except Exception as error:  # noqa: BLE001 - 转场失败不该毁掉整条流程
        log("  转场 %s 失败（%s）：%s" % (name, type(error).__name__,
                                        str(error).replace("\n", " ")[:240]))
        return None
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


def font_is_usable(font):
    """该字体在本机是否真的可用（有实体文件，而不是只有 font.lock 空壳）。

    歌词动效会指定自己的字体，而那些字体**需要联网下载**；沙箱没有网络时
    缓存目录里往往只剩一个 ``font.lock``，渲染便回退成系统默认字体。
    """
    if not isinstance(font, dict):
        return False
    raw = str(font.get("path") or "")
    if not raw:
        return False
    # 包内占位路径（##_draftpath_placeholder_...）随包而来，视为可用
    if raw.startswith("##_draftpath_placeholder"):
        return bool(font.get("id"))
    path = Path(raw)
    if path.is_file():
        return True
    if path.is_dir():
        return any(p.suffix.lower() in (".ttf", ".otf", ".ttc")
                   for p in path.rglob("*") if p.is_file())
    return False


def unify_lyric_font(project, root, folder):
    """把歌词段的字体换成模板自带字体。

    动效自带的字体在无网沙箱里下不下来（只剩 ``font.lock``），渲染会回退成
    系统默认字体——就是"字很丑"的来源。模板的片头字幕用的是随包字体，把它
    复制到歌词段，动效照旧、字形恢复。
    """
    timeline, source = read_draft_timeline(project, folder)
    texts = timeline.get("materials", {}).get("texts") or []

    template_font = None
    for node in texts:
        if str(node.get("type")) != "subtitle":
            continue
        content = parse_text_content(node.get("content")) or {}
        for style in content.get("styles") or []:
            font = style.get("font") if isinstance(style, dict) else None
            if font_is_usable(font):
                template_font = copy.deepcopy(font)
                break
        if template_font:
            break
    if not template_font:
        return None

    replaced, skipped = 0, 0
    target_id = str(template_font.get("id"))
    for node in texts:
        if str(node.get("type")) == "subtitle":
            continue
        changed = False
        for key in ("content", "base_content"):
            content = parse_text_content(node.get(key))
            if not isinstance(content, dict):
                continue
            for style in content.get("styles") or []:
                if not isinstance(style, dict):
                    continue
                current = style.get("font")
                # 只要不是模板字体就换。动效自带字体通常是能用的，但字形未必好看；
                # 模板那套字体是模板作者配的，风格统一、也已经随包进了草稿。
                if isinstance(current, dict) and str(current.get("id")) == target_id:
                    skipped += 1
                    continue
                style["font"] = copy.deepcopy(template_font)
                changed = True
            if changed:
                node[key] = dump_text_content(content)
        if changed:
            replaced += 1
    if replaced:
        write_draft_timeline(project, folder, timeline, source)
        return {"font_id": str(template_font.get("id")), "replaced": replaced,
                "kept": skipped}
    return None


def apply_loudness_normalize(project, root, folder, target_loudness=-14.0):
    """把草稿里的音频段做响度归一（官方 ``draft algo loudness-normalize``）。

    平台一般按整轨响度判定音量，-14 LUFS 是短视频的常用目标。这条命令作用在
    草稿的音频段上、跟着渲染走，比在 ffmpeg 里拍脑袋调增益更可控；
    逐段调用，单段失败不影响其它段。
    """
    engine = str(Path(project) / "engine")
    if engine not in sys.path:
        sys.path.insert(0, engine)
    import lyra_cli  # noqa: PLC0415

    timeline, _path = read_draft_timeline(project, folder)
    editor = Editor(timeline)
    targets = []
    for _track, segment in editor.segments():
        material_id = segment.get("material_id")
        if not material_id:
            continue
        if editor.bucket(material_id) in ("audios", "videos"):
            targets.append(segment.get("id"))
    if not targets:
        return None

    folder = Path(folder)
    ref = "local://" + folder.name
    workspace = Path(tempfile.gettempdir()) / ("guzhu-loud-%s" % uuid.uuid4().hex[:8])
    done = 0
    try:
        _project_script(project, "draftediting_runtime.py", ["init", "--workspace", workspace])
        _project_script(project, "draftediting_runtime.py",
                        ["sync", "--workspace", workspace, "--ref", ref,
                         "--draft-root", root])
        for segment_id in targets:
            try:
                lyra_cli.draft(["algo", "loudness-normalize"], str(root), ref,
                               {"--seg-id": segment_id, "--enable": "true",
                                "--target-loudness": str(target_loudness)},
                               workspace=workspace)
                done += 1
            except Exception as error:  # noqa: BLE001 - 单段失败不阻断
                log("  响度归一 %s 失败：%s" % (str(segment_id)[:8],
                                              str(error).replace("\n", " ")[:140]))
        if done:
            _mirror_draft(folder)
        return {"segments": done, "target_loudness": target_loudness} if done else None
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


def lint_draft_before_export(project, root, folder, evidence_path=None):
    """导出前用官方 ``lint draft`` 做一次契约验收。

    注意官方 lint 用**进程退出码**表达"发现问题"（``automation_exit_code: 1``）
    而不是 ``err_code``，所以封装层会把它当异常抛出；诊断详情写在
    ``draft_json_file`` 指向的文件里，这里把它挖出来。只记录、不阻断渲染——
    它的价值是渲染出问题时能提供一份官方诊断。
    """
    engine = str(Path(project) / "engine")
    if engine not in sys.path:
        sys.path.insert(0, engine)
    import lyra_cli  # noqa: PLC0415

    folder = Path(folder)
    ref = "local://" + folder.name
    workspace = Path(tempfile.gettempdir()) / ("guzhu-lint-%s" % uuid.uuid4().hex[:8])
    try:
        _project_script(project, "draftediting_runtime.py", ["init", "--workspace", workspace])
        _project_script(project, "draftediting_runtime.py",
                        ["sync", "--workspace", workspace, "--ref", ref,
                         "--draft-root", root])
        # 让官方把诊断写到可写目录里——它随命令返回的那份会被封装层截断（800 字符），
        # 路径都取不全。
        report_path = Path(workspace) / "lint-report.json"
        summary = {"report": str(report_path)}
        try:
            lyra_cli.lint_draft(str(root), ref, output=str(report_path),
                                workspace=workspace, timeout=900)
            summary["passed"] = True
        except Exception as error:  # noqa: BLE001
            # 官方 lint 用**进程退出码**表达"发现问题"，这不是命令失败
            summary["passed"] = False
            summary["exit"] = str(error).replace("\n", " ")[:160]
        if report_path.is_file():
            if evidence_path:
                saved = Path(evidence_path)
                saved.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(report_path, saved)
                summary["report"] = str(saved)
            try:
                data = json.loads(report_path.read_text(encoding="utf-8", errors="replace"))
            except (OSError, ValueError):
                data = None
            if isinstance(data, dict):
                summary["keys"] = sorted(data)[:12]
                for key in ("issues", "errors", "warnings", "summary", "result", "documents"):
                    if key in data:
                        value = data[key]
                        summary[key] = value[:6] if isinstance(value, list) else value
        return summary
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


def apply_intro_gain(project, root, folder, db=3.0):
    """给片头 TTS 口播段加增益（官方 ``draft audio volume``）。

    口播与背景音乐是**两条独立通道**，必须分开调：

    1. 垫乐压到 -8dB，是为了不盖住人声；
    2. 口播自己还要再抬 +3dB，才够亮、听得清。

    过去只做了第 1 步，口播一直是原始音量——这就是"口播听着没劲"的原因。
    两条通道分别用官方音量命令设置，互不干扰。
    """
    engine = str(Path(project) / "engine")
    if engine not in sys.path:
        sys.path.insert(0, engine)
    import lyra_cli  # noqa: PLC0415

    timeline, _path = read_draft_timeline(project, folder)
    skeleton = inspect_template(timeline)
    segments = [group.tts_segment for group in skeleton.groups if group.tts_segment]
    if not segments:
        return None

    folder = Path(folder)
    ref = "local://" + folder.name
    workspace = Path(tempfile.gettempdir()) / ("guzhu-intro-%s" % uuid.uuid4().hex[:8])
    done = 0
    try:
        _project_script(project, "draftediting_runtime.py", ["init", "--workspace", workspace])
        _project_script(project, "draftediting_runtime.py",
                        ["sync", "--workspace", workspace, "--ref", ref,
                         "--draft-root", root])
        for segment in segments:
            try:
                lyra_cli.draft(["audio", "volume"], str(root), ref,
                               {"--seg-id": segment.get("id"), "--db": str(db)},
                               workspace=workspace)
                done += 1
            except Exception as error:  # noqa: BLE001 - 单段失败不阻断
                log("  口播增益 %s 失败：%s" % (str(segment.get("id"))[:8],
                                              str(error).replace("\n", " ")[:120]))
        if done:
            _mirror_draft(folder)
        return {"segments": done, "db": db} if done else None
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


def apply_picture_adjust(project, root, folder, settings):
    """给草稿加全局画面调色（官方 ``draft adjust add``）。

    生成的背景图往往偏"平"，官方这条命令能整片调亮度/对比/饱和/色温/锐化，
    比自己在 ffmpeg 里烘参数更好——它作用在草稿层，跟着渲染走，
    而且不需要任何特效资源 id。
    """
    engine = str(Path(project) / "engine")
    if engine not in sys.path:
        sys.path.insert(0, engine)
    import lyra_cli  # noqa: PLC0415

    options = {}
    mapping = {"brightness": "--brightness", "contrast": "--contrast",
               "saturation": "--saturation", "color_temperature": "--color-temperature",
               "highlight": "--highlight", "shadow": "--shadow",
               "sharpening": "--sharpening"}
    for key, flag in mapping.items():
        if settings.get(key) is not None:
            options[flag] = str(settings[key])
    if not options:
        return None

    folder = Path(folder)
    ref = "local://" + folder.name
    workspace = Path(tempfile.gettempdir()) / ("guzhu-adjust-%s" % uuid.uuid4().hex[:8])
    try:
        _project_script(project, "draftediting_runtime.py", ["init", "--workspace", workspace])
        _project_script(project, "draftediting_runtime.py",
                        ["sync", "--workspace", workspace, "--ref", ref,
                         "--draft-root", root])
        lyra_cli.draft(["adjust", "add"], str(root), ref, options, workspace=workspace)
        _mirror_draft(folder)
        return {"options": options}
    except Exception as error:  # noqa: BLE001 - 调色失败不该毁掉整条流程
        log("  画面调色失败（%s），按原样渲染" % type(error).__name__)
        return None
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


def read_draft_timeline(project, folder):
    """解密草稿目录里最新的时间线（官方 CLI 只写 Timelines/<id>/）。"""
    engine = str(Path(project) / "engine")
    if engine not in sys.path:
        sys.path.insert(0, engine)
    import windows_runtime  # noqa: PLC0415
    timelines = sorted((Path(folder) / "Timelines").glob("*/draft_content.json"))
    if not timelines:
        fail("草稿目录里没有时间线文件")
    source = max(timelines, key=lambda path: path.stat().st_mtime_ns)
    return windows_runtime._decrypt_metadata_in_memory(source), source


def write_draft_timeline(project, folder, timeline, source):
    """把改过的时间线加密写回，并同步四个镜像。"""
    engine = str(Path(project) / "engine")
    if engine not in sys.path:
        sys.path.insert(0, engine)
    import windows_runtime  # noqa: PLC0415
    payload = json.dumps(timeline, ensure_ascii=False,
                         separators=(",", ":")).encode("utf-8")
    source = Path(source)
    if source.exists():
        source.unlink()
    windows_runtime._encrypt_metadata_from_memory(payload, source)
    _mirror_draft(folder)


def chorus_start_from_recognition(recognized, chorus_at, lines):
    """用官方识别的句子时间，找出歌词里"副歌第一行"真正在歌曲的哪一秒。

    纯文本歌词没有时间戳，但它有顺序；官方识别的文本虽然有个别同音错字，
    句子切分和时间却是准的。两者按顺序对齐后，副歌第一行落在哪一段，
    那一段的开始时间就是裁剪点。
    """
    if not recognized or not lines:
        return None
    plans, _cost = _align_lyrics([item.get("text") or "" for item in recognized], lines)
    for index, (low, high) in enumerate(plans):
        if low <= int(chorus_at) < high:
            return int(recognized[index]["start_us"])
    if len(recognized) >= 2:
        # 没落到任何一段（例如副歌正好在两段之间）：按首尾时间线性插值
        first = int(recognized[0]["start_us"])
        last = int(recognized[-1]["start_us"])
        return int(first + (last - first) * int(chorus_at) / max(1, len(lines)))
    return None


def overwrite_lyric_text(project, root, folder, cues, known_ids=(), ordered=None):
    """用提供的歌词文本覆盖官方识别结果，**保留官方时间轴**。

    官方 `lyrics recognize` 给出的是句子切分与时间（准），文本常有个别同音字出入；
    这里保留官方时间轴，只替换文本。必须在 `lyrics animation update` **之前**做——
    套动效会把整段重建并展开成逐词多段，之后就改不动了。

    两种对齐方式：
    - `cues`（LRC/SRT，带时间）：按时间重叠匹配，同一段内多行用换行连接；
    - `ordered`（纯文本，无时间）：**按顺序**对齐，按比例把行分给各段。
    """
    engine = str(Path(project) / "engine")
    if engine not in sys.path:
        sys.path.insert(0, engine)
    import windows_runtime  # noqa: PLC0415 - 复用核心项目的草稿加解密

    timelines = sorted((Path(folder) / "Timelines").glob("*/draft_content.json"))
    if not timelines:
        fail("草稿目录里没有时间线文件")
    source = max(timelines, key=lambda path: path.stat().st_mtime_ns)
    timeline = windows_runtime._decrypt_metadata_in_memory(source)
    editor = Editor(timeline)

    known = set(known_ids)
    rows = []
    for track, segment in editor.segments():
        material_id = segment.get("material_id")
        if not material_id or material_id in known:
            continue
        if editor.bucket(material_id) != "texts":
            continue
        rows.append((track, range_of(segment), segment, editor.node(material_id) or {}))
    if not rows:
        fail("草稿里找不到官方识别生成的歌词文本段，无法覆盖文本")
    rows.sort(key=lambda item: item[1][0])

    def apply_text(node, text, duration, fresh_words=False):
        """替换文本。

        默认**保留官方识别的字级节奏骨架**（words 里的词块边界就是演唱节奏）；
        只有拆出来的新段（时间轴变了）才按新时长重算。
        """
        skeleton = None if fresh_words else node.get("words")
        retitle(node, text)
        if fresh_words:
            node["words"] = even_words(text, {"end_time": [max(1, int(duration // 1000))]})
        else:
            node["words"] = remap_words(text, skeleton, max(1, int(duration // 1000)))

    def split_row(track, segment, node, start, duration, group):
        """把"一段含多行"拆成一行一段。

        官方识别的分句比歌词行粗（常把两小句并成一段）。整段塞两行会让逐词动效
        按整段字数均分时间、跟实际演唱错位，模板卡也排不下两行。这里按行拆开，
        各段时间按该行字数占比切分（近似演唱时长）。
        """
        weights = [max(1, len(item)) for item in group]
        total_weight = sum(weights)
        cursor = start
        created = 0
        for index, (text, weight) in enumerate(zip(group, weights)):
            if index == len(group) - 1:
                span = max(1, start + duration - cursor)
            else:
                span = max(1, int(round(duration * weight / total_weight)))
            if index == 0:
                target_segment, target_node = segment, node
            else:
                clone = copy.deepcopy(segment)
                clone["id"] = new_id()
                clone["material_id"] = editor.clone_material(node["id"])
                clone["extra_material_refs"] = editor.clone_refs(
                    segment.get("extra_material_refs"))
                set_range(clone, "target_timerange", cursor, span)
                if isinstance(clone.get("source_timerange"), dict):
                    set_range(clone, "source_timerange", 0, span)
                editor.add_segment(track, clone)
                target_segment = clone
                target_node = editor.node(clone["material_id"])
                created += 1
            set_range(target_segment, "target_timerange", cursor, span)
            if isinstance(target_segment.get("source_timerange"), dict):
                set_range(target_segment, "source_timerange", 0, span)
            apply_text(target_node, text, span)
            cursor += span
        return created

    replaced = 0
    split_created = 0
    samples = []
    if ordered:
        # 纯文本歌词没有时间戳：用官方识别段的文本，把歌词行按顺序单调对齐上去，
        # 段的时间边界仍用官方的。多行的段会被拆成一行一段。
        lines = list(ordered.get("lines") or [])
        seg_texts = [_recognized_text(node) for _, _, _, node in rows]
        plans, mean_cost = _align_lyrics(seg_texts, lines)
        scores = []
        for (low, high), (track, (start, duration), segment, node) in zip(plans, rows):
            group = lines[low:high]
            if not group:
                continue
            scores.append(_similarity(_recognized_text(node), "".join(group)))
            if len(group) == 1:
                apply_text(node, group[0], duration)
            else:
                split_created += split_row(track, segment, node, start, duration, group)
            replaced += 1
            if len(samples) < 2:
                # 留证：覆盖后的字级时间应当保留演唱节奏（间隔不均），不是机械均分
                samples.append({
                    "text": str("".join(group))[:18],
                    "gaps_ms": [int(b) - int(a) for a, b in
                                zip((node.get("words") or {}).get("start_time") or [],
                                    ((node.get("words") or {}).get("start_time") or [])[1:])][:8],
                })
        report = {"segments": len(rows), "replaced": replaced, "lines": len(lines),
                  "align": "ordered", "spans": [[low, high] for low, high in plans],
                  "split_created": split_created, "word_samples": samples,
                  "mean_similarity": round(sum(scores) / len(scores), 3) if scores else 0.0,
                  "mean_cost": round(mean_cost, 3)}
    else:
        spans = sorted((int(cue["start_us"]),
                        int(cue["start_us"]) + int(cue["duration_us"]),
                        str(cue["text"])) for cue in cues)
        for _, (start, duration), segment, node in rows:
            end = start + duration
            matched = [text for cue_start, cue_end, text in spans
                       if min(end, cue_end) > max(start, cue_start)]
            if not matched:
                continue
            apply_text(node, "\n".join(matched), duration)
            replaced += 1
        report = {"segments": len(rows), "replaced": replaced,
                  "cues": len(spans), "align": "timed"}

    payload = json.dumps(timeline, ensure_ascii=False,
                         separators=(",", ":")).encode("utf-8")
    if source.exists():
        source.unlink()
    windows_runtime._encrypt_metadata_from_memory(payload, source)
    _mirror_draft(folder)
    return report


def correct_official_lyrics(project, root, folder, text, known_ids=()):
    """**保留官方重建的段结构**，只逐段纠正错别字。

    官方套用歌词模板后重建出的段，与它自己的时间段是天然对齐的（分句比歌词细）。
    实测三条错误路线：
      1. 先写歌词再套模板 → 文本被重建覆盖，出重复字（"我我不再"）；
      2. 套完按整句往段里填 → 只有部分段被覆盖，其余碎片与原句重叠；
      3. 套完按时间占比重新分配字符 → 字数对但全部错位。
    正解是**不改写、只纠错**：把官方各段文本按顺序拼成一条字符流，与用户歌词做
    差分，把差分映射回各段，只替换真正错误的字，**不改变任何段的字数分配**。
    """
    import difflib  # noqa: PLC0415
    import re  # noqa: PLC0415

    engine = str(Path(project) / "engine")
    if engine not in sys.path:
        sys.path.insert(0, engine)
    import windows_runtime  # noqa: PLC0415

    timelines = sorted((Path(folder) / "Timelines").glob("*/draft_content.json"))
    if not timelines:
        fail("草稿目录里没有时间线文件")
    source = max(timelines, key=lambda path: path.stat().st_mtime_ns)
    timeline = windows_runtime._decrypt_metadata_in_memory(source)
    editor = Editor(timeline)

    known = set(known_ids)
    rows = []
    for _track, segment in editor.segments():
        material_id = segment.get("material_id")
        if not material_id or material_id in known:
            continue
        if editor.bucket(material_id) != "texts":
            continue
        rows.append((range_of(segment), segment, editor.node(material_id) or {}))
    if not rows:
        fail("草稿里找不到套模板后重建的歌词文本段")
    rows.sort(key=lambda item: item[0][0])

    def squeeze(value):
        return re.sub(r"\s+", "", str(value or ""))

    spans = []
    cursor = 0
    for index, ((_start, _duration), _segment, node) in enumerate(rows):
        official = squeeze(_recognized_text(node))
        spans.append((cursor, cursor + len(official), index, official))
        cursor += len(official)
    official_all = "".join(item[3] for item in spans)
    target = squeeze(text)
    if not official_all or not target:
        fail("官方歌词或目标歌词为空，无法纠错")

    # 逐字符建立"官方位置 -> 正确字符"的映射
    mapping = {}
    matcher = difflib.SequenceMatcher(None, official_all, target, autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for offset in range(i2 - i1):
                mapping[i1 + offset] = target[j1 + offset]
        elif tag == "replace":
            # 1:1 对齐，绝不把一个字映射给多个位置（历史 bug：按宽度均分导致"审判判判判"）
            width = i2 - i1
            piece = target[j1:j2]
            for offset in range(width):
                mapping[i1 + offset] = piece[offset] if offset < len(piece) else ""
        elif tag == "delete":
            # 官方多出来的字（碎片）：留空，避免与相邻段重复显示
            for pos in range(i1, i2):
                mapping[pos] = ""

    changed = 0
    for start_at, end_at, _index, official in spans:
        new_text = "".join(mapping.get(pos, official_all[pos])
                           for pos in range(start_at, end_at))
        _start, duration = rows[_index][0]
        node = rows[_index][2]
        if new_text == official:
            continue
        if not new_text:
            # 整段是多余碎片：清空内容但不删段，避免动效算法崩
            retitle(node, " ")
            changed += 1
            continue
        retitle(node, new_text)
        changed += 1

    payload = json.dumps(timeline, ensure_ascii=False,
                         separators=(",", ":")).encode("utf-8")
    if source.exists():
        source.unlink()
    windows_runtime._encrypt_metadata_from_memory(payload, source)
    _mirror_draft(folder)
    return {"align": "official-preserved-corrected", "segments": len(rows),
            "replaced": changed, "official_chars": len(official_all),
            "target_chars": len(target)}


def distribute_lyric_text(project, root, folder, text, known_ids=()):
    """套模板后，把整段歌词**按段时间占比逐字**填回碎片段。

    官方套用歌词模板时会把识别结果重建为**逐词碎片段**（实测同一条草稿从 6 段变 43 段）。
    这时再按"整句往段里填"是填不进去的：句数对不上段数，只有部分段被覆盖，
    剩下的碎片会与原句**同时显示、互相重叠**（实测出现三段叠在一起）。

    正确做法是字符级分配：读出重建后的全部歌词段，按各段时长占比把整段歌词
    逐字切开、依次填进各段。模板本来就是逐词动画，每段几个字正是它要的效果。
    """
    import re  # noqa: PLC0415

    engine = str(Path(project) / "engine")
    if engine not in sys.path:
        sys.path.insert(0, engine)
    import windows_runtime  # noqa: PLC0415

    timelines = sorted((Path(folder) / "Timelines").glob("*/draft_content.json"))
    if not timelines:
        fail("草稿目录里没有时间线文件")
    source = max(timelines, key=lambda path: path.stat().st_mtime_ns)
    timeline = windows_runtime._decrypt_metadata_in_memory(source)
    editor = Editor(timeline)

    known = set(known_ids)
    rows = []
    for _track, segment in editor.segments():
        material_id = segment.get("material_id")
        if not material_id or material_id in known:
            continue
        if editor.bucket(material_id) != "texts":
            continue
        rows.append((range_of(segment), segment, editor.node(material_id) or {}))
    if not rows:
        fail("草稿里找不到套模板后重建的歌词文本段")
    rows.sort(key=lambda item: item[0][0])

    chars = re.sub(r"\s+", "", str(text))
    if not chars:
        fail("传入的歌词文本为空")
    total = sum(max(1, duration) for (_s, duration), _seg, _node in rows)
    cursor = 0
    filled = 0
    for index, ((start, duration), _segment, node) in enumerate(rows):
        if index == len(rows) - 1:
            take = len(chars) - cursor
        else:
            take = int(round(len(chars) * max(1, duration) / total))
        take = max(1, take)
        piece = chars[cursor:cursor + take]
        cursor += take
        if not piece:
            continue
        retitle(node, piece)
        node["words"] = even_words(piece, {"end_time": [max(1, int(duration // 1000))]})
        filled += 1

    payload = json.dumps(timeline, ensure_ascii=False,
                         separators=(",", ":")).encode("utf-8")
    if source.exists():
        source.unlink()
    windows_runtime._encrypt_metadata_from_memory(payload, source)
    _mirror_draft(folder)
    return {"align": "char-distributed", "segments": len(rows), "filled": filled,
            "replaced": filled, "segments_total": len(rows),
            "chars": len(chars), "consumed": cursor}


def recognized_rows(project, folder, known_ids=()):
    """读出草稿里歌词文本段的时间与文本（诊断/对齐用）。

    覆盖文本之后这些内容会被改写、套动效后还会被拆成逐词段，所以只在
    识别刚结束、还没覆盖时调用才能拿到官方原文。
    """
    engine = str(Path(project) / "engine")
    if engine not in sys.path:
        sys.path.insert(0, engine)
    import windows_runtime  # noqa: PLC0415
    timelines = sorted((Path(folder) / "Timelines").glob("*/draft_content.json"))
    if not timelines:
        return []
    source = max(timelines, key=lambda path: path.stat().st_mtime_ns)
    editor = Editor(windows_runtime._decrypt_metadata_in_memory(source))
    known = set(known_ids)
    rows = []
    for _, segment in editor.segments():
        material_id = segment.get("material_id")
        if not material_id or material_id in known:
            continue
        if editor.bucket(material_id) != "texts":
            continue
        node = editor.node(material_id) or {}
        if str(node.get("type")) == "subtitle":
            continue
        start, duration = range_of(segment)
        rows.append({"start_us": start, "duration_us": duration,
                     "text": _recognized_text(node)})
    rows.sort(key=lambda item: item["start_us"])
    return rows


def install_lyrics_via_cli(project, root, folder, timeline, settings, cues=None,
                           ordered=None, chorus_at=None, lyric_lines=None):
    """歌词完全走剪映 CLI：官方识别 + 官方歌词动效。

    链路（实测本机 11.5.0.14471 全程通过、成片带官方歌词动效出字）：
      1. `blueprint sync` 拿主歌音乐段的 seg-id；
      2. `lyrics recognize --mode segment` 只识别主歌段，官方把结果写成
         **不带 template 的 `<text>` 段**（这正是 `animation update` 接受的目标）；
      3. 同步镜像后重新 sync，取到歌词段的 seg-id；
      4. `lyrics animation update --resource vimo://<动效资源>` 套官方歌词动效；
      5. 同步镜像，交给原生渲染。

    注意 `--resource` 必须是 **lyric_animation** 类资源（如"浪漫氛围"
    7591420714515844395，其目录里是 LyricStyle.json）。若传 subtitle_template，
    官方会报 `failed to read LyricStyle.json`。
    """
    engine = str(Path(project) / "engine")
    if engine not in sys.path:
        sys.path.insert(0, engine)
    import lyra_cli  # noqa: PLC0415 - 官方封装只在官方歌词模式需要

    skeleton = inspect_template(timeline)
    if not skeleton.main_music:
        fail("模板里没有主歌音乐段，无法定位歌词识别范围")
    music_segment = skeleton.main_music[0][1].get("id")
    folder = Path(folder)
    ref = "local://" + folder.name
    temp = Path(tempfile.gettempdir())
    workspaces = []

    def blueprint(tag):
        workspace = temp / ("guzhu-lyric-%s-%s" % (tag, uuid.uuid4().hex[:8]))
        if workspace.exists():
            shutil.rmtree(workspace)
        workspaces.append(workspace)
        _project_script(project, "draftediting_runtime.py",
                        ["init", "--workspace", workspace])
        _project_script(project, "draftediting_runtime.py",
                        ["sync", "--workspace", workspace, "--ref", ref,
                         "--draft-root", root])
        return workspace

    try:
        workspace = blueprint("a")
        id_map = json.loads((workspace / "id_map.json").read_text(encoding="utf-8"))
        if music_segment not in {item["seg_id"] for item in id_map}:
            fail("官方工作区里找不到主歌音乐段，无法限定识别范围")

        language = str(settings.get("language") or "zh")
        before_ids = _text_material_ids(folder)
        lyra_cli.lyrics_recognize(str(root), ref, language=language, mode="segment",
                                  seg_id=music_segment,
                                  timeout=int(settings.get("recognize_timeout", 1800)))
        _mirror_draft(folder)
        # 覆盖文本之前先把官方识别的原文与时间留下来，便于逐句核对
        recognized = recognized_rows(project, folder, before_ids)

        # 这里**不再改草稿结构**：曾试过按识别出的副歌时间在草稿上裁剪，
        # 但官方动效算法遇到被删改过的歌词段会 IndexError 崩溃。
        # 现在裁剪点在 build 阶段就用本地 ASR 定好（见 locate_chorus_by_asr）。
        trim_report = None

        # **顺序很关键**：必须先套模板、最后再写文本。
        # 官方套用模板时会**重新识别一遍歌词**并重建文本段；如果先把用户歌词写进去，
        # 这一步会把刚写的文本覆盖掉（实测产生"我我不再""在在""你爱过都"这类重复与漏字）。
        # 历史实现正是"先写文本、后套模板"，才需要每次套用后再逐段校正一遍。
        text_report = None

        workspace2 = blueprint("b")
        xml = (workspace2 / "current_draft.xml").read_text(encoding="utf-8", errors="replace")
        lyric_xml = [match.group(1) for match in TEXT_SEGMENT_RE.finditer(xml)
                     if "<template" not in match.group(0)]
        if not lyric_xml:
            fail("官方识别没有产出可套动效的歌词文本段（<text>）")
        id_map2 = json.loads((workspace2 / "id_map.json").read_text(encoding="utf-8"))
        seg_by_xml = {item["xml_id"]: item["seg_id"] for item in id_map2}

        animation_setting = str(settings.get("animation") or "auto")
        if animation_setting.lower() in ("none", "off", "skip"):
            # 不套任何动效模板：**直接用官方识别生成的标准歌词字幕**。
            # 官方识别的样式是剪映自带配置，开箱即可正常渲染；既然不换模板，
            # 也就不存在"模板依赖字体缺失"的问题，不必再折腾字体。
            text_report = (overwrite_lyric_text(project, root, folder, cues, before_ids, ordered)
                           if (cues or ordered) else None)
            return {"engine": "official", "lyric_segments": len(lyric_xml),
                    "animation": None, "music_segment": music_segment,
                    "language": language, "text_override": text_report,
                    "recognized": recognized, "chorus_trim": trim_report}

        resource = str(settings.get("animation") or LYRIC_ANIMATION_DEFAULT)
        if not resource.startswith("vimo://"):
            resource = "vimo://" + resource
        lyra_cli.lyrics_animation_update(
            str(root), ref, seg_by_xml[lyric_xml[0]], resource,
            language=str(settings.get("animation_language") or "zh-CN"),
            timeout=int(settings.get("animation_timeout", 900)))
        _mirror_draft(folder)

        # **默认保留官方重建的文本，不做任何改写**。官方重建出的段与它自己的时间段
        # 天然对齐（只是分句比歌词细）。实测三条改写路线全部失败：
        #   1. 先写歌词再套模板 → 被重建覆盖，出重复字（"我我不再"）；
        #   2. 套完按整句往段里填 → 只有部分段被覆盖，其余碎片与原句重叠；
        #   3. 套完按字符分配 / 差分纠错 → 字数对但错位，且重建段里存在
        #      content 结构异常的段（读出来是 JSON 串），纠错不可靠。
        # 因此纠错改为**显式开关**（media.correct_official_lyrics），默认关闭。
        if settings.get("correct_official_lyrics") and (cues or ordered):
            lyric_text = "".join(str(cue.get("text") or "") for cue in (cues or []))
            if not lyric_text and ordered:
                lyric_text = "".join(str(line) for line in (ordered.get("lines") or []))
            text_report = correct_official_lyrics(project, root, folder, lyric_text)
        return {"engine": "official", "lyric_segments": len(lyric_xml),
                "animation": resource, "music_segment": music_segment,
                "language": language, "text_override": text_report,
                "recognized": recognized, "chorus_trim": trim_report}
    finally:
        for workspace in workspaces:
            shutil.rmtree(workspace, ignore_errors=True)


def image_size(path):
    """读图片宽高（用 ffprobe，避免额外依赖）。"""
    completed = subprocess.run(
        [shutil.which("ffprobe") or "ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    if completed.returncode != 0:
        fail("无法读取图片尺寸：" + str(path))
    parts = [item for item in completed.stdout.strip().splitlines()[0].split(",") if item]
    if len(parts) < 2:
        fail("图片尺寸输出无法解析：" + str(path))
    return int(parts[0]), int(parts[1])


def lyric_cues_for(batch, entry):
    """取这首歌的歌词：有时间信息的给 cues，纯文本给按顺序的行。"""
    song = next((item for item in batch["songs"]
                 if str(item.get("name")) == entry.get("name")), None)
    if not song or not song.get("lyrics"):
        return [], None
    path = resolve_path(song["lyrics"], batch["_base"])
    if not Path(path).is_file():
        fail("歌词文件不存在：" + str(path))
    layout = str(entry.get("audio_layout") or "")
    intro_us = int(entry["timeline"]["intro_after_us"])
    if Path(path).suffix.lower() in (".lrc", ".srt"):
        # full/chorus：主歌段是独立剪出的片段、从它的第 0 秒起播，
        # 所以草稿时间 = 片头 + (歌词时间 - 片段起点) => 对应草稿 0 的源时间是 起点-片头。
        anchor = int(entry["start_us"]) - intro_us if layout in ("full", "chorus") \
            else int(entry["start_us"])
        return build_cues(str(path), anchor, intro_us, entry["window_us"]), None
    lines, chorus_at = parse_lyric_lines(str(path))
    total = int(entry.get("source_duration_us") or 0)
    if total <= 0 or not lines:
        return [], None
    if layout == "full":
        # 整首歌都在主歌段里，整份歌词从第 1 行开始，不需要估算起点
        return [], {"lines": lines, "start_index": 0}
    if layout == "chorus" and chorus_at is not None:
        # 作者标了「副歌」：口播结束后正好从那一行唱起，起点就是它
        return [], {"lines": lines, "start_index": max(0, min(chorus_at, len(lines) - 1))}
    step = total / len(lines)
    if layout == "chorus":
        lead_us = int(entry["start_us"])
    else:
        lead_us = int(entry["start_us"]) + intro_us
    start_index = int(lead_us / step) if step > 0 else 0
    start_index = max(0, min(start_index, len(lines) - 1))
    return [], {"lines": lines, "start_index": start_index}


def ascii_draft_name(safe_name, index):
    """官方 CLI 沙箱遇到非 ASCII 路径会直接崩溃，草稿目录名必须是 ASCII。"""
    cleaned = re.sub(r"[^0-9A-Za-z]+", "", str(safe_name))[:24]
    return ("guzhu-%02d-%s" % (index, cleaned)) if cleaned else ("guzhu-%02d" % index)


def render_one(batch, project, entry, out_dir, cleanup=False, index=1, crypto=None):
    settings = batch.get("render") or {}
    render_dir = out_dir / "render" / entry["safe_name"]
    if render_dir.exists():
        shutil.rmtree(render_dir)
    render_dir.parent.mkdir(parents=True, exist_ok=True)

    root = draft_root(project)
    folder, unpacked = install_draft(entry["jypack"], root, ascii_draft_name(entry["safe_name"], index))
    log("  安装草稿：%s（%d 个文件）" % (folder.name, unpacked))

    # 增益只应用一次：旧裁切文件已烘焙增益，不能再叠加模板段音量。
    # 同时做口播到副歌的交接：垫乐在口播结束前淡出，副歌淡入，避免硬切造成的突兀感。
    import lyra_cli
    music_timeline, _ = read_draft_timeline(project, folder)
    music_skeleton = inspect_template(music_timeline)
    music_ref = "local://" + folder.name
    intro_fade_out_us = int(((batch.get("media") or {}).get("intro_fade_out_ms", 600)) * 1000)
    main_fade_in_us = int(entry.get("main_fade_in_us") or 500000)
    for kind, items in (("main", music_skeleton.main_music),
                        ("intro", music_skeleton.intro_music)):
        db = 0.0
        if entry.get("native_audio"):
            db = entry.get("main_gain_db", 3.0) if kind == "main" else entry.get("intro_gain_db", -8.0)
            if db is None:
                raise RuntimeError("原生音频静音需显式设置，不接受空增益")
        for _track, segment, _material_id in items:
            lyra_cli.draft(["audio", "volume"], str(root), music_ref,
                           {"--seg-id": segment["id"], "--db": str(db)})
            _mirror_draft(folder)
            if not entry.get("native_audio"):
                continue
            if kind == "intro":
                # 垫乐尾部淡出：口播说完时音乐不是"啪"地断掉
                lyra_cli.draft(["audio", "fade"], str(root), music_ref,
                               {"--seg-id": segment["id"],
                                "--out": "%dus" % intro_fade_out_us})
                _mirror_draft(folder)
            else:
                lyra_cli.draft(["audio", "fade"], str(root), music_ref,
                               {"--seg-id": segment["id"],
                                "--in": "%dus" % main_fade_in_us,
                                "--out": "%dus" % entry.get("main_fade_out_us", 1200000)})
                _mirror_draft(folder)
    entry["music_gain_processing"] = "原素材增益与段增益去重"
    entry["audio_handover"] = {"intro_fade_out_us": intro_fade_out_us,
                               "main_fade_in_us": main_fade_in_us}

    # 原始官方 TTS 文件不转码；在已编排的片段上只设置一次官方播放速度。
    tts_settings = ((batch.get("intro") or {}).get("tts") or {})
    if tts_settings.get("mode", "official") == "official":
        import lyra_cli
        raw_timeline, _ = read_draft_timeline(project, folder)
        raw_groups = inspect_template(raw_timeline).groups
        ref = "local://" + folder.name
        for group in raw_groups:
            if group.tts_segment:
                lyra_cli.draft(["audio", "speed"], str(root), ref,
                               {"--seg-id": group.tts_segment["id"],
                                "--speed": str(tts_settings.get("speed", 1.3))})
                _mirror_draft(folder)
        entry["tts_processing"] = "官方原始音频 + 官方段速率"

    lyrics_settings = dict(batch.get("lyrics") or {})
    if str(lyrics_settings.get("engine") or "official") == "official":
        if crypto is None:
            crypto = EngineCrypto(project)
        cues, ordered = lyric_cues_for(batch, entry)
        chorus_at = entry.get("chorus_at")
        lyric_lines = None
        if entry.get("lyrics_source"):
            lyric_lines, _ = parse_lyric_lines(entry["lyrics_source"])
        # animation=auto（默认）：按歌词气质 + 背景明暗，从剪映的歌词动效里挑一个
        animation = str(lyrics_settings.get("animation") or "auto")
        if animation in ("", "auto"):
            chosen, why = pick_animation("".join(lyric_lines or []),
                                         background=(batch.get("media") or {}).get("background"),
                                         project=project)
            lyrics_settings["animation"] = chosen
            entry["animation_pick"] = {"id": chosen, "why": why}
            log("  歌词动效自动匹配：%s（%s）" % (chosen, why))
        produced = install_lyrics_via_cli(project, root, folder,
                                          read_package(entry["jypack"], crypto).timeline,
                                          lyrics_settings, cues=cues, ordered=ordered,
                                          chorus_at=chorus_at, lyric_lines=lyric_lines)
        entry["lyrics_cli"] = produced
        override = produced.get("text_override")
        log("  官方歌词：识别 %d 段 + 动效 %s%s"
            % (produced["lyric_segments"], produced.get("animation") or "官方识别默认样式",
               ("，LRC 文本覆盖 %d/%d 段" % (override["replaced"], override["segments"]))
               if override else ""))
        trim = produced.get("chorus_trim")
        if trim and trim.get("delta_us"):
            log("  按识别出的副歌起剪：前移 %.3fs，丢弃 %d 段歌词"
                % (trim["delta_us"] / 1e6, trim.get("dropped_lyrics", 0)))

    # 转场（官方 draft video transition add）：片头切进副歌时叠化一下
    transition_setting = (batch.get("media") or {}).get("transition", "dissolve")
    if transition_setting and str(transition_setting) != "off":
        transition = apply_transition(project, root, folder, key=str(transition_setting),
                                      duration_us=int(((batch.get("media") or {})
                                                       .get("transition_ms", 500)) * 1000))
        if transition:
            entry["transition"] = transition
            log("  转场：%s（%s）" % (transition["name"], transition["resource"]))

    # 画面特效（官方 draft video effect add）：给主歌画面套胶片调色一类特效
    effect_setting = (batch.get("media") or {}).get("effect", "film")
    if effect_setting and str(effect_setting) != "off":
        effected = apply_video_effect(project, root, folder, key=str(effect_setting))
        if effected:
            entry["video_effect"] = effected
            log("  画面特效：%s（%s）" % (effected["name"], effected["resource"]))

    # 口播 +3dB（官方 draft audio volume）：口播和背景是**两条独立通道**。
    # 垫乐 -8dB 只保证不盖人声，口播自身还要抬 +3dB 才听得清——两件事不能合并成一次调音量。
    intro_gain = (batch.get("media") or {}).get("intro_volume_db")
    if intro_gain is None:
        tts_mode = str((((batch.get("intro") or {}).get("tts")) or {}).get("mode") or "official")
        intro_gain = 3.0 if tts_mode == "official" else None
    if intro_gain not in (None, False, "off"):
        boosted = apply_intro_gain(project, root, folder, db=float(intro_gain))
        if boosted:
            entry["intro_gain"] = boosted
            log("  口播增益：%d 段 +%.1fdB（背景音乐另有独立通道）"
                % (boosted["segments"], boosted["db"]))

    # 画面调色（官方 draft adjust add）：让生成的背景图不那么"平"
    color_settings = ((batch.get("media") or {}).get("color")
                      if isinstance((batch.get("media") or {}).get("color"), dict) else None)
    if color_settings:
        adjusted = apply_picture_adjust(project, root, folder, color_settings)
        if adjusted:
            entry["picture_adjust"] = adjusted
            log("  画面调色：%s" % json.dumps(adjusted["options"], ensure_ascii=False))

    # 注意：歌词的字体由**官方歌词模板**（lyrics animation 的 text_templates）决定，
    # 与片头 TTS 字幕是两套东西，不要互相套用——早前把歌词字体改成片头字幕字体
    # 是搞错了方向。字丑的真正原因是所选模板依赖的字体本机缺失，正确做法是在
    # pick_animation 阶段就排除依赖不全的模板（见 guzhu_anim.animation_dependencies_ready）。

    # 响度归一（官方 draft algo loudness-normalize）：按平台标准统一音量
    loudness = (batch.get("media") or {}).get("loudness_normalize")
    if loudness not in (None, False, "off"):
        target = -14.0 if loudness in (True, "auto") else float(loudness)
        normalized = apply_loudness_normalize(project, root, folder, target_loudness=target)
        if normalized:
            entry["loudness_normalize"] = normalized
            log("  响度归一：%d 段 -> %.1f LUFS" % (normalized["segments"],
                                                  normalized["target_loudness"]))

    # 导出前自检（官方 lint draft）：只记录，不阻断
    lint = lint_draft_before_export(project, root, folder,
                                    evidence_path=out_dir / (entry["safe_name"] + "-official-lint.json"))
    entry["lint"] = lint
    if lint and not lint.get("error"):
        log("  官方自检：%s" % json.dumps(lint, ensure_ascii=False)[:200])
    command = [sys.executable, str(project / "engine" / "jypack_render.py"),
               "--input", entry["jypack"], "--out", str(render_dir),
               "--draft-dir", str(folder),
               "--fps", str(settings.get("fps", 30)),
               "--bitrate", str(int(settings.get("bitrate", 6_000_000))),
               "--timeout", str(int(settings.get("timeout", 900)))]
    if settings.get("width"):
        command += ["--width", str(int(settings["width"]))]
    if settings.get("height"):
        command += ["--height", str(int(settings["height"]))]
    completed = subprocess.run(command, capture_output=True, cwd=str(project))
    stdout = completed.stdout.decode("utf-8", "replace")
    stderr = completed.stderr.decode("utf-8", "replace")
    (out_dir / "render" / (entry["safe_name"] + ".log")).write_text(
        stdout + "\n--- stderr ---\n" + stderr, encoding="utf-8")
    entry["draft_dir"] = str(folder)
    if completed.returncode != 0:
        entry["status"] = "render-failed"
        entry["error"] = (stderr.strip().splitlines() or ["未知错误"])[-1]
        if cleanup:
            shutil.rmtree(folder, ignore_errors=True)
        return entry
    result_path = render_dir / "result.json"
    if result_path.is_file():
        result = json.loads(result_path.read_text(encoding="utf-8"))
        entry["render"] = {"output": result.get("output"),
                           "duration": result.get("video_duration"),
                           "width": result.get("width"), "height": result.get("height"),
                           "sha256": result.get("output_sha256"),
                           "size": result.get("output_size"),
                           "imported_draft": result.get("imported_draft")}
    entry["status"] = "rendered"
    if cleanup:
        shutil.rmtree(folder, ignore_errors=True)
        entry["draft_dir"] = None
    return entry


# --------------------------------------------------------------------------- 主流程


def command_check(args):
    project = resolve_project(args.project)
    log("核心项目：" + str(project))
    log("Python：" + sys.executable)
    if shutil.which("ffmpeg") and shutil.which("ffprobe"):
        log("FFmpeg：已找到")
    else:
        log("FFmpeg：未找到（换歌与音频处理需要它）")
    try:
        crypto = EngineCrypto(project)
        log("剪映引擎：加载成功（草稿加解密可用）")
    except Exception as error:  # noqa: BLE001 - 体检要报告所有失败
        log("剪映引擎：不可用 —— " + str(error))
        return 1
    if args.template:
        package = read_package(resolve_path(args.template, Path.cwd()), crypto)
        skeleton = inspect_template(package.timeline)
        log("模板：" + str(package.source))
        log("  片头分界：%.3fs（%d 组引流话术）"
            % (skeleton.intro_end / 1e6, len(skeleton.groups)))
        log("  主歌段：%.3fs" % (skeleton.main_duration / 1e6))
        log("  总时长：%.3fs" % (package.timeline.get("duration", 0) / 1e6))
        log("  时间线 id：" + str(package.timeline.get("id")))
        for index, group in enumerate(skeleton.groups, 1):
            node = package.timeline and None
            log("    第 %d 句：%.3fs" % (index, group.duration / 1e6))
    voices = list_voices()
    chinese = [item["name"] for item in voices if item["culture"].lower().startswith("zh")]
    log("离线音色（中文）：" + ("、".join(chinese) if chinese else "无"))
    return 0


def command_voices(args):
    for item in list_voices():
        log("%-40s %s" % (item["name"], item["culture"]))
    return 0


def load_context(args):
    batch = load_batch(args.batch)
    project = resolve_project(args.project)
    out_dir = resolve_path(batch.get("out") or ("work/guzhu-" + time.strftime("%Y%m%d-%H%M%S")),
                           batch["_base"])
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    crypto = EngineCrypto(project)
    template = read_package(resolve_path(batch["template"], batch["_base"]), crypto)
    inspect_template(template.timeline)
    return batch, project, out_dir, crypto, template


def selected_songs(batch, only):
    songs = batch["songs"]
    if not only:
        return songs
    wanted = {item.strip() for item in only}
    return [song for song in songs if str(song.get("name")) in wanted]


def report_path(out_dir):
    return out_dir / "report.json"


def load_report(out_dir, batch):
    path = report_path(out_dir)
    if path.is_file():
        try:
            report = json.loads(path.read_text(encoding="utf-8"))
        except ValueError:
            report = None
        if isinstance(report, dict) and report.get("schema") == SCHEMA:
            return report
    return {"schema": SCHEMA, "template": str(batch["template"]), "songs": {}}


def save_report(out_dir, batch, report, tts=None):
    merged = []
    for song in batch["songs"]:
        name = str(song["name"])
        entry = report["songs"].get(name)
        if entry:
            merged.append(entry)
    report["songs"] = {str(item["name"]): item for item in merged}
    report["order"] = [str(song["name"]) for song in batch["songs"]]
    if tts:
        report["intro"] = {"lines": [line["text"] for line in tts["lines"]],
                           "mode": tts.get("mode"), "voice": tts.get("voice"),
                           "total_us": sum(int(line["duration_us"]) for line in tts["lines"])}
    report["totals"] = {
        "count": len(report["songs"]),
        "rendered": sum(1 for item in report["songs"].values() if item.get("status") == "rendered"),
        "built": sum(1 for item in report["songs"].values() if item.get("status") == "built"),
        "failed": sum(1 for item in report["songs"].values()
                      if str(item.get("status", "")).endswith("failed")),
    }
    report_path(out_dir).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                                    encoding="utf-8")
    return report


def command_build(args):
    batch, project, out_dir, crypto, template = load_context(args)
    log("输出目录：" + str(out_dir))
    tts = prepare_tts(batch, out_dir, project, template,
                      resolve_path(batch["template"], batch["_base"]))
    log("引流话术：%d 句，共 %.3fs（%s）"
        % (len(tts["lines"]), sum(line["duration_us"] for line in tts["lines"]) / 1e6,
           tts.get("voice") or tts.get("mode")))
    report = load_report(out_dir, batch)
    songs = selected_songs(batch, args.only)
    for index, song in enumerate(songs, 1):
        name = str(song["name"])
        log("[%d/%d] %s" % (index, len(songs), name))
        try:
            entry = build_one(batch, template, tts, song, out_dir, project, crypto)
        except (GuzhuError, OSError, subprocess.SubprocessError) as error:
            log("  失败：" + str(error))
            report["songs"][name] = {"name": name, "status": "build-failed",
                                     "error": str(error)}
        else:
            log("  起草稿：%.2f MB | 选段 %.3fs（%s）| 片头 %.3fs→%.3fs | 歌词 %d 句"
                % (entry["jypack_bytes"] / 1e6, entry["start_us"] / 1e6, entry["start_pick"],
                   entry["timeline"]["intro_before_us"] / 1e6,
                   entry["timeline"]["intro_after_us"] / 1e6, entry["lyric_cues"]))
            report["songs"][name] = entry
        save_report(out_dir, batch, report, tts)
    save_report(out_dir, batch, report, tts)
    log("报告：" + str(report_path(out_dir)))
    return 0 if report["totals"]["failed"] == 0 else 1


def command_export(args):
    batch, project, out_dir, crypto, template = load_context(args)
    tts = prepare_tts(batch, out_dir, project, template,
                      resolve_path(batch["template"], batch["_base"]))
    report = load_report(out_dir, batch)
    songs = selected_songs(batch, args.only)
    for index, song in enumerate(songs, 1):
        name = str(song["name"])
        entry = report["songs"].get(name)
        if not entry or entry.get("status") in ("build-failed",):
            log("[%d/%d] %s：尚未起草稿，跳过（先运行 build）" % (index, len(songs), name))
            continue
        if args.resume and entry.get("status") == "rendered":
            log("[%d/%d] %s：已导出，跳过" % (index, len(songs), name))
            continue
        log("[%d/%d] %s：开始导出" % (index, len(songs), name))
        started = time.monotonic()
        try:
            render_one(batch, project, entry, out_dir,
                       cleanup=getattr(args, "cleanup_drafts", False),
                       index=index, crypto=crypto)
        except (GuzhuError, OSError, subprocess.SubprocessError) as error:
            entry["status"] = "render-failed"
            entry["error"] = str(error)
            log("  失败：" + str(error))
        entry["render_seconds"] = round(time.monotonic() - started, 1)
        if entry.get("status") == "rendered":
            info = entry.get("render") or {}
            log("  完成：%s（%.2fs, %sx%s）"
                % (info.get("output"), info.get("duration") or 0,
                   info.get("width"), info.get("height")))
        else:
            log("  失败：" + str(entry.get("error")))
        save_report(out_dir, batch, report, tts)
    save_report(out_dir, batch, report, tts)
    log("报告：" + str(report_path(out_dir)))
    return 0 if report["totals"]["failed"] == 0 else 1


def command_run(args):
    code = command_build(args)
    export_args = argparse.Namespace(**vars(args))
    export_args.resume = True
    code2 = command_export(export_args)
    return code or code2


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--project", help="jianying-headless-windows 检出目录")
    sub = parser.add_subparsers(dest="command", required=True)

    check = sub.add_parser("check", help="环境与模板体检")
    check.add_argument("--template", help="股东号模板 .jypack")
    check.set_defaults(func=command_check)

    voices = sub.add_parser("voices", help="列出本机可用的离线音色")
    voices.set_defaults(func=command_voices)

    for name, func in (("build", command_build), ("export", command_export),
                       ("run", command_run)):
        item = sub.add_parser(name, help={"build": "按清单批量起草稿",
                                          "export": "把草稿批量导出成片",
                                          "run": "起草稿并导出"}[name])
        item.add_argument("--batch", required=True, help="批次清单 batch.json")
        item.add_argument("--only", nargs="*", help="只处理指定歌名")
        item.add_argument("--cleanup-drafts", action="store_true",
                          help="渲染完成后删除草稿根下的临时草稿目录")
        item.set_defaults(func=func)
        if name == "export":
            item.add_argument("--resume", action="store_true", help="跳过已导出的条目")
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except GuzhuError as error:
        print("错误：" + str(error), file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("已中断", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
