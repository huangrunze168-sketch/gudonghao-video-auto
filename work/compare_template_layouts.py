"""对比 material_cache 里已缓存模板的目录结构，找出 lyric_animation 类模板需要哪些文件。"""
import json
from pathlib import Path

MC = Path(r"C:\Users\Administrator\AppData\Local\JianyingPro\User Data\Cache\lyra-cli\material_cache.json")
LYRA = Path(r"C:\Users\Administrator\AppData\Local\JianyingPro\User Data\Cache\lyra-cli\material-cache")
ARTIST = Path(r"C:\Users\Administrator\AppData\Local\JianyingPro\User Data\Cache\artistEffect")

items = json.loads(MC.read_text(encoding="utf-8"))["items"]
print(f"已缓存材料 {len(items)} 项\n")
for rid, entry in items.items():
    kind = entry.get("text_template_resource_type") or entry.get("sub_type") or "?"
    path = entry.get("path") or ""
    name = entry.get("name") or entry.get("title") or ""
    print(f"== {rid} | name={name} | type={kind} | effect_type={entry.get('effect_type')}")
    for label, base in (("lyra", LYRA), ("artist", ARTIST)):
        folder = base
        for part in ("text_template", "lyric_animation", "anim_text"):
            candidate = folder / part / rid
            if candidate.is_dir():
                leaves = [p for p in candidate.rglob("*") if p.is_dir() and any(x.is_file() for x in p.iterdir())]
                for leaf in leaves[:4]:
                    files = sorted(x.name for x in leaf.iterdir() if x.is_file())
                    print(f"    [{label}/{part}] {leaf.relative_to(candidate)} -> {files[:12]}")
    if path:
        p = Path(path)
        print(f"    记录路径存在: {p.is_dir()} | {p}")
        if p.is_dir():
            print(f"      文件: {sorted(x.name for x in p.iterdir())[:14]}")
    print()
