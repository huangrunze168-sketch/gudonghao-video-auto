# -*- coding: utf-8 -*-
"""引流话术配音：离线 SAPI 合成，或使用用户自备的音频文件。

剪映官方 TTS 需要由官方 Agent Runtime 启动的进程（JIANYING_AGENT_RUNTIME_TOKEN），
本 skill 无法满足，因此话术配音走本机离线能力，并保留"外面给音频"的入口。
"""
from __future__ import annotations

from pathlib import Path
import re
import subprocess
import tempfile

from guzhu_audio import normalize_voice, probe
from guzhu_common import GuzhuError

DEFAULT_VOICE = "Microsoft Huihui Desktop"
SAPI_SCRIPT = """param([string]$Voice, [int]$Rate, [string]$TextPath, [string]$OutPath)
Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
if ($Voice) { $synth.SelectVoice($Voice) }
$synth.Rate = $Rate
$synth.SetOutputToWaveFile($OutPath)
$text = Get-Content -LiteralPath $TextPath -Raw -Encoding UTF8
$synth.Speak($text)
$synth.Dispose()
"""


def list_voices():
    """列出本机可用的 SAPI 音色。"""
    script = ("Add-Type -AssemblyName System.Speech;"
              "(New-Object System.Speech.Synthesis.SpeechSynthesizer)"
              ".GetInstalledVoices() | ForEach-Object {"
              " $_.VoiceInfo.Name + '|' + $_.VoiceInfo.Culture }")
    completed = subprocess.run(["powershell", "-NoProfile", "-Command", script],
                               capture_output=True, text=True, encoding="utf-8",
                               errors="replace", timeout=60)
    if completed.returncode != 0:
        raise GuzhuError("无法枚举 SAPI 音色：" + completed.stderr.strip()[:200])
    voices = []
    for line in completed.stdout.splitlines():
        if "|" in line:
            name, culture = line.split("|", 1)
            voices.append({"name": name.strip(), "culture": culture.strip()})
    return voices


def _sapi_to_wav(text, wav_path, voice, rate):
    with tempfile.TemporaryDirectory(prefix="guzhu-tts-") as folder:
        folder = Path(folder)
        text_path = folder / "text.txt"
        script_path = folder / "speak.ps1"
        text_path.write_text(text, encoding="utf-8")
        script_path.write_text(SAPI_SCRIPT, encoding="utf-8-sig")
        completed = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script_path),
             "-Voice", voice or "", "-Rate", str(int(rate)),
             "-TextPath", str(text_path), "-OutPath", str(wav_path)],
            capture_output=True, timeout=300)
    if completed.returncode != 0 or not Path(wav_path).is_file():
        detail = completed.stderr.decode("utf-8", "replace").strip()[:300]
        raise GuzhuError("SAPI 合成失败（音色 " + str(voice) + "）：" + detail)
    if Path(wav_path).stat().st_size == 0:
        raise GuzhuError("SAPI 合成结果为空，请换一个音色")


def resolve_voice(voice, voices=None):
    """把用户写的音色名解析成真实存在的 SAPI 音色。"""
    voices = voices or list_voices()
    if not voices:
        raise GuzhuError("本机没有可用的 SAPI 音色")
    if not voice:
        chinese = [item for item in voices if item["culture"].lower().startswith("zh")]
        return (chinese or voices)[0]["name"]
    for item in voices:
        if item["name"].lower() == voice.lower():
            return item["name"]
    for item in voices:
        if voice.lower() in item["name"].lower():
            return item["name"]
    raise GuzhuError("找不到音色 " + voice + "；可用：" +
                     "、".join(item["name"] for item in voices))


def synthesize_lines(lines, out_dir, mode="sapi", voice=None, rate=0, files=None,
                     gap_ms=0, sample_rate=44100):
    """按话术顺序产出配音音频，返回带时长的清单。

    mode=sapi   用本机离线语音合成；
    mode=files  使用 files 指定的音频（按顺序一一对应），或按行号命名的文件。
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    if not lines:
        raise GuzhuError("话术不能为空")

    results = []
    if mode == "files":
        if not files:
            raise GuzhuError("mode=files 时必须提供音频文件列表")
        if len(files) < len(lines):
            raise GuzhuError("提供的配音文件少于话术条数（%d < %d）" % (len(files), len(lines)))
    elif mode != "sapi":
        raise GuzhuError("不支持的配音模式：" + str(mode))

    resolved_voice = resolve_voice(voice) if mode == "sapi" else None
    for index, text in enumerate(lines):
        target = out_dir / ("line-%02d.wav" % (index + 1))
        if target.exists():
            target.unlink()
        raw = out_dir / ("line-%02d.raw.wav" % (index + 1))
        if mode == "sapi":
            _sapi_to_wav(text, raw, resolved_voice, rate)
        else:
            raw = Path(files[index])
        duration_us = normalize_voice(raw, target, sample_rate=sample_rate)
        if mode == "sapi" and raw.exists():
            raw.unlink()
        if duration_us <= 0:
            raise GuzhuError("配音时长为零：" + text)
        results.append({"text": text, "path": str(target),
                        "duration_us": duration_us + int(gap_ms) * 1000})
    return {"mode": mode, "voice": resolved_voice, "rate": rate, "lines": results}


def load_line_file(path):
    """从文本文件读取话术，一行一句，忽略空行与 # 注释。"""
    path = Path(path)
    if not path.is_file():
        raise GuzhuError("话术文件不存在：" + str(path))
    lines = []
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        text = raw.strip()
        if not text or text.startswith("#"):
            continue
        lines.append(text)
    return lines


def sanitize(name):
    """把歌名转成安全的文件名。"""
    cleaned = re.sub(r"[\\/:*?\"<>|\s]+", "_", str(name)).strip("_")
    return cleaned or "untitled"
