"""用 draft lyrics animation update 逐段套用官方歌词动效（浪漫氛围）。"""
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
NAME = "headless-lyrics-update"
DST = DRAFT_ROOT / NAME
JYPACK = Path(r"C:\Users\Administrator\Desktop\剪映测试\测试.jypack")
OUT = ROOT / "work" / "run-lyrics-update"
WS = Path(os.environ["LOCALAPPDATA"]) / "Temp" / "jianying-draftediting" / "ws-update"
RESOURCE = "vimo://7591420714515844395"  # 浪漫氛围
TARGETS = [
    "F115244E-ED22-409a-91DC-4FBFD7627BAF",  # t1（segment_text）
    "83E2C964-6C6B-4a5a-8C3E-B85597765742",  # t2
    "D558DFE7-27EE-4818-87C1-2C1B18F66F6C",  # t3
    "280EAF16-0D36-44f2-97F9-C8C8517D2EDC",  # t4
    "9857A870-3A18-4905-A45F-CF7C61F65ED9",  # t5
]

if not DST.exists():
    shutil.copytree(SRC, DST)
if not WS.exists() or not any(WS.iterdir()):
    dr.blueprint_init(WS)
ref = dr.local_ref(NAME)
dr.blueprint_sync(WS, ref, DRAFT_ROOT)
print("ref:", ref)

for target in TARGETS:
    args = ["draft", "lyrics", "animation", "add", "--ref", ref,
            "--seg-id", target, "--resource", RESOURCE, "--language", "zh-CN", "--cover-old"]
    try:
        result = dr.run_lyra(args, DRAFT_ROOT, 600, [WS, DST])
        print(f"[{target}] OK", json.dumps(result["result"], ensure_ascii=False)[:300])
    except Exception as error:  # noqa: BLE001
        print(f"[{target}] 失败", str(error)[:400])

try:
    print("mirrors:", json.dumps(hp.sync_draft_mirrors(DST), ensure_ascii=False)[:200])
except Exception as error:  # noqa: BLE001
    print("mirrors 失败", str(error)[:300])

try:
    rendered = jypack_render.render(str(JYPACK), str(OUT), draft_dir=str(DST))
    print("render:", json.dumps({key: rendered[key] for key in ("output", "output_size", "video_duration")}, ensure_ascii=False))
except Exception as error:  # noqa: BLE001
    print("render 失败", str(error)[:600])
