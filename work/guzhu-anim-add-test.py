# -*- coding: utf-8 -*-
"""验证：官方 lyrics animation add 能否把坏歌词模板换成可用模板并下载资源。"""
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\Administrator\Documents\剪映")
sys.path.insert(0, str(ROOT / "engine"))
sys.path.insert(0, str(ROOT / "skills" / "guzhu-hao" / "scripts"))

import lyra_cli  # noqa: E402
import windows_runtime  # noqa: E402
from guzhu_jypack import read_package  # noqa: E402

DR = Path(windows_runtime.DRAFT_ROOT).resolve()
NAME = "guzhu-anim-test"
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
print("已安装模板副本（含原歌词动效卡）:", FOLDER)

WS = Path(r"C:\Temp\anim-ws")
if WS.exists():
    shutil.rmtree(WS)
for arguments in (["init", "--workspace", str(WS)],
                  ["sync", "--workspace", str(WS), "--ref", "local://" + NAME,
                   "--draft-root", str(DR)]):
    completed = subprocess.run([sys.executable, str(ROOT / "engine" / "draftediting_runtime.py"),
                                *arguments], capture_output=True, cwd=str(ROOT))
    print(arguments[0], "rc =", completed.returncode)
    if completed.returncode:
        print(completed.stderr.decode("utf-8", "replace")[-600:])

CACHE = Path(r"C:\Users\Administrator\AppData\Local\JianyingPro\User Data\Cache\artistEffect")


def cache_state(resource_id):
    folder = CACHE / resource_id
    if not folder.is_dir():
        return "无缓存"
    hits = list(folder.rglob("content.json"))
    return "content.json x%d" % len(hits) if hits else "无 content.json"


print("\n调用前 7638543120313142553 :", cache_state("7638543120313142553"))
print("调用前 7591420714515844395 :", cache_state("7591420714515844395"))

for resource in ("vimo://7638543120313142553", "vimo://7628140934768692542"):
    print("\n===== lyrics animation add  %s =====" % resource)
    try:
        result = lyra_cli.lyrics_animation_add(str(DR), "local://" + NAME, resource, timeout=900)
        print("成功:", str(result)[:700])
    except Exception as error:  # noqa: BLE001 - 探测哪条路径可用
        print("失败:", str(error)[:500])
    rid = resource.split("/")[-1]
    print("调用后缓存:", cache_state(rid))
