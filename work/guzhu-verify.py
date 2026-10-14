# -*- coding: utf-8 -*-
"""校验生成的 jypack：镜像一致性、素材引用、轨道结构。"""
import hashlib
import sys
from pathlib import Path

SKILL = Path(r"C:\Users\Administrator\Documents\剪映\skills\guzhu-hao\scripts")
sys.path.insert(0, str(SKILL))

from guzhu_common import EngineCrypto, resolve_project  # noqa: E402
from guzhu_jypack import read_package  # noqa: E402
from guzhu_timeline import Editor, inspect_template, range_of  # noqa: E402

TARGET = Path(sys.argv[1] if len(sys.argv) > 1
              else r"C:\Users\Administrator\Documents\剪映\work\guzhu-run-01\jypack\问春风.jypack")

crypto = EngineCrypto(resolve_project())
package = read_package(TARGET, crypto)
timeline = package.timeline
editor = Editor(timeline)
ident = timeline["id"]

print("包体积 %.2f MB，条目 %d" % (TARGET.stat().st_size / 1e6, len(package.names())))
print("时间线 id:", ident, "  总时长: %.3fs" % (timeline["duration"] / 1e6))

print("\n== 草稿镜像一致性 ==")
names = [name for name in package.names()
         if name == "draft_content.json" or name.startswith("Timelines/%s/" % ident)
         or name in ("template-2.tmp", "draft_content.json.bak")]
digests = {}
for name in names:
    if name.endswith(("draft_content.json", "template-2.tmp", ".bak")):
        digests.setdefault(hashlib.sha256(package.read(name)).hexdigest(), []).append(name)
print("镜像组数（应为 1）:", len(digests))
for digest, group in digests.items():
    print("  ", digest[:16], group)

print("\n== 素材条目 ==")
for name in package.names():
    if name.startswith(("textReading/", "ImportedMaterials/", "Resources/")):
        print("  %9d  %s" % (len(package.read(name)), name))

print("\n== 轨道 ==")
skeleton = inspect_template(timeline)
for track in timeline["tracks"]:
    segments = track.get("segments") or []
    print("  %-8s 片段 %d" % (track.get("type"), len(segments)))
    for segment in sorted(segments, key=lambda item: range_of(item)[0]):
        start, duration = range_of(segment)
        material_id = segment.get("material_id")
        node = editor.node(material_id) or {}
        bucket = editor.bucket(material_id)
        label = ""
        if bucket == "audios":
            label = "audio:%s %.3fs" % (node.get("name"), (node.get("duration") or 0) / 1e6)
        elif bucket == "texts":
            label = "text:" + str(node.get("recognize_text") or node.get("content", ""))[:36]
        elif bucket == "videos":
            label = "video:" + Path(str(node.get("path"))).name[-28:]
        elif bucket == "stickers":
            label = "sticker:" + str(node.get("resource_id"))
        print("      %8.3fs +%7.3fs  %-10s %s" % (start / 1e6, duration / 1e6, bucket, label))

print("\n== 音频素材引用 ==")
for node in timeline["materials"].get("audios") or []:
    print("  %-10s %-22s %.3fs" % (node.get("type"), node.get("name"),
                                   (node.get("duration") or 0) / 1e6))
    print("      " + str(node.get("path")))
