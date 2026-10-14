"""批量爬取官方歌词/字幕模板，下载封面并拼成对照图。

检索走官方 blueprint resource --search（需要账号权益与网络）；结果按 resource_id 去重，
封面来自官方返回的签名 URL。本脚本只读取与下载预览，不修改官方资源。
"""
import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "engine"))
import draftediting_runtime as dr  # noqa: E402

WS = Path(os.environ["LOCALAPPDATA"]) / "Temp" / "jianying-draftediting" / "catalog"
COVERS = ROOT / "work" / "template-catalog"
KEYWORDS = ["歌词", "卡拉OK", "逐字歌词", "歌词动效", "发光字幕", "手写字幕",
            "字幕", "动感歌词", "双语字幕", "氛围感歌词", "歌词卡点", "跟唱字幕"]

if not WS.exists() or not any(WS.iterdir()):
    dr.blueprint_init(WS)
COVERS.mkdir(parents=True, exist_ok=True)

catalog = {}
for keyword in KEYWORDS:
    payload = {"mode": "knowledge_then_vimo",
               "search": [{"type": "subtitle_template", "keyword": keyword}]}
    try:
        result = dr.run_lyra(["draft", "blueprint", "resource", "--workspace", str(WS),
                              "--search", json.dumps(payload, ensure_ascii=False)], WS, 180, [WS])
        assets = (result["result"].get("result") or {}).get("assets") or []
    except Exception as error:  # noqa: BLE001
        print(f"[{keyword}] 检索失败: {str(error)[:120]}")
        continue
    for asset in assets:
        metadata = asset.get("metadata") or {}
        rid = asset.get("resource_id")
        if not rid or not metadata.get("text_template_slots"):
            continue
        catalog.setdefault(rid, {"resource_id": rid, "title": asset.get("title"),
                                 "asset_id": asset.get("asset_id"),
                                 "cover": metadata.get("cover_url"),
                                 "slots": metadata.get("text_template_slot_count"),
                                 "keywords": []})
        catalog[rid]["keywords"].append(keyword)
        catalog[rid]["asset_id"] = asset.get("asset_id")

items = list(catalog.values())
print(f"去重后可用模板 {len(items)} 个\n")

downloaded = []
for index, item in enumerate(items[:18], 1):
    print(f"{index:2d}. {item['title']} | {item['resource_id']} | 槽位 {item['slots']} | asset {item['asset_id']}")
    if not item.get("cover"):
        continue
    png = COVERS / f"t{index:02d}.png"
    gif = COVERS / f"t{index:02d}.gif"
    try:
        request = urllib.request.Request(item["cover"], headers={"User-Agent": "Mozilla/5.0"})
        gif.write_bytes(urllib.request.urlopen(request, timeout=40).read())
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(gif), "-frames:v", "1",
                        "-vf", "scale=300:-1:flags=lanczos", str(png)],
                       capture_output=True, timeout=60)
        downloaded.append((index, item["title"], png))
    except Exception as error:  # noqa: BLE001
        print(f"    封面下载失败: {str(error)[:120]}")

(ROOT / "work" / "template-catalog.json").write_text(
    json.dumps(items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"\n封面已下载 {len(downloaded)} 张")
print("清单: work/template-catalog.json")
