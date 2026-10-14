"""探测官方检索接口对"歌词动效"（lyric_animation）类模板的支持情况。"""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "engine"))
import draftediting_runtime as dr  # noqa: E402

WS = Path(os.environ["LOCALAPPDATA"]) / "Temp" / "jianying-draftediting" / "lyric-probe"
if not WS.exists() or not any(WS.iterdir()):
    dr.blueprint_init(WS)

TYPES = ["lyric_animation", "lyrics_effect", "lyric_effect", "lyric", "lyrics", "text_effect"]
KEYWORDS = ["浪漫氛围", "月光下", "每个梦想"]

for kind in TYPES:
    payload = {"mode": "knowledge_then_vimo", "search": [{"type": kind, "keyword": KEYWORDS[0]}]}
    try:
        result = dr.run_lyra(["draft", "blueprint", "resource", "--workspace", str(WS),
                              "--search", json.dumps(payload, ensure_ascii=False)], WS, 180, [WS])
    except Exception as error:  # noqa: BLE001
        print(f"[{kind}] 失败: {str(error)[:220]}")
        continue
    body = result["result"].get("result") or {}
    assets = body.get("assets") or []
    errors = body.get("errors")
    print(f"[{kind}] assets={len(assets)} errors={json.dumps(errors, ensure_ascii=False)[:200]}")
    for asset in assets[:4]:
        metadata = asset.get("metadata") or {}
        print(f"    {asset.get('asset_id')} | {asset.get('resource_id')} | {asset.get('title')}"
              f" | slots={metadata.get('text_template_slot_count')}"
              f" | err={metadata.get('text_template_slots_error')}")

print()
print("== 用模板名当关键词，看能否搜到具体歌词动效模板 ==")
for keyword in KEYWORDS:
    payload = {"mode": "knowledge_then_vimo", "search": [{"type": "subtitle_template", "keyword": keyword}]}
    try:
        result = dr.run_lyra(["draft", "blueprint", "resource", "--workspace", str(WS),
                              "--search", json.dumps(payload, ensure_ascii=False)], WS, 180, [WS])
        assets = (result["result"].get("result") or {}).get("assets") or []
    except Exception as error:  # noqa: BLE001
        print(f"[{keyword}] 失败: {str(error)[:160]}")
        continue
    titles = [(asset.get("title"), (asset.get("metadata") or {}).get("text_template_slot_count"),
               (asset.get("metadata") or {}).get("text_template_slots_error")) for asset in assets]
    print(f"[{keyword}] {json.dumps(titles, ensure_ascii=False)[:500]}")
