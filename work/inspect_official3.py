"""查看官方识别后的草稿结构，并按段应用歌词动效。"""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "engine"))
import draftediting_runtime as dr  # noqa: E402

DRAFT_ROOT = Path(r"C:\Users\Administrator\AppData\Local\JianyingPro\User Data\Projects\com.lveditor.draft")
NAME = "headless-official3"
WS = Path(os.environ["LOCALAPPDATA"]) / "Temp" / "jianying-draftediting" / "ws-official3"
ref = dr.local_ref(NAME)

dr.blueprint_sync(WS, ref, DRAFT_ROOT)

xml_path = WS / "current_draft.xml"
id_map = {item["xml_id"]: item["seg_id"]
          for item in json.loads((WS / "id_map.json").read_text(encoding="utf-8"))}
text = xml_path.read_text(encoding="utf-8", errors="replace")

print("=== canonical XML 里的段 ===")
current = None
for line in text.splitlines():
    stripped = line.strip()
    if stripped.startswith("<text ") or stripped.startswith("<subtitle "):
        current = stripped[:150]
        print("  ", current)
    elif stripped.startswith("<template ") and current:
        print("       ->", stripped[:80])
    elif "<content>" in stripped and current:
        print("       content:", stripped.strip()[:200])
        current = None

print()
print("=== id 映射（text/subtitle 段）===")
for xml_id, seg_id in sorted(id_map.items()):
    if xml_id.startswith(("t", "s", "a")):
        print(f"  {xml_id} -> {seg_id}")
