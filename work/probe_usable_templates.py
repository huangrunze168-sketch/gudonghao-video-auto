"""检索资源完整的官方歌词/字幕模板，作为损坏模板的替换候选。"""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "engine"))
import draftediting_runtime as dr  # noqa: E402

WS = Path(os.environ["LOCALAPPDATA"]) / "Temp" / "jianying-draftediting" / "resource-probe"
KEYWORDS = ["歌词", "中文歌词", "字幕"]

for keyword in KEYWORDS:
    payload = {"mode": "knowledge_then_vimo", "search": [{"type": "subtitle_template", "keyword": keyword}]}
    print("=" * 26, keyword)
    try:
        result = dr.run_lyra(["draft", "blueprint", "resource", "--workspace", str(WS),
                              "--search", json.dumps(payload, ensure_ascii=False)],
                             WS, 180, [WS])
        data = result["result"]["result"]
    except Exception as error:  # noqa: BLE001
        print("FAIL:", str(error)[:400])
        continue
    for asset in (data.get("assets") or [])[:6]:
        metadata = asset.get("metadata") or {}
        slots = metadata.get("text_template_slots")
        error = metadata.get("text_template_slots_error")
        print(f"  {asset.get('asset_id')} | {asset.get('resource_id')} | {asset.get('title')}")
        print(f"      slots={metadata.get('text_template_slot_count')} "
              f"| ok={bool(slots) and not error} | error={error}")
        if slots:
            preview = json.loads(slots) if isinstance(slots, str) else slots
            print(f"      default_text={json.dumps(preview, ensure_ascii=False)[:160]}")
