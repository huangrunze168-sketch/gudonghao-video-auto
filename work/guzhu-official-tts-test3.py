# -*- coding: utf-8 -*-
"""验证 --replace 是否真正替换目标段的语音，以及替换后时长如何变化。"""
import json
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\Administrator\Documents\剪映")
sys.path.insert(0, str(ROOT / "engine"))
import lyra_cli  # noqa: E402
import windows_runtime  # noqa: E402

WS = Path(r"C:\Temp\guzhu-ws")
DRAFT_ROOT = Path(windows_runtime.DRAFT_ROOT).resolve()
DRAFT = DRAFT_ROOT / "guzhu-official-test"
REF = "local://guzhu-official-test"

id_map = json.loads((WS / "id_map.json").read_text(encoding="utf-8"))
segs = {item["xml_id"]: item["seg_id"] for item in id_map}

before = None
timeline_path = next(DRAFT.glob("Timelines/*/draft_content.json"))
before = windows_runtime._decrypt_metadata_in_memory(timeline_path)


def tts_segment_rows(timeline):
    rows = {}
    for track in timeline["tracks"]:
        if track.get("type") != "text":
            continue
        for segment in track.get("segments") or []:
            node = next((n for n in timeline["materials"].get("texts", [])
                         if n.get("id") == segment.get("material_id")), None)
            if not node or node.get("type") != "subtitle":
                continue
            try:
                text = json.loads(node["content"])["text"]
            except Exception:  # noqa: BLE001
                continue
            value = segment.get("target_timerange") or {}
            rows[text] = (value.get("start") or 0, value.get("duration") or 0)
    return rows


print("替换前:", json.dumps(tts_segment_rows(before), ensure_ascii=False))

print("\n===== t2 + --replace true =====")
try:
    result = lyra_cli.draft(
        ["algo", "tts"], str(DRAFT_ROOT), REF,
        {"--seg-id": segs["t2"], "--text": "这句话被官方音色替换了",
         "--speaker": "ICL_zh_female_xinmanbo", "--write-to-draft": "true",
         "--replace": "true"},
        timeout=900)
    print("成功:", json.dumps(result, ensure_ascii=False)[:600])
except Exception as error:  # noqa: BLE001
    print("失败:", str(error)[:400])

after = windows_runtime._decrypt_metadata_in_memory(next(DRAFT.glob("Timelines/*/draft_content.json")))
print("\n替换后:", json.dumps(tts_segment_rows(after), ensure_ascii=False))
print("duration:", before.get("duration"), "->", after.get("duration"))
