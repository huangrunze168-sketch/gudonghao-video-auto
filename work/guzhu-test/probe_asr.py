"""用本地 ASR 定位副歌：识别整首歌的句子时间，与歌词顺序对齐。"""
import os
import subprocess
import sys
import time
from pathlib import Path

for name in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"):
    os.environ.pop(name, None)
os.environ["NO_PROXY"] = "*"

sys.path.insert(0, r"C:\Users\Administrator\Documents\剪映\skills\guzhu-hao\scripts")
from guzhu_lyrics import parse_lyric_lines  # noqa: E402

SONG = r"C:\Users\Administrator\.dsh\attachments\v1\files\eb\eb41d90d8cf6bf7bb78602ed13db37e392180b27076694a627d06e186767d207\mv测试.mp3"
LYRIC = r"C:\Users\Administrator\.dsh\attachments\v1\files\4a\4a4e64a2fc482eaa81d556548711bc536b4c47c1365be5112ff29d05e14fdceb\mv歌词.txt"
WAV = r"C:\Users\Administrator\Documents\剪映\work\guzhu-test\_asr.wav"

subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", SONG, "-ac", "1", "-ar", "16000",
                "-c:a", "pcm_s16le", WAV], check=True)

lines, chorus_at = parse_lyric_lines(LYRIC)
print("歌词 %d 行，副歌标记在第 %s 行（即 [%s]）" % (len(lines), chorus_at, lines[chorus_at]))

from faster_whisper import WhisperModel  # noqa: E402

for size in ("small",):
    print("\n=== 模型 %s ===" % size)
    started = time.time()
    model = WhisperModel(size, device="cpu", compute_type="int8")
    segments, info = model.transcribe(WAV, language="zh", beam_size=1)
    rows = [(seg.start, seg.end, seg.text.strip()) for seg in segments]
    print("识别 %.1fs 用时，得到 %d 句（语言 %s）" % (time.time() - started, len(rows), info.language))
    for start, end, text in rows:
        print("  %6.2f - %6.2f  %s" % (start, end, text))
