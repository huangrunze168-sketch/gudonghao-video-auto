"""诊断：官方识别给出的句级/字级时间，与实际演唱是否吻合。"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(r"C:\Users\Administrator\Documents\剪映")
sys.path.insert(0, str(ROOT / "skills" / "guzhu-hao" / "scripts"))
sys.path.insert(0, str(ROOT / "engine"))

import guzhu_batch as gb  # noqa: E402
from guzhu_common import EngineCrypto  # noqa: E402
from guzhu_jypack import read_package  # noqa: E402
from guzhu_timeline import Editor, range_of  # noqa: E402

project = str(ROOT)
crypto = EngineCrypto(project)
out_dir = ROOT / "work" / "guzhu-probe"
jypack = next((out_dir / "jypack").glob("*.jypack"))
report = json.loads((out_dir / "report.json").read_text(encoding="utf-8"))
entry = report["songs"]["mv测试"]
intro_us = int(entry["timeline"]["intro_after_us"])

folder, _count = gb.install_draft(jypack, gb.draft_root(project), "guzhu-probe-words")
rows = gb.recognize_lyrics(project, gb.draft_root(project), folder,
                           read_package(jypack, crypto).timeline, {"engine": "official"})
print("识别到 %d 句（时间为草稿时间，减 %.3fs 即歌曲时间）" % (len(rows), intro_us / 1e6))
for row in rows:
    start = (row["start_us"] - intro_us) / 1e6
    end = (row["start_us"] + row["duration_us"] - intro_us) / 1e6
    print("  %6.2f-%6.2f  %s" % (start, end, row["text"]))

# 直接读草稿里的字级时间
timeline, _path = gb.read_draft_timeline(project, folder)
editor = Editor(timeline)
print("\n字级时间（前 2 段的 words 结构）:")
shown = 0
for _track, segment in editor.segments():
    material_id = segment.get("material_id")
    if not material_id or editor.bucket(material_id) != "texts":
        continue
    node = editor.node(material_id) or {}
    if str(node.get("type")) == "subtitle":
        continue
    words = node.get("words")
    print("  段 %s  words 类型=%s" % (str(node.get("content"))[:40], type(words).__name__))
    if words:
        print("    ", json.dumps(words, ensure_ascii=False)[:400])
    shown += 1
    if shown >= 2:
        break
