# -*- coding: utf-8 -*-
"""歌词完全走剪映 CLI：官方识别 + 官方歌词动效，端到端验证是否出字。"""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\Administrator\Documents\剪映")
SKILL = ROOT / "skills" / "guzhu-hao" / "scripts"
sys.path.insert(0, str(ROOT / "engine"))
sys.path.insert(0, str(SKILL))

import lyra_cli  # noqa: E402
import windows_runtime as w  # noqa: E402
from guzhu_common import EngineCrypto, resolve_project  # noqa: E402
from guzhu_jypack import read_package  # noqa: E402
from guzhu_timeline import inspect_template  # noqa: E402

DR = Path(w.DRAFT_ROOT).resolve()
NAME = "guzhu-lyric-cli"
FOLDER = DR / NAME
BATCH = ROOT / "work" / "guzhu-test" / "batch-lyric-cli.json"
OUT = ROOT / "work" / "guzhu-lyric-cli"


def run_script(script, arguments, timeout=1800):
    completed = subprocess.run([sys.executable, str(ROOT / "engine" / script), *arguments],
                               capture_output=True, cwd=str(ROOT), timeout=timeout)
    if completed.returncode:
        print("  %s 失败: %s" % (script, completed.stderr.decode("utf-8", "replace")[-300:]))
    return completed.returncode


def sync(workspace):
    if Path(workspace).exists():
        shutil.rmtree(workspace)
    run_script("draftediting_runtime.py", ["init", "--workspace", str(workspace)])
    run_script("draftediting_runtime.py",
               ["sync", "--workspace", str(workspace), "--ref", "local://" + NAME,
                "--draft-root", str(DR)])


def sync_mirrors():
    timelines = sorted((FOLDER / "Timelines").glob("*/draft_content.json"))
    source = max(timelines, key=lambda path: path.stat().st_mtime_ns)
    for mirror in (FOLDER / "draft_content.json", FOLDER / "template-2.tmp",
                   source.parent / "template-2.tmp"):
        shutil.copyfile(source, mirror)
    return source.parent.name


# 1) 生成不含歌词的草稿
print("[1] build 无歌词草稿")
print(subprocess.run([sys.executable, str(SKILL / "guzhu_batch.py"), "build", "--batch", str(BATCH)],
                     capture_output=True, cwd=str(ROOT)).stdout.decode("utf-8", "replace")[-400:])

# 2) 安装成 ASCII 名草稿
print("[2] 安装草稿")
if FOLDER.exists():
    shutil.rmtree(FOLDER)
FOLDER.mkdir(parents=True)
package = read_package(OUT / "jypack" / "问春风.jypack", None, decrypt=False)
for name in package.names():
    if name.endswith("/"):
        continue
    target = FOLDER / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(package.read(name))

# 3) 定位主歌音乐段的 seg-id
skeleton = inspect_template(read_package(OUT / "jypack" / "问春风.jypack",
                                         EngineCrypto(resolve_project())).timeline)
main_ids = [segment.get("id") for _, segment, _ in skeleton.main_music]
print("[3] 主歌音乐段:", main_ids)

WS = Path(r"C:\Temp\lyric-cli-ws")
sync(WS)
id_map = json.loads((WS / "id_map.json").read_text(encoding="utf-8"))
by_seg = {item["seg_id"]: item["xml_id"] for item in id_map}
music_xml = [by_seg.get(item) for item in main_ids]
print("    对应 xml_id:", music_xml)

# 4) 官方歌词识别（只用主歌段）
print("[4] lyrics recognize --mode segment")
try:
    result = lyra_cli.lyrics_recognize(str(DR), "local://" + NAME, language="zh",
                                       mode="segment",
                                       seg_id=main_ids[0], timeout=1800)
    print("    识别句数:", len(lyra_cli.lyrics_recognized_sentences(result)))
    for cue in lyra_cli.recognized_cues(result)[:12]:
        print("      %6d-%6d ms  %s" % (cue["start_ms"], cue["end_ms"], cue["text"]))
except Exception as error:  # noqa: BLE001 - 官方识别探测
    print("    失败:", str(error)[:400])
sync_mirrors()

# 5) 重新 sync，找歌词 <text> 段
WS2 = Path(r"C:\Temp\lyric-cli-ws2")
sync(WS2)
xml = (WS2 / "current_draft.xml").read_text(encoding="utf-8", errors="replace")
lyric_xml = [m.group(1) for m in re.finditer(r'<text id="([^"]+)"[^>]*>(?:(?!</text>).)*?</text>', xml, re.S)
             if "<template" not in m.group(0)]
print("[5] 可套动效的 <text> 段:", lyric_xml)
id_map2 = json.loads((WS2 / "id_map.json").read_text(encoding="utf-8"))
seg2 = {item["xml_id"]: item["seg_id"] for item in id_map2}

# 6) 官方歌词动效（lyric_animation 资源）
print("[6] lyrics animation update --resource vimo://7591420714515844395")
for xml_id in lyric_xml[:1]:
    try:
        outcome = lyra_cli.lyrics_animation_update(
            str(DR), "local://" + NAME, seg2[xml_id],
            "vimo://7591420714515844395", timeout=900)
        print("    成功:", json.dumps(outcome, ensure_ascii=False)[:400])
    except Exception as error:  # noqa: BLE001 - 官方动效探测
        print("    失败:", str(error)[:500])
sync_mirrors()

# 7) 渲染
print("[7] 渲染")
RENDER = ROOT / "work" / "guzhu-lyric-cli-render"
if RENDER.exists():
    shutil.rmtree(RENDER)
completed = subprocess.run(
    [sys.executable, str(ROOT / "engine" / "jypack_render.py"),
     "--input", str(OUT / "jypack" / "问春风.jypack"), "--out", str(RENDER),
     "--draft-dir", str(FOLDER), "--width", "1280", "--height", "720", "--timeout", "900"],
    capture_output=True, cwd=str(ROOT))
print("    rc =", completed.returncode, completed.stderr.decode("utf-8", "replace")[-200:])
if (RENDER / "render.mp4").is_file():
    log = (RENDER / "native.stdout.log").read_text(encoding="utf-8", errors="replace")
    print("    addTemplate 报错:", log.count("content path not invalid"),
          "| LyricStyle 相关:", log.count("LyricStyle"))
    for stamp in (3, 12, 20):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(stamp),
                        "-i", str(RENDER / "render.mp4"), "-frames:v", "1",
                        str(RENDER / ("c-%d.png" % stamp))], capture_output=True)
    print("    已抽帧")
