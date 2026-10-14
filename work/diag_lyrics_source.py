"""定位官方歌词模板卡的实际文字来源。

对比：草稿 texts[].content 已是我们的歌词，但渲染画面仍是模板内置示例文本。
本脚本 dump 模板材料字段，并在草稿目录里搜索示例文本字节，找出真正的数据源。
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "engine"))
import windows_runtime  # noqa: E402

DRAFT = Path(r"C:\Users\Administrator\AppData\Local\JianyingPro\User Data\Projects"
             r"\com.lveditor.draft\headless-full-20261009-200555")
SEGMENT = "D2C62A99-F9B5-4028-8451-C69437BAD2DF"  # t10
NEEDLE = "time machine"

timeline_path = next((DRAFT / "Timelines").glob("*/draft_content.json"))
timeline = windows_runtime._decrypt_metadata_in_memory(timeline_path)
segments = {s["id"]: s for t in timeline["tracks"] for s in t.get("segments", [])}
segment = segments[SEGMENT]
materials = {n["id"]: n for bucket in timeline["materials"].values() for n in bucket}
template = materials[segment["material_id"]]

print("== segment keys:", sorted(segment))
print("== template keys:", sorted(template))
for key in sorted(template):
    value = template[key]
    if isinstance(value, (dict, list)):
        text = json.dumps(value, ensure_ascii=False)
        print(f"  {key}: {text[:300]}")
    else:
        print(f"  {key}: {str(value)[:300]}")

print()
print("== 草稿目录内搜索示例文本 ==")
needle = NEEDLE.encode("utf-8")
for path in DRAFT.rglob("*"):
    if not path.is_file() or path.stat().st_size > 40 * 1024 * 1024:
        continue
    try:
        data = path.read_bytes()
    except OSError:
        continue
    if needle in data:
        print("  hit(utf8):", path.relative_to(DRAFT))
    if NEEDLE.encode("utf-16-le") in data:
        print("  hit(utf16):", path.relative_to(DRAFT))
