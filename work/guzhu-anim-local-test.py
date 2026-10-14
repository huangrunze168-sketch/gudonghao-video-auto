# -*- coding: utf-8 -*-
"""最后一条路：用本地已有 content.json 的模板替换草稿里的坏模板卡，看能否出字。"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\Administrator\Documents\剪映")
sys.path.insert(0, str(ROOT / "engine"))
sys.path.insert(0, str(ROOT / "skills" / "guzhu-hao" / "scripts"))

import windows_runtime as w  # noqa: E402
from guzhu_jypack import read_package  # noqa: E402

DR = Path(w.DRAFT_ROOT).resolve()
CACHE = Path(r"C:\Users\Administrator\AppData\Local\JianyingPro\User Data\Cache\artistEffect")

usable = []
for folder in CACHE.iterdir():
    if not folder.is_dir():
        continue
    hits = list(folder.rglob("content.json"))
    if not hits:
        continue
    try:
        blob = hits[0].read_text(encoding="utf-8", errors="replace")
    except OSError:
        continue
    usable.append({"resource_id": folder.name, "content": str(hits[0].parent),
                   "blob": blob[:4000]})
print("本地有 content.json 的模板数:", len(usable))

# 优先挑 content.json 里带文本/字幕特征的
scored = sorted(usable, key=lambda item: -sum(
    item["blob"].lower().count(key) for key in ("text", "subtitle", "font", "lyric")))
for item in scored[:6]:
    hits = sum(item["blob"].lower().count(k) for k in ("text", "subtitle", "font", "lyric"))
    print("  %s  特征分=%d" % (item["resource_id"], hits))
chosen = scored[0]
print("\n选用:", chosen["resource_id"], "->", chosen["content"])

NAME = "guzhu-anim-local"
FOLDER = DR / NAME
if FOLDER.exists():
    shutil.rmtree(FOLDER)
FOLDER.mkdir(parents=True)
package = read_package(ROOT / "work" / "guzhu-roundtrip" / "roundtrip.jypack", None, decrypt=False)
for name in package.names():
    if name.endswith("/"):
        continue
    target = FOLDER / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(package.read(name))

timeline_file = next(FOLDER.glob("Timelines/*/draft_content.json"))
timeline = w._decrypt_metadata_in_memory(timeline_file)
patched = 0
for node in timeline["materials"].get("text_templates") or []:
    node["resource_id"] = chosen["resource_id"]
    node["effect_id"] = chosen["resource_id"]
    node["path"] = chosen["content"].replace("\\", "/")
    patched += 1
print("已改写模板卡:", patched)

payload = json.dumps(timeline, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
mirrors = [timeline_file, timeline_file.parent / "template-2.tmp",
           FOLDER / "draft_content.json", FOLDER / "template-2.tmp"]
for mirror in mirrors:
    if mirror.exists():
        mirror.unlink()
    w._encrypt_metadata_from_memory(payload, mirror)
print("已写回并同步镜像")

OUT = ROOT / "work" / "guzhu-anim-local-render"
if OUT.exists():
    shutil.rmtree(OUT)
completed = subprocess.run(
    [sys.executable, str(ROOT / "engine" / "jypack_render.py"),
     "--input", str(ROOT / "work" / "guzhu-roundtrip" / "roundtrip.jypack"),
     "--out", str(OUT), "--draft-dir", str(FOLDER),
     "--width", "2276", "--height", "1280", "--timeout", "900"],
    capture_output=True, cwd=str(ROOT))
print("渲染 rc =", completed.returncode)
print(completed.stderr.decode("utf-8", "replace")[-400:])
if (OUT / "render.mp4").is_file():
    log = (OUT / "native.stdout.log").read_text(encoding="utf-8", errors="replace")
    print("addTemplate 报错次数:", log.count("content path not invalid"))
    for stamp in (12, 21, 28):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(stamp),
                        "-i", str(OUT / "render.mp4"), "-frames:v", "1",
                        str(OUT / ("f-%d.png" % stamp))], capture_output=True)
    print("已抽帧")
