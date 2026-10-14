"""扫描本机剪映草稿，收集贴纸素材的（名称, 资源id）映射。

贴纸本体在剪映的素材缓存里没有名称（名称在服务器上），但**任何被使用过的
贴纸**都会把 name + resource_id 写进草稿。把所有草稿扫一遍，就能攒出一本
"名称 -> 资源 id"的词典，供按语义挑贴图使用。
"""
import json
import os
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(r"C:\Users\Administrator\Documents\剪映")
sys.path.insert(0, str(ROOT / "engine"))
import windows_runtime  # noqa: E402

draft_root = Path(os.environ["LOCALAPPDATA"]) / "JianyingPro/User Data/Projects/com.lveditor.draft"
found = {}
scanned = 0
for folder in draft_root.iterdir() if draft_root.is_dir() else []:
    if not folder.is_dir():
        continue
    for name in ("draft_content.json",):
        path = folder / name
        if not path.is_file():
            continue
        try:
            timeline = windows_runtime._decrypt_metadata_in_memory(path)
        except Exception:  # noqa: BLE001
            continue
        scanned += 1
        for item in (timeline.get("materials", {}).get("stickers") or []):
            sticker_name = item.get("name")
            rid = item.get("resource_id") or item.get("sticker_id")
            if sticker_name and rid:
                found[str(rid)] = sticker_name

print("扫描草稿数:", scanned)
print("收集到带名称的贴纸:", len(found))
for rid, sticker_name in list(found.items())[:60]:
    print("  %-20s %s" % (rid, sticker_name))

out = Path(r"C:\Users\Administrator\Documents\剪映\work\guzhu-test\sticker-names.json")
out.write_text(json.dumps(found, ensure_ascii=False, indent=2), encoding="utf-8")
print("已写出", out.name)
