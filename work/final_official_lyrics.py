"""官方歌词链路（最终版）：识别 → 每句精确套用一次"浪漫氛围" → 渲染。

要点：应用动效会把整句歌词展开成逐词多段，所以待处理段必须按"整句文本"匹配，
否则展开出的词段会被反复套用，导致动效层层叠加。
"""
import json
import os
import re
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
NAME = "headless-final-lyrics"
DST = DRAFT_ROOT / NAME
JYPACK = Path(r"C:\Users\Administrator\Desktop\剪映测试\测试.jypack")
OUT = ROOT / "work" / "run-final-lyrics"
WS = Path(os.environ["LOCALAPPDATA"]) / "Temp" / "jianying-draftediting" / "ws-final"
RESOURCE = "vimo://7591420714515844395"  # 浪漫氛围
ref = dr.local_ref(NAME)


def segment_texts():
    """返回 canonical XML 里 (xml_id, 文本, 是否已有 template) 列表。"""
    dr.blueprint_sync(WS, ref, DRAFT_ROOT)
    id_map = {item["xml_id"]: item["seg_id"]
              for item in json.loads((WS / "id_map.json").read_text(encoding="utf-8"))}
    text = (WS / "current_draft.xml").read_text(encoding="utf-8", errors="replace")
    rows, current, has_template, body = [], None, False, ""
    for line in text.splitlines():
        stripped = line.strip()
        opened = re.match(r'<(?:text|subtitle) id="(t\d+)"', stripped)
        if opened:
            current, has_template, body = opened.group(1), False, ""
            continue
        if current:
            if stripped.startswith("<template"):
                has_template = True
            match = re.search(r'text="([^"]*)"', stripped)
            if match and "<sub " in stripped:
                body = match.group(1)
            if "</text>" in stripped or "</subtitle>" in stripped:
                rows.append((current, body, has_template))
                current = None
    if current:
        rows.append((current, body, has_template))
    return [(xml_id, body, has_template, id_map.get(xml_id)) for xml_id, body, has_template in rows]


if not DST.exists():
    shutil.copytree(SRC, DST)
if not WS.exists() or not any(WS.iterdir()):
    dr.blueprint_init(WS)
dr.blueprint_sync(WS, ref, DRAFT_ROOT)
print("ref:", ref)

# 1. 官方歌词识别
result = dr.run_lyra(["draft", "lyrics", "recognize", "--ref", ref, "--language", "zh"],
                     DRAFT_ROOT, 1800, [WS, DST])
payload = result["result"]["result"]
lyrics = []
for segment in payload.get("affected_segments", []):
    for sentence in (segment.get("asr") or {}).get("sentences", []):
        lyrics.append(sentence["text"])
print("识别歌词句数:", len(lyrics))
for index, line in enumerate(lyrics, 1):
    print(f"  {index:2d}. {line}")

# 2. 每句精确套用一次
done = set()
for _ in range(len(lyrics) + 4):
    rows = segment_texts()
    target = None
    for xml_id, body, has_template, seg_id in rows:
        if has_template or not seg_id or body not in lyrics or body in done:
            continue
        target = (body, seg_id)
        break
    if target is None:
        break
    body, seg_id = target
    try:
        dr.run_lyra(["draft", "lyrics", "animation", "update", "--ref", ref,
                     "--seg-id", seg_id, "--resource", RESOURCE, "--language", "zh-CN"],
                    DRAFT_ROOT, 600, [WS, DST])
        done.add(body)
        print(f"  已套用（{len(done)}/{len(lyrics)}）: {body}")
    except Exception as error:  # noqa: BLE001
        print(f"  套用失败 {body}: {str(error)[:200]}")
        done.add(body)

print(f"共套用 {len(done)}/{len(lyrics)} 句")
print("mirrors:", json.dumps(hp.sync_draft_mirrors(DST), ensure_ascii=False)[:160])
rendered = jypack_render.render(str(JYPACK), str(OUT), draft_dir=str(DST))
print("RENDER:", json.dumps({key: rendered[key] for key in
                             ("output", "output_size", "video_duration")}, ensure_ascii=False))
