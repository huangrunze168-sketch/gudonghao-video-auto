# -*- coding: utf-8 -*-
"""Dump 一条 subtitle 文字素材及其关联材料的完整结构。"""
import json
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\Administrator\Documents\剪映")
sys.path.insert(0, str(ROOT / "engine"))
import windows_runtime  # noqa: E402

SRC = ROOT / "work" / "jypack-inspect" / "extracted" / "draft_content.json"
OUT = ROOT / "work" / "jypack-inspect" / "text-material.txt"

t = windows_runtime._decrypt_metadata_in_memory(SRC)
m = t["materials"]
by_id = {}
for key, nodes in m.items():
    if isinstance(nodes, list):
        for node in nodes:
            if isinstance(node, dict) and node.get("id"):
                by_id[node["id"]] = (key, node)

lines = []


def p(*parts):
    lines.append(" ".join(str(x) for x in parts))


TEXT_ID = "3B1370D4-E32C-41df-BC7B-A72C3C780353"   # 家人们别划走（subtitle）
TPL_ID = "114C6B44-684D-48b3-9958-C85CFF027E5F"    # 第一张歌词模板卡

kind, node = by_id[TEXT_ID]
p("===== subtitle material:", TEXT_ID, "bucket=", kind)
p(json.dumps(node, ensure_ascii=False, indent=2))
p("")
p("===== 该素材 content 解析后")
p(json.dumps(json.loads(node["content"]), ensure_ascii=False, indent=2))

# 找引用它的 segment，列出 extra_material_refs
for track in t["tracks"]:
    for seg in track.get("segments") or []:
        if seg.get("material_id") == TEXT_ID:
            p("")
            p("===== segment in track", track.get("type"), json.dumps(seg, ensure_ascii=False, indent=2)[:1500])
            for ref in seg.get("extra_material_refs") or []:
                if ref in by_id:
                    bucket, refnode = by_id[ref]
                    p("")
                    p("--- ref", ref, "bucket=", bucket)
                    p(json.dumps(refnode, ensure_ascii=False, indent=2)[:1800])

kind, tpl = by_id[TPL_ID]
p("")
p("===== 歌词模板卡完整结构:", TPL_ID)
p(json.dumps(tpl, ensure_ascii=False, indent=2)[:4000])
for track in t["tracks"]:
    for seg in track.get("segments") or []:
        if seg.get("material_id") == TPL_ID:
            p("")
            p("===== 模板卡 segment 完整结构")
            p(json.dumps(seg, ensure_ascii=False, indent=2)[:2500])
            for ref in seg.get("extra_material_refs") or []:
                if ref in by_id:
                    bucket, refnode = by_id[ref]
                    p("--- ref", ref, "bucket=", bucket)
                    p(json.dumps(refnode, ensure_ascii=False, indent=2)[:1200])

OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("written", OUT)
