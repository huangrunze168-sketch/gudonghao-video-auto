"""检索一批可用的官方歌词/字幕模板，供选择替换。"""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "engine"))
import draftediting_runtime as dr  # noqa: E402

WS = Path(os.environ["LOCALAPPDATA"]) / "Temp" / "jianying-draftediting" / "catalog-probe"
if not WS.exists() or not any(WS.iterdir()):
    dr.blueprint_init(WS)

KEYWORDS = ["歌词", "歌词动效", "卡拉OK", "字幕", "手写字幕", "发光字幕", "歌词字幕"]
seen = {}
for keyword in KEYWORDS:
    payload = {"mode": "knowledge_then_vimo",
               "search": [{"type": "subtitle_template", "keyword": keyword}]}
    try:
        result = dr.run_lyra(["draft", "blueprint", "resource", "--workspace", str(WS),
                              "--search", json.dumps(payload, ensure_ascii=False)], WS, 180, [WS])
        assets = (result["result"].get("result") or {}).get("assets") or []
    except Exception as error:  # noqa: BLE001
        print(f"[{keyword}] 失败: {str(error)[:160]}")
        continue
    for asset in assets:
        metadata = asset.get("metadata") or {}
        if asset.get("resource_id") and metadata.get("text_template_slots"):
            seen.setdefault(asset["resource_id"], {
                "title": asset.get("title"), "asset_id": asset.get("asset_id"),
                "resource_id": asset["resource_id"],
                "cover": metadata.get("cover_url"),
                "keywords": []})
            seen[asset["resource_id"]]["keywords"].append(keyword)

print(json.dumps(list(seen.values()), ensure_ascii=False, indent=2))
