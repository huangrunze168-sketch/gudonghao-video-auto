"""官方歌词链路：歌词识别 → 应用歌词动效（浪漫氛围）→ 原生渲染。

对应用户在剪映里的操作：字幕 → 歌词识别 → 选歌词动效模板。
"""
import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "engine"))
import draftediting_runtime as dr  # noqa: E402
import headless_pipeline as hp  # noqa: E402
import jypack_render  # noqa: E402

DRAFT_ROOT = Path(r"C:\Users\Administrator\AppData\Local\JianyingPro\User Data\Projects\com.lveditor.draft")
SRC = DRAFT_ROOT / "测试 (1)"
NAME = "headless-official3"
DST = DRAFT_ROOT / NAME
JYPACK = Path(r"C:\Users\Administrator\Desktop\剪映测试\测试.jypack")
OUT = ROOT / "work" / "run-official3"
WS = Path(os.environ["LOCALAPPDATA"]) / "Temp" / "jianying-draftediting" / "ws-official3"
RESOURCE = "vimo://7591420714515844395"  # 浪漫氛围


def show(title, payload):
    print("=" * 20, title)
    print(json.dumps(payload, ensure_ascii=False)[:1600])


if not DST.exists():
    shutil.copytree(SRC, DST)
if not WS.exists() or not any(WS.iterdir()):
    dr.blueprint_init(WS)
ref = dr.local_ref(NAME)
dr.blueprint_sync(WS, ref, DRAFT_ROOT)
print("ref:", ref)

# 1. 官方歌词识别（写入草稿）
try:
    result = dr.run_lyra(["draft", "lyrics", "recognize", "--ref", ref, "--language", "zh"],
                         DRAFT_ROOT, 1800, [WS, DST])
    show("lyrics recognize", result["result"])
except Exception as error:  # noqa: BLE001
    show("lyrics recognize 失败", {"error": str(error)[:1600]})

# 2. 应用歌词动效（用户的"浪漫氛围"）
try:
    result = dr.run_lyra(["draft", "lyrics", "animation", "add", "--ref", ref,
                          "--resource", RESOURCE, "--language", "zh-CN"],
                         DRAFT_ROOT, 900, [WS, DST])
    show("lyrics animation add", result["result"])
except Exception as error:  # noqa: BLE001
    show("lyrics animation add 失败", {"error": str(error)[:1600]})

# 3. 同步镜像并渲染
try:
    show("mirrors", hp.sync_draft_mirrors(DST))
except Exception as error:  # noqa: BLE001
    show("mirrors 失败", {"error": str(error)[:600]})

try:
    rendered = jypack_render.render(str(JYPACK), str(OUT), draft_dir=str(DST))
    show("render", {key: rendered[key] for key in ("output", "output_size", "video_duration")})
except Exception as error:  # noqa: BLE001
    show("render 失败", {"error": str(error)[:900]})
