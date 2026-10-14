"""把"浪漫氛围"歌词动效补齐到所有官方识别歌词段。

每次应用动效都会重建该段（UUID 变化），因此每轮都要重新 sync 再取 id。
"""
import json
import os
import re
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
OUT = ROOT / "work" / "run-official5"
WS = Path(os.environ["LOCALAPPDATA"]) / "Temp" / "jianying-draftediting" / "ws-official3"
RESOURCE = "vimo://7591420714515844395"  # 浪漫氛围
ref = dr.local_ref(NAME)


def pending_lyric_segments():
    """返回尚未套用歌词动效的 t* 段（canonical XML 里没有 <template> 的）。"""
    dr.blueprint_sync(WS, ref, DRAFT_ROOT)
    id_map = {item["xml_id"]: item["seg_id"]
              for item in json.loads((WS / "id_map.json").read_text(encoding="utf-8"))}
    text = (WS / "current_draft.xml").read_text(encoding="utf-8", errors="replace")
    pending, current, has_template = [], None, False
    for line in text.splitlines():
        stripped = line.strip()
        opened = re.match(r'<text id="(t\d+)"', stripped)
        if opened:
            current, has_template = opened.group(1), False
            continue
        if current and stripped.startswith("<template"):
            has_template = True
            continue
        if current and ("</text>" in stripped or stripped.startswith("<text ")):
            if not has_template:
                pending.append(current)
            current = None
    if current and not has_template:
        pending.append(current)
    return [(xml_id, id_map[xml_id]) for xml_id in pending if xml_id in id_map]


applied = 0
for round_no in range(1, 16):
    todo = pending_lyric_segments()
    print(f"第 {round_no} 轮：待处理 {len(todo)} 段", [item[0] for item in todo][:6])
    if not todo:
        break
    xml_id, seg_id = todo[0]
    args = ["draft", "lyrics", "animation", "update", "--ref", ref,
            "--seg-id", seg_id, "--resource", RESOURCE, "--language", "zh-CN"]
    try:
        dr.run_lyra(args, DRAFT_ROOT, 600, [WS, DST])
        applied += 1
        print(f"    {xml_id} 已套用")
    except Exception as error:  # noqa: BLE001
        print(f"    {xml_id} 失败 {str(error)[:220]}")
        break

print(f"本轮共套用 {applied} 段")
print("mirrors:", json.dumps(hp.sync_draft_mirrors(DST), ensure_ascii=False)[:160])
rendered = jypack_render.render(str(JYPACK), str(OUT), draft_dir=str(DST))
print("RENDER:", json.dumps({key: rendered[key] for key in
                             ("output", "output_size", "video_duration")}, ensure_ascii=False))
