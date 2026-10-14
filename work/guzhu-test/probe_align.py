"""诊断：官方识别整首歌，打印每段的绝对时间与文本。

用来确定「副歌第一句」在歌曲里的真实时间，避免再靠估算。
"""
import json
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\Administrator\Documents\剪映")
sys.path.insert(0, str(ROOT / "skills" / "guzhu-hao" / "scripts"))
sys.path.insert(0, str(ROOT / "engine"))

import guzhu_batch as gb  # noqa: E402
from guzhu_common import EngineCrypto  # noqa: E402
from guzhu_jypack import read_package  # noqa: E402
from guzhu_lyrics import parse_lyric_lines  # noqa: E402
from guzhu_timeline import Editor, range_of  # noqa: E402

project = str(ROOT)
crypto = EngineCrypto(project)
batch = gb.load_batch(str(ROOT / "work" / "guzhu-test" / "batch-probe.json"))
out_dir = Path(batch["out"])
jypack = next((out_dir / "jypack").glob("*.jypack"))
print("草稿包:", jypack.name)

package = read_package(jypack, crypto)
intro_us = 0
report = json.loads((out_dir / "report.json").read_text(encoding="utf-8"))
entry = report["songs"]["mv测试"]
intro_us = int(entry["timeline"]["intro_after_us"])
print("片头 %.3fs，主歌 %.3fs" % (intro_us / 1e6, entry["timeline"]["main_duration_us"] / 1e6))

# 装成草稿并交给官方识别
folder, _count = gb.install_draft(jypack, gb.draft_root(project), "guzhu-probe-full")
settings = {"engine": "official"}
result = gb.install_lyrics_via_cli(project, gb.draft_root(project), folder,
                                   package.timeline, settings)
print("识别段数:", result["lyric_segments"])

print("\n官方识别（草稿时间 -> 歌曲时间 -> 文本）:")
for row in result.get("recognized") or []:
    print("  ct %7.3fs / song %7.3fs  %s"
          % (row["start_us"] / 1e6, (row["start_us"] - intro_us) / 1e6, row["text"]))

lines, chorus_at = parse_lyric_lines(
    r"C:\Users\Administrator\.dsh\attachments\v1\files\4a\4a4e64a2fc482eaa81d556548711bc536b4c47c1365be5112ff29d05e14fdceb\mv歌词.txt")
print("\n用户歌词（副歌标记在第 %s 行）:" % chorus_at)
for index, item in enumerate(lines):
    print("  [%d]%s %s" % (index, "*副歌*" if index == chorus_at else "    ", item))
