# -*- coding: utf-8 -*-
"""实测官方 TTS 的 --seg-id 目标：TTS 音频段（a*）还是字幕段（t*）。"""
import json
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\Administrator\Documents\剪映")
sys.path.insert(0, str(ROOT / "engine"))
import lyra_cli  # noqa: E402
import windows_runtime  # noqa: E402

WS = Path(r"C:\Temp\guzhu-ws")
DRAFT_ROOT = Path(windows_runtime.DRAFT_ROOT).resolve()
REF = "local://guzhu-official-test"

id_map = json.loads((WS / "id_map.json").read_text(encoding="utf-8"))
segs = {item["xml_id"]: item["seg_id"] for item in id_map}
print("id_map:", json.dumps(segs, ensure_ascii=False))

TEXT = "家人们别划走，官方音色测试"
for xml_id in ("a1", "t1"):
    print("\n===== --seg-id 用 %s (%s) =====" % (xml_id, segs.get(xml_id)))
    try:
        result = lyra_cli.draft(
            ["algo", "tts"], str(DRAFT_ROOT), REF,
            {"--seg-id": segs[xml_id], "--text": TEXT,
             "--speaker": "ICL_zh_female_xinmanbo", "--write-to-draft": "true"},
            timeout=900)
        print("成功:", json.dumps(result, ensure_ascii=False)[:900])
    except Exception as error:  # noqa: BLE001 - 探测参数组合
        print("失败:", str(error)[:400])
