"""挖本机剪映可用的官方效果资源：带名称 + 本地有实体。

剪映的素材缓存里资源没有名字（名字在服务器上），但**凡是被用过的**都会把
name + resource_id 写进草稿。把所有草稿扫一遍即可攒出可用清单；
再逐个核对本地缓存是否有实体——缺实体的官方会去联网下载，沙箱没有网络。
"""
import json
import os
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\Administrator\Documents\剪映\engine")
import windows_runtime  # noqa: E402

local = os.environ["LOCALAPPDATA"]
draft_root = Path(local) / "JianyingPro/User Data/Projects/com.lveditor.draft"
cache_root = Path(local) / "JianyingPro/User Data/Cache"
cache_dirs = [d for d in cache_root.iterdir() if d.is_dir()] if cache_root.is_dir() else []

ID_KEYS = ("resource_id", "effect_id", "transition_id", "animation_id",
           "filter_id", "sticker_id", "text_effect_id", "material_id")

found = {}
scanned = 0
for folder in draft_root.iterdir() if draft_root.is_dir() else []:
    if not folder.is_dir():
        continue
    content = folder / "draft_content.json"
    if not content.is_file():
        continue
    try:
        timeline = windows_runtime._decrypt_metadata_in_memory(content)
    except Exception:  # noqa: BLE001
        continue
    scanned += 1
    for bucket, items in (timeline.get("materials") or {}).items():
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            name = item.get("name")
            rid = next((item.get(key) for key in ID_KEYS if item.get(key)), None)
            if name and rid and str(rid).isdigit():
                found.setdefault(bucket, {})[str(rid)] = str(name)

print("扫描草稿:", scanned)
print()
for bucket in sorted(found, key=lambda b: -len(found[b])):
    items = found[bucket]
    ready = {}
    for rid, name in items.items():
        if any((folder / rid).is_dir() for folder in cache_dirs):
            ready[rid] = name
    print("== %s：%d 个带名称，其中本地有实体 %d 个 ==" % (bucket, len(items), len(ready)))
    for rid, name in list(ready.items())[:14]:
        print("   %-20s %s" % (rid, name))
    missing = [n for r, n in items.items() if r not in ready]
    if missing:
        print("   （缺实体 %d 个，例：%s）" % (len(missing), "、".join(missing[:5])))
    print()

out = Path(r"C:\Users\Administrator\Documents\剪映\work\guzhu-test\effect-pool.json")
ready_all = {}
for bucket, items in found.items():
    ready_all[bucket] = {rid: name for rid, name in items.items()
                         if any((folder / rid).is_dir() for folder in cache_dirs)}
out.write_text(json.dumps(ready_all, ensure_ascii=False, indent=2), encoding="utf-8")
print("已写出", out.name)
