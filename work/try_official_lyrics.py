"""用官方原生链路做「歌词识别 + 歌词动效」，复现剪映里的操作。

对应剪映界面：字幕 → 歌词识别 → 选歌词动效模板。
命令：
  draft lyrics recognize --language zh
  draft lyrics animation add --resource vimo://7591420714515844395   # 浪漫氛围
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
NAME = "headless-official-lyrics2"
DST = DRAFT_ROOT / NAME
JYPACK = Path(r"C:\Users\Administrator\Desktop\剪映测试\测试.jypack")
OUT = ROOT / "work" / "run-official-lyrics"
WS = Path(os.environ["LOCALAPPDATA"]) / "Temp" / "jianying-draftediting" / "ws-official"
LYRIC_RESOURCE = "vimo://7591420714515844395"  # 浪漫氛围


def step(title, payload):
    print("=" * 22, title)
    print(json.dumps(payload, ensure_ascii=False)[:1200])


if DST.exists():
    shutil.rmtree(DST)
shutil.copytree(SRC, DST)
if not WS.exists() or not any(WS.iterdir()):
    dr.blueprint_init(WS)
ref = dr.local_ref(NAME)
dr.blueprint_sync(WS, ref, DRAFT_ROOT)
step("sync", {"ref": ref, "draft": str(DST)})

try:
    result = dr.run_lyra(["draft", "lyrics", "recognize", "--ref", ref, "--language", "zh"],
                         DRAFT_ROOT, 1200, [WS, DST])
    step("lyrics recognize", result["result"])
except Exception as error:  # noqa: BLE001
    step("lyrics recognize 失败", {"error": str(error)[:1500]})

try:
    result = dr.run_lyra(["draft", "lyrics", "animation", "add", "--ref", ref,
                          "--resource", LYRIC_RESOURCE, "--language", "zh-CN", "--cover-old"],
                         DRAFT_ROOT, 1200, [WS, DST])
    step("lyrics animation add", result["result"])
except Exception as error:  # noqa: BLE001
    step("lyrics animation add 失败", {"error": str(error)[:1500]})

# 官方命令只写 Timelines 下的时间线，渲染读根文件，必须先同步镜像
try:
    step("mirrors", hp.sync_draft_mirrors(DST))
except Exception as error:  # noqa: BLE001
    step("mirrors 失败", {"error": str(error)[:600]})

try:
    rendered = jypack_render.render(str(JYPACK), str(OUT), draft_dir=str(DST))
    step("render", {key: rendered[key] for key in ("output", "output_size", "video_duration")})
except Exception as error:  # noqa: BLE001
    step("render 失败", {"error": str(error)[:1200]})
