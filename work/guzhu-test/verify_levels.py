import wave
import struct
import math
import glob
import subprocess
import os


def rms(path):
    with wave.open(path, "rb") as handle:
        data = handle.readframes(handle.getnframes())
    count = len(data) // 2
    if not count:
        return -999.0
    values = struct.unpack("<%dh" % count, data[:count * 2])
    energy = sum(item * item for item in values) / count
    return 20 * math.log10(max(1e-12, math.sqrt(energy) / 32768.0))


root = r"C:\Users\Administrator\Documents\剪映\work\guzhu-mv"
mp4 = os.path.join(root, r"render\mv测试\render.mp4")

subprocess.run(["ffmpeg", "-v", "error", "-y", "-t", "5.5", "-i", mp4, "-vn",
                "-ac", "2", "-ar", "44100", "-c:a", "pcm_s16le",
                os.path.join(root, "_h.wav")], check=True)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "12", "-t", "6", "-i", mp4, "-vn",
                "-ac", "2", "-ar", "44100", "-c:a", "pcm_s16le",
                os.path.join(root, "_m.wav")], check=True)

files = sorted(glob.glob(os.path.join(root, r"tts\official\*.mp3")))
listing = os.path.join(root, "_tts.txt")
with open(listing, "w", encoding="utf-8") as handle:
    for path in files:
        handle.write("file '%s'\n" % os.path.abspath(path).replace("\\", "/"))
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0",
                "-i", listing, "-ac", "2", "-ar", "44100", "-c:a", "pcm_s16le",
                os.path.join(root, "_tts.wav")], check=True)

voice = rms(os.path.join(root, "_tts.wav"))
head = rms(os.path.join(root, "_h.wav"))
main = rms(os.path.join(root, "_m.wav"))
print("纯 TTS（无音乐参照）  %6.1f dB" % voice)
print("成片 0-5.5s 口播段    %6.1f dB   => 比纯人声高 %+.1f dB" % (head, head - voice))
print("成片 12-18s 副歌段    %6.1f dB" % main)
print("片头垫乐素材          %6.1f dB" % rms(os.path.join(root, r"songs\mv测试-intro.wav")))
