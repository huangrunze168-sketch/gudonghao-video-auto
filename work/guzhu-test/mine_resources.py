"""挖遍本机剪映的全部素材缓存，提取每个资源的名称。

第 2 代挖法：不只看草稿里"被用过"的资源（那样只能得到零星几个），而是直接遍历
``Cache/`` 下每个子目录里的每个资源目录，读它自带的元数据 json，把里面的
name / title / label 字段抽出来。这样能一次性得到可用资源的全貌。

产出 ``references/resource-index.json``：
``{缓存目录: {资源id: {"name":..., "files":[...]}}}``
"""
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(r"C:\Users\Administrator\Documents\剪映")
REFERENCES = ROOT / "skills" / "guzhu-hao" / "references"
cache_root = Path(os.environ["LOCALAPPDATA"]) / "JianyingPro/User Data/Cache"

NAME_KEYS = ("name", "title", "label", "display_name", "effect_name", "resource_name")
# 只读小文件，避免把几 MB 的效果定义整个塞进内存
MAX_JSON_BYTES = 600_000

index = {}
stats = []
for cache_dir in sorted(p for p in cache_root.iterdir() if p.is_dir()):
    found = {}
    try:
        resources = [d for d in cache_dir.iterdir() if d.is_dir()]
    except OSError:
        continue
    for resource in resources:
        entry = {"name": None, "files": [], "markers": []}
        try:
            files = [f for f in resource.rglob("*") if f.is_file()]
        except OSError:
            continue
        for path in files:
            entry["files"].append(path.name)
            lower = path.name.lower()
            if any(marker in lower for marker in
                   ("lyricstyle", "infosticker", "effectstyle", "config", "effect.json",
                    "content.json", "tmp.json", "template.json", "meta")):
                entry["markers"].append(path.name)
            if entry["name"] or path.suffix.lower() != ".json":
                continue
            if path.stat().st_size > MAX_JSON_BYTES:
                continue
            try:
                data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
            except (OSError, ValueError):
                continue
            if isinstance(data, dict):
                for key in NAME_KEYS:
                    value = data.get(key)
                    if isinstance(value, str) and value.strip():
                        entry["name"] = value.strip()
                        entry["name_from"] = path.name
                        break
        found[resource.name] = entry
    if found:
        index[cache_dir.name] = found
        named = sum(1 for item in found.values() if item["name"])
        stats.append((cache_dir.name, len(found), named))

stats.sort(key=lambda row: -row[1])
print("缓存目录                 资源数  有名称")
for name, total, named in stats[:26]:
    print("  %-24s %5d  %5d" % (name, total, named))
print()
totals = (sum(row[1] for row in stats), sum(row[2] for row in stats))
print("合计 %d 个资源，其中 %d 个带名称" % totals)

out = REFERENCES / "resource-index.json"
out.write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")
print("已写出", out.name, "(%.1f MB)" % (out.stat().st_size / 1e6))

print("\n各目录里有名称的样例：")
for name, total, named in stats:
    if not named:
        continue
    samples = [item["name"] for item in index[name].values() if item["name"]][:6]
    print("  %-24s %s" % (name, "、".join(samples)))
