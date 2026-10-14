"""对官方识别出的歌词段逐段套用"浪漫氛围"歌词动效，然后渲染。"""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "engine"))
import draftediting_runtime as dr  # noqa: E402
import headless_pipeline as hp  # noqa: E402
import jypack_render  # noqa: E402

DRAFT_ROOT = Path(r"C:\Users\Administrator\AppData\Local\JianyingPro\User Data\Projects\com.lveditor.draft")
NAME = "headless-official3"
DST = DRAFT_ROOT / NAME
JYPACK = Path(r"C:\Users\Administrator\Desktop\剪映测试\测试.jypack")
OUT = ROOT / "work" / "run-official4"
WS = Path(os.environ["LOCALAPPDATA"]) / "Temp" / "jianying-draftediting" / "ws-official3"
RESOURCE = "vimo://7591420714515844395"  # 浪漫氛围

ref = dr.local_ref(NAME)
id_map = {item["xml_id"]: item["seg_id"]
          for item in json.loads((WS / "id_map.json").read_text(encoding="utf-8"))}
targets = [id_map[key] for key in sorted(id_map)
           if key.startswith("t") and key[1:].isdigit() and int(key[1:]) >= 12]
print("歌词段:", len(targets))

succeeded = 0
for seg_id in targets:
    args = ["draft", "lyrics", "animation", "update", "--ref", ref,
            "--seg-id", seg_id, "--resource", RESOURCE, "--language", "zh-CN"]
    try:
        result = dr.run_lyra(args, DRAFT_ROOT, 600, [WS, DST])
        succeeded += 1
        print(f"  {seg_id[:8]} OK {json.dumps(result['result'], ensure_ascii=False)[:160]}")
    except Exception as error:  # noqa: BLE001
        print(f"  {seg_id[:8]} 失败 {str(error)[:260]}")

print(f"成功 {succeeded}/{len(targets)}")
print("mirrors:", json.dumps(hp.sync_draft_mirrors(DST), ensure_ascii=False)[:180])

if succeeded:
    rendered = jypack_render.render(str(JYPACK), str(OUT), draft_dir=str(DST))
    print("RENDER:", json.dumps({key: rendered[key] for key in
                                 ("output", "output_size", "video_duration")},
                                ensure_ascii=False))
