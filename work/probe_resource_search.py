"""探测官方 blueprint resource --search 是否能联网检索模板资源。"""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "engine"))
import draftediting_runtime as dr  # noqa: E402

WS = Path(os.environ["LOCALAPPDATA"]) / "Temp" / "jianying-draftediting" / "resource-probe"

if not WS.exists() or not any(WS.iterdir()):
    print("初始化工作区 ...")
    dr.blueprint_init(WS)

RID = "7591420714515844395"
CASES = [
    {"mode": "knowledge_then_vimo", "search": [{"type": "subtitle_template", "keyword": "浪漫氛围"}]},
    {"mode": "knowledge_then_vimo", "search": [{"type": "template", "keyword": "浪漫氛围"}]},
    {"mode": "knowledge_then_vimo", "search": [{"type": "text_template", "keyword": "浪漫氛围"}]},
    {"mode": "knowledge_then_vimo", "search": [{"type": "subtitle_template", "resource_id": RID}]},
    {"mode": "knowledge_then_vimo", "search": [{"type": "template", "resource_id": RID}]},
]

for payload in CASES:
    print("=" * 20, json.dumps(payload, ensure_ascii=False))
    try:
        result = dr.run_lyra(["draft", "blueprint", "resource", "--workspace", str(WS),
                              "--search", json.dumps(payload, ensure_ascii=False)],
                             WS, 120, [WS])
        print(json.dumps(result["result"], ensure_ascii=False)[:1200])
    except Exception as error:  # noqa: BLE001 - 探测脚本需要看到每种失败
        print("FAIL:", str(error)[:900])
