"""用 template_id 精确检索歌词模板，并查看资源元数据里的可下载地址。"""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "engine"))
import draftediting_runtime as dr  # noqa: E402

WS = Path(os.environ["LOCALAPPDATA"]) / "Temp" / "jianying-draftediting" / "resource-probe"
RID = "7591420714515844395"

CASES = [
    {"type": "subtitle_template", "template_id": RID},
    {"type": "subtitle_template", "resource_id": RID, "keyword": "浪漫氛围"},
]

for case in CASES:
    payload = {"mode": "knowledge_then_vimo", "search": [case]}
    print("=" * 24, json.dumps(case, ensure_ascii=False))
    try:
        result = dr.run_lyra(["draft", "blueprint", "resource", "--workspace", str(WS),
                              "--search", json.dumps(payload, ensure_ascii=False)],
                             WS, 120, [WS])
        data = result["result"]["result"]
    except Exception as error:  # noqa: BLE001
        print("FAIL:", str(error)[:600])
        continue
    assets = data.get("assets") or []
    print("assets:", len(assets), "| errors:", json.dumps(data.get("errors"), ensure_ascii=False)[:300])
    for asset in assets[:2]:
        print("  asset_id:", asset.get("asset_id"))
        print("  lyra_resource:", asset.get("lyra_resource"))
        print("  resource_id:", asset.get("resource_id"))
        print("  title:", asset.get("title"))
        print("  url-like keys:", [k for k, v in asset.items() if isinstance(v, str) and v.startswith("http")])
        metadata = asset.get("metadata") or {}
        print("  metadata keys:", sorted(metadata))
        for key, value in metadata.items():
            text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
            if isinstance(text, str) and (text.startswith("http") or "url" in key.lower()
                                          or "path" in key.lower() or key.startswith("text_template")):
                print(f"    {key}: {text[:400]}")
    print()
