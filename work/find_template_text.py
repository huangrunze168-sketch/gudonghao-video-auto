"""在解密后的草稿里搜索模板示例歌词，定位模板文本的真实存储字段。"""
import json
from pathlib import Path
import sys

TARGETS = ("time machine", "fall asleep", "时光", "睡着", "梦中", "dreams")


def walk(node, prefix, hits):
    if isinstance(node, dict):
        for key, value in node.items():
            walk(value, f"{prefix}.{key}", hits)
    elif isinstance(node, list):
        for index, value in enumerate(node):
            walk(value, f"{prefix}[{index}]", hits)
    elif isinstance(node, str):
        for target in TARGETS:
            if target in node:
                hits.append((prefix, target, node[:160]))


for argument in sys.argv[1:]:
    path = Path(argument)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(path, "读取失败:", error)
        continue
    hits = []
    walk(data, "", hits)
    print("=" * 20, path.name, "命中", len(hits))
    seen = set()
    for prefix, target, sample in hits:
        key = (prefix, target)
        if key in seen:
            continue
        seen.add(key)
        print(f"  [{target}] {prefix} -> {sample}")
