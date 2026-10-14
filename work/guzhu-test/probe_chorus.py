import sys

sys.path.insert(0, r"C:\Users\Administrator\Documents\剪映\skills\guzhu-hao\scripts")

from guzhu_audio import detect_chorus, probe  # noqa: E402
from guzhu_lyrics import parse_lyric_lines  # noqa: E402

song = r"C:\Users\Administrator\.dsh\attachments\v1\files\eb\eb41d90d8cf6bf7bb78602ed13db37e392180b27076694a627d06e186767d207\mv测试.mp3"
lyric = r"C:\Users\Administrator\.dsh\attachments\v1\files\4a\4a4e64a2fc482eaa81d556548711bc536b4c47c1365be5112ff29d05e14fdceb\mv歌词.txt"

lines, chorus_at = parse_lyric_lines(lyric)
total = probe(song)["duration_us"]
print("歌词行数 %d，副歌标记行号 %s，歌曲 %.3fs" % (len(lines), chorus_at, total / 1e6))
for index, item in enumerate(lines):
    print("   [%d] %s" % (index, item))

expected = int(total * chorus_at / len(lines))
span = max(int(expected * 0.05), 1_000_000)
print("预期位置 %.3fs，搜索区间 [%.3f, %.3f]"
      % (expected / 1e6, (expected - span) / 1e6, (expected + span) / 1e6))

for label, kwargs in [("全曲盲搜", {}),
                      ("标记约束", {"search_us": (expected - span, expected + span)})]:
    start, basis = detect_chorus(song, 31_062_000, min_lead_us=5_000_000, **kwargs)
    print("%s => 起点 %.3fs  依据 %s" % (label, start / 1e6, basis))
