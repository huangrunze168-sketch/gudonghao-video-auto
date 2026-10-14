# -*- coding: utf-8 -*-
"""Dump 测试.jypack 解密后的时间线结构摘要（只读分析用）。"""
import json
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\Administrator\Documents\剪映")
sys.path.insert(0, str(ROOT / "engine"))
import windows_runtime  # noqa: E402

SRC = ROOT / "work" / "jypack-inspect" / "extracted" / "draft_content.json"
OUT = ROOT / "work" / "jypack-inspect" / "structure.txt"

t = windows_runtime._decrypt_metadata_in_memory(SRC)
lines = []


def p(*parts):
    lines.append(" ".join(str(x) for x in parts))


def txt(material):
    content = material.get("content")
    if not isinstance(content, str):
        return ""
    try:
        value = json.loads(content)
    except ValueError:
        return content[:80]
    return value.get("text", "") if isinstance(value, dict) else ""


p("TOP:", sorted(t.keys()))
p("id", t.get("id"), "duration_us", t.get("duration"), "fps", t.get("fps"),
  "canvas", t.get("canvas_config"), "ratio", t.get("ratio"))
cfg = t.get("config") or {}
p("config keys", sorted(cfg.keys()))
p("platform", json.dumps((t.get("platform") or {}), ensure_ascii=False))
p("last_modified_platform", json.dumps((t.get("last_modified_platform") or {}), ensure_ascii=False))

m = t.get("materials") or {}
p("")
p("MATERIAL KEYS:", sorted(m.keys()))
for key in sorted(m.keys()):
    value = m[key]
    if isinstance(value, list):
        p(" ", key, len(value))

p("")
p("========== AUDIOS ==========")
for it in m.get("audios") or []:
    p(" ", it.get("id"), "|type=", it.get("type"), "|name=", it.get("name"),
      "|dur=", it.get("duration"), "|music_id=", it.get("music_id"))
    p("      path=", it.get("path"))
    for extra in ("tone_type", "tone_speaker", "resource_id", "app_id", "category_name"):
        if it.get(extra):
            p("      ", extra, "=", it.get(extra))

p("")
p("========== VIDEOS ==========")
for it in m.get("videos") or []:
    p(" ", it.get("id"), "|type=", it.get("type"), "|dur=", it.get("duration"),
      "|w/h=", it.get("width"), it.get("height"), "|mat=", it.get("material_name"))
    p("      path=", it.get("path"))
    p("      extra_keys=", sorted(k for k in it.keys() if k not in
                                 {"id", "type", "duration", "width", "height", "path", "material_name"})[:20])

p("")
p("========== TEXTS ==========")
for it in m.get("texts") or []:
    p(" ", it.get("id"), "|type=", it.get("type"), "|text=", repr(txt(it)))
    if it.get("type") != "lyrics":
        p("      keys=", sorted(it.keys())[:24])

p("")
p("========== TEXT_TEMPLATES ==========")
for it in m.get("text_templates") or []:
    p(" ", it.get("id"), "|type=", it.get("type"), "|res=", it.get("resource_id"))
    p("      keys=", sorted(it.keys()))
    p("      json=", json.dumps(it, ensure_ascii=False)[:400])

p("")
p("========== STICKERS ==========")
for it in m.get("stickers") or []:
    p(" ", json.dumps(it, ensure_ascii=False)[:300])

p("")
p("========== MATERIAL_ANIMATIONS ==========")
for it in m.get("material_animations") or []:
    p(" ", json.dumps(it, ensure_ascii=False)[:260])

p("")
p("========== PLACEHOLDER_INFOS ==========")
for it in m.get("placeholder_infos") or []:
    p(" ", json.dumps(it, ensure_ascii=False)[:300])

p("")
p("========== TRACKS ==========")
by_id = {}
for key in ("audios", "videos", "texts", "stickers", "text_templates"):
    for it in m.get(key) or []:
        by_id[it.get("id")] = (key, it)
for track in t.get("tracks") or []:
    segs = track.get("segments") or []
    p("TRACK", track.get("type"), "|id=", track.get("id"), "|segs=", len(segs),
      "|flag=", track.get("flag"), "|attr=", track.get("attribute"))
    for seg in segs:
        mid = seg.get("material_id")
        kind, material = by_id.get(mid, ("?", {}))
        label = ""
        if kind == "texts":
            label = repr(txt(material))[:60]
        elif kind == "audios":
            label = "audio:" + str(material.get("name"))
        elif kind == "videos":
            label = "video:" + str(Path(str(material.get("path"))).name)
        elif kind == "stickers":
            label = "sticker:" + str(material.get("resource_id"))
        elif kind == "text_templates":
            label = "tpl:" + str(material.get("resource_id"))
        p("   seg", mid, kind, label)
        p("      target=", json.dumps(seg.get("target_timerange")),
          "source=", json.dumps(seg.get("source_timerange")))
        extra = {k: v for k, v in seg.items()
                 if k not in {"material_id", "target_timerange", "source_timerange", "id",
                              "render_index", "track_render_index"}}
        if extra:
            p("      extra=", json.dumps(extra, ensure_ascii=False)[:400])

OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("written", OUT, len(lines), "lines")
