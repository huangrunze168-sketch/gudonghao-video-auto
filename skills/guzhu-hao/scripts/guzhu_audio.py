# -*- coding: utf-8 -*-
"""音频支撑：素材探测、副歌自动选段、按需裁成草稿可用音频。"""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import wave

from guzhu_common import GuzhuError

SUPPORTED_SUFFIXES = {".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg", ".wma", ".mp4"}
ANALYSIS_RATE = 8000
ANALYSIS_FRAME_SECONDS = 0.25


def _tool(name):
    path = shutil.which(name)
    if not path:
        raise GuzhuError("PATH 中找不到 " + name + "，请先安装 FFmpeg")
    return path


def probe(path):
    """用 ffprobe 读取时长与音频规格。"""
    path = Path(path)
    if not path.is_file():
        raise GuzhuError("音频文件不存在：" + str(path))
    completed = subprocess.run(
        [_tool("ffprobe"), "-v", "error", "-show_entries",
         "format=duration:stream=codec_name,sample_rate,channels", "-of", "json", str(path)],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    if completed.returncode != 0:
        raise GuzhuError("ffprobe 读取失败：" + completed.stderr.strip()[:200])
    info = json.loads(completed.stdout)
    stream = next((item for item in info.get("streams") or []
                   if item.get("codec_type", "audio") == "audio"), {})
    duration = (info.get("format") or {}).get("duration")
    if duration is None:
        raise GuzhuError("无法读取音频时长：" + str(path))
    return {"path": str(path), "duration_us": int(round(float(duration) * 1_000_000)),
            "codec": stream.get("codec_name"),
            "sample_rate": int(stream["sample_rate"]) if stream.get("sample_rate") else None,
            "channels": stream.get("channels")}


def _decode_mono(path, dest, rate=ANALYSIS_RATE):
    completed = subprocess.run(
        [_tool("ffmpeg"), "-v", "error", "-y", "-i", str(path),
         "-ac", "1", "-ar", str(rate), "-c:a", "pcm_s16le", str(dest)],
        capture_output=True, timeout=900)
    if completed.returncode != 0:
        raise GuzhuError("ffmpeg 解码失败：" +
                         completed.stderr.decode("utf-8", "replace").strip()[:200])


def _read_mono(path):
    import numpy as np

    with wave.open(str(path), "rb") as source:
        frames = source.readframes(source.getnframes())
        rate = source.getframerate()
        channels = source.getnchannels()
        width = source.getsampwidth()
    if width == 2:
        data = np.frombuffer(frames, dtype="<i2").astype(np.float32)
    elif width == 4:
        data = np.frombuffer(frames, dtype="<i4").astype(np.float32)
    elif width == 1:
        data = np.frombuffer(frames, dtype=np.uint8).astype(np.float32) - 128.0
    else:
        raise GuzhuError("不支持的 PCM 位宽：" + str(width))
    if channels > 1:
        data = data.reshape(-1, channels).mean(axis=1)
    return data, rate


def detect_chorus(path, window_us, min_lead_us=0, anchors_ms=None, intro_us=0,
                  min_anchors=3, search_us=None):
    """挑选最合适的窗口起点。

    默认用能量包络找最像副歌的一段；若提供了歌词时间（LRC），则优先选
    歌词行足够多、同时能量较高的窗口，避免自动落到没有歌词的间奏上。
    ``search_us=(low, high)`` 把搜索限制在一段区间内——纯文本歌词用一行
    「副歌」标注起点时，按行数比例估出大致位置，再在这里附近收敛到真正的
    段落切分点，比全曲盲搜准得多。

    返回 (起点微秒, 依据)。
    """
    import numpy as np

    info = probe(path)
    window_us = int(window_us)
    if window_us <= 0:
        raise GuzhuError("窗口长度必须为正")
    if info["duration_us"] < window_us:
        raise GuzhuError(
            "歌曲太短：%s 只有 %.2fs，少于需要的 %.2fs"
            % (Path(path).name, info["duration_us"] / 1e6, window_us / 1e6))

    with tempfile.TemporaryDirectory(prefix="guzhu-chorus-") as folder:
        mono = Path(folder) / "mono.wav"
        _decode_mono(path, mono)
        data, rate = _read_mono(mono)

    frame = max(1, int(rate * ANALYSIS_FRAME_SECONDS))
    usable = len(data) // frame * frame
    if usable < frame * 2:
        return 0, "window-too-short"
    blocks = data[:usable].reshape(-1, frame)
    energy = np.sqrt((blocks.astype(np.float64) ** 2).mean(axis=1))

    window_frames = max(1, int(round(window_us / 1e6 * rate / frame)))
    if window_frames >= len(energy):
        return 0, "window-covers-file"
    cumulative = np.concatenate([[0.0], np.cumsum(energy)])
    totals = cumulative[window_frames:] - cumulative[:-window_frames]
    best = int(np.argmax(totals))
    limited = ""
    if search_us:
        # 在标记给出的区间里找"响度跃升点"：副歌起点就是伴奏由弱转强的地方。
        # 不能沿用"固定窗口累计能量"——固定窗口在这里会越界（起点+窗口 > 歌曲总长），
        # 旧代码把起点回退到 总长-窗口，于是怎么搜都得到同一个偏早的结果。
        low, high = int(search_us[0]), int(search_us[1])
        index_low = max(0, min(int(round(low / 1e6 * rate / frame)), len(energy) - 1))
        index_high = max(index_low + 1,
                         min(int(round(high / 1e6 * rate / frame)) + 1, len(energy)))
        short = max(1, int(round(2.0 * rate / frame)))
        best, best_score = index_low, -1e18
        for index in range(index_low, index_high):
            after = energy[index:index + short]
            if not len(after):
                break
            before = energy[max(0, index - short):index]
            score = float(after.mean()) - (float(before.mean()) if len(before) else 0.0)
            if score > best_score:
                best, best_score = index, score
        limited = "-near"
    best_start = int(round(best * frame / rate * 1e6))

    def energy_at(start_us):
        index = int(round(start_us / 1e6 * rate / frame))
        index = max(0, min(index, len(energy) - window_frames))
        return float(energy[index:index + window_frames].mean())

    if anchors_ms:
        limit = info["duration_us"] - window_us
        candidates = set()
        for stamp in anchors_ms:
            start = int(stamp) * 1000 - int(intro_us)
            if 0 <= start <= limit:
                candidates.add(start)
        if candidates:
            scored = []
            for start in candidates:
                end = start + window_us
                inside = sum(1 for stamp in anchors_ms
                             if start + int(intro_us) <= int(stamp) * 1000 < end)
                scored.append((inside, energy_at(start), -start, start))
            scored.sort(reverse=True)
            best_count, _, _, picked = scored[0]
            if best_count >= int(min_anchors):
                return picked, "lyrics+energy(%d 句歌词)" % best_count

    if min_lead_us:
        best_start = max(best_start, int(min_lead_us))
    # search_us 用于"起点到歌曲结尾"的可变长度布局，这里不能按固定窗口回退
    if not search_us and best_start + window_us > info["duration_us"]:
        best_start = max(0, info["duration_us"] - window_us)
    return best_start, "energy" + limited


def cut_to_wav(source, dest, start_us, duration_us, sample_rate=44100, channels=2,
               gain_db=0.0, fade_in_us=0, fade_out_us=0):
    """把源音频的一段裁成草稿可直接使用的 wav。

    ``gain_db`` 直接把增益烘进音频（-8dB 压低口播时的背景音乐、+3dB 推高副歌），
    比去改草稿里的音量素材更稳——模板里那套音量引用本身是悬空的。
    ``fade_in_us``/``fade_out_us`` 让片头垫乐与副歌之间的衔接不再是硬切。
    """
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        raise GuzhuError("拒绝覆盖已存在的音频：" + str(dest))
    filters = []
    if abs(float(gain_db)) > 1e-6:
        filters.append("volume=%.3fdB" % float(gain_db))
    if int(fade_in_us) > 0:
        filters.append("afade=t=in:st=0:d=%.3f" % (int(fade_in_us) / 1e6))
    if int(fade_out_us) > 0:
        start = max(0.0, duration_us / 1e6 - int(fade_out_us) / 1e6)
        filters.append("afade=t=out:st=%.3f:d=%.3f" % (start, int(fade_out_us) / 1e6))
    args = ["-af", ",".join(filters)] if filters else []
    completed = subprocess.run(
        [_tool("ffmpeg"), "-v", "error", "-y",
         "-ss", "%.6f" % (start_us / 1e6), "-t", "%.6f" % (duration_us / 1e6),
         "-i", str(source)] + args +
        ["-ac", str(channels), "-ar", str(sample_rate),
         "-c:a", "pcm_s16le", str(dest)],
        capture_output=True, timeout=900)
    if completed.returncode != 0:
        raise GuzhuError("ffmpeg 裁剪失败：" +
                         completed.stderr.decode("utf-8", "replace").strip()[:200])
    return {"path": str(dest), "duration_us": probe(dest)["duration_us"]}


SILENCE_FILTER = ("silenceremove=start_periods=1:start_duration=0:start_threshold=-45dB,"
                  "areverse,"
                  "silenceremove=start_periods=1:start_duration=0:start_threshold=-45dB,"
                  "areverse")


def normalize_voice(source, dest, sample_rate=44100, channels=2, trim=True):
    """把任意语音文件统一成草稿可用的 wav，并默认去掉首尾静音。

    剪映模板里的配音素材都带前导/尾部静音（1.37s 的素材实际只用了 0.87s），
    不裁剪会让片头被静音拖长、节奏变慢。
    """
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        raise GuzhuError("拒绝覆盖已存在的音频：" + str(dest))
    base = [_tool("ffmpeg"), "-v", "error", "-y", "-i", str(source)]
    tail = ["-ac", str(channels), "-ar", str(sample_rate), "-c:a", "pcm_s16le", str(dest)]
    attempts = [base + ["-af", SILENCE_FILTER] + tail, base + tail] if trim else [base + tail]
    last = None
    for command in attempts:
        completed = subprocess.run(command, capture_output=True, timeout=300)
        if completed.returncode == 0 and dest.is_file() and dest.stat().st_size > 0:
            return probe(dest)["duration_us"]
        last = completed.stderr.decode("utf-8", "replace").strip()[:200]
        if dest.exists():
            dest.unlink()
    raise GuzhuError("ffmpeg 转码失败：" + str(last))
