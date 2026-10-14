"""一次扒清剪映 CLI 的能力面：全部命令清单 + 各类素材缓存盘点 + 可挖到的名称。

产物：
- ``references/cli-commands.md``  官方命令行能力清单（按域分组）
- ``references/effect-pool.json``  各类效果资源池（名称 -> id，本地有实体的）

思路：素材缓存里资源没有名字，名字在服务器上；但**凡是被用过的资源**都会把
name + resource_id 写进草稿。所以「扫全部草稿拿名字 + 扫全部缓存确认本地有实体」
就能得到一份当下可用的资源清单，不必一个类型一个类型去试。
"""
import json
import os
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(r"C:\Users\Administrator\Documents\剪映")
sys.path.insert(0, str(ROOT / "engine"))
import windows_runtime  # noqa: E402

REFERENCES = ROOT / "skills" / "guzhu-hao" / "references"

# ---------------------------------------------------------------- 1. 命令清单
commands = json.loads((ROOT / "engine" / "lyra_commands.json").read_text(encoding="utf-8"))
groups = {}
for item in commands.get("commands") or []:
    path = [str(part) for part in (item.get("path") or [])]
    if not path:
        continue
    group = path[0] if len(path) > 1 else "(顶层)"
    groups.setdefault(group, []).append({
        "name": ".".join(path),
        "summary": str(item.get("summary") or "").strip(),
        "options": [str(opt) for opt in (item.get("options") or [])],
    })

lines = ["# 剪映官方 CLI 能力清单", "",
         "由 `engine/lyra_commands.json` 生成（本机剪映 11.5.0.14471）。",
         "全部命令都经 `engine/draftediting_runtime.py` 在官方 VMSDK 沙箱内执行，",
         "直接调 `lyra-cli.exe` 会报 `unauthorized host process`。", ""]
for group in sorted(groups):
    items = sorted(groups[group], key=lambda row: row["name"])
    lines.append("## %s（%d 条）" % (group, len(items)))
    lines.append("")
    lines.append("| 命令 | 用途 | 关键参数 |")
    lines.append("| --- | --- | --- |")
    for row in items:
        options = [opt for opt in row["options"] if opt not in ("--help", "--version", "--jq")]
        shown = ", ".join(options[:8]) + (" …" if len(options) > 8 else "")
        lines.append("| `%s` | %s | %s |" % (row["name"], row["summary"] or "-", shown or "-"))
    lines.append("")
(REFERENCES / "cli-commands.md").write_text("\n".join(lines), encoding="utf-8")
total = sum(len(v) for v in groups.values())
print("命令清单：%d 条，分 %d 个域 -> cli-commands.md" % (total, len(groups)))

# ---------------------------------------------------------------- 2. 资源盘点
local = os.environ["LOCALAPPDATA"]
cache_root = Path(local) / "JianyingPro/User Data/Cache"
draft_root = Path(local) / "JianyingPro/User Data/Projects/com.lveditor.draft"

# 2a. 每个缓存子目录下有多少个资源目录
cache_counts = {}
if cache_root.is_dir():
    for folder in cache_root.iterdir():
        if not folder.is_dir():
            continue
        try:
            count = sum(1 for child in folder.iterdir() if child.is_dir())
        except OSError:
            continue
        if count:
            cache_counts[folder.name] = count
print("\n缓存子目录资源数（前 20）：")
for name, count in sorted(cache_counts.items(), key=lambda pair: -pair[1])[:20]:
    print("   %-28s %d" % (name, count))

# 2b. 扫草稿收集 (bucket -> {id: name})
ID_KEYS = ("resource_id", "effect_id", "transition_id", "animation_id", "filter_id",
           "sticker_id", "text_effect_id", "audio_effect_id", "material_id")
names = {}
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
                names.setdefault(bucket, {})[str(rid)] = str(name)

# 2c. 只保留本地有实体的
def is_local(resource_id):
    if not cache_root.is_dir():
        return True
    return any((folder / str(resource_id)).is_dir()
               for folder in cache_root.iterdir() if folder.is_dir())

pool = {}
print("\n资源池（带名称且本地有实体）：")
for bucket in sorted(names, key=lambda key: -len(names[key])):
    ready = {rid: name for rid, name in names[bucket].items() if is_local(rid)}
    pool[bucket] = ready
    print("   %-18s %d / %d" % (bucket, len(ready), len(names[bucket])))

pool["_cache_counts"] = cache_counts
(REFERENCES / "effect-pool.json").write_text(
    json.dumps(pool, ensure_ascii=False, indent=2), encoding="utf-8")
kinds = {key: len(value) for key, value in pool.items() if not key.startswith("_")}
print("\n可用资源池已写入 effect-pool.json：%s" % kinds)
