"""A：用联网开关把缺失字体下载下来，解禁依赖不全的歌词模板。

做法：对每个"依赖缺失"的歌词动效资源，在**放开沙箱网络**的前提下套一次
``draft lyrics animation update``——官方会去下载它缺的字体。下载成功后缓存里
会出现 ``Cache/lyra-cli/material-cache/font/<id>/font.ttf``，该模板即可用。
"""
import shutil
import sys
import tempfile
import uuid
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(r"C:\Users\Administrator\Documents\剪映")
sys.path.insert(0, str(ROOT / "skills" / "guzhu-hao" / "scripts"))
sys.path.insert(0, str(ROOT / "engine"))

import guzhu_batch as gb  # noqa: E402
import lyra_cli  # noqa: E402
from guzhu_anim import (animation_catalog, animation_dependencies_ready,  # noqa: E402
                        effect_pool)
from guzhu_timeline import Editor  # noqa: E402

root = gb.draft_root(str(ROOT))
folders = sorted((d for d in Path(root).iterdir() if d.name.startswith("guzhu-")),
                 key=lambda p: p.stat().st_mtime_ns, reverse=True)
folder = folders[0]
ref = "local://" + folder.name
timeline, _src = gb.read_draft_timeline(str(ROOT), folder)
editor = Editor(timeline)
seg_id = None
for _track, segment in editor.segments():
    material_id = segment.get("material_id")
    if not material_id:
        continue
    node = editor.node(material_id) or {}
    if str(node.get("type")) != "subtitle" and editor.bucket(material_id) == "texts":
        seg_id = segment.get("id")
        break
if not seg_id:
    raise SystemExit("草稿里没有可用于套动效的歌词段")
print("草稿 %s，歌词段 %s" % (folder.name, str(seg_id)[:12]))

items = animation_catalog()
names = effect_pool().get("text_templates") or {}
missing = [item for item in items if not animation_dependencies_ready(item.get("style"))]
print("待下载依赖的动效 %d 个（其中资源池里有中文名的 %d 个）"
      % (len(missing), sum(1 for item in missing if item["id"] in names)))

workspace = Path(tempfile.gettempdir()) / ("guzhu-dl-%s" % uuid.uuid4().hex[:8])
gb._project_script(str(ROOT), "draftediting_runtime.py", ["init", "--workspace", str(workspace)])
gb._project_script(str(ROOT), "draftediting_runtime.py",
                   ["sync", "--workspace", str(workspace), "--ref", ref,
                    "--draft-root", str(root)])

done = failed = 0
for item in missing:
    resource_id = item["id"]
    label = names.get(resource_id) or item.get("title") or resource_id
    try:
        lyra_cli.lyrics_animation_update(str(root), ref, seg_id,
                                         resource="vimo://" + resource_id,
                                         workspace=workspace, timeout=600)
        done += 1
        print("  OK   %-20s %s" % (resource_id, label))
    except Exception as error:  # noqa: BLE001
        failed += 1
        print("  失败 %-20s %-18s %s" % (resource_id, label,
                                        str(error).replace("\n", " ")[:110]))
shutil.rmtree(workspace, ignore_errors=True)
print("\n成功 %d，失败 %d" % (done, failed))

ready = [item for item in animation_catalog() if animation_dependencies_ready(item.get("style"))]
print("现在依赖齐全的动效：%d / %d" % (len(ready), len(animation_catalog())))
