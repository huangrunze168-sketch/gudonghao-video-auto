# -*- coding: utf-8 -*-
"""验证：对官方识别出的 <text> 段套用官方歌词动效模板，资源是否落地。"""
import json
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\Administrator\Documents\剪映")
sys.path.insert(0, str(ROOT / "engine"))

import lyra_cli  # noqa: E402
import windows_runtime  # noqa: E402

DR = Path(windows_runtime.DRAFT_ROOT).resolve()
NAME = "guzhu-lyric-text"
WS = Path(r"C:\Temp\lyric-ws2")
CACHE = Path(r"C:\Users\Administrator\AppData\Local\JianyingPro\User Data\Cache\artistEffect")

segs = {item["xml_id"]: item["seg_id"]
        for item in json.loads((WS / "id_map.json").read_text(encoding="utf-8"))}
target = segs.get("t16")
print("目标歌词段 t16 =", target)


def state(resource_id):
    folder = CACHE / resource_id
    if not folder.is_dir():
        return "无缓存"
    hits = list(folder.rglob("content.json"))
    return "content.json x%d" % len(hits) if hits else "无 content.json"


for resource_id in ("7638543120313142553", "7418206434447363340", "7485655034164989209"):
    print("调用前 %s : %s" % (resource_id, state(resource_id)))

for resource_id in ("7638543120313142553", "7418206434447363340"):
    print("\n===== lyrics animation update  vimo://%s =====" % resource_id)
    try:
        result = lyra_cli.lyrics_animation_update(
            str(DR), "local://" + NAME, target, "vimo://" + resource_id, timeout=900)
        print("成功:", json.dumps(result, ensure_ascii=False)[:500])
        print("缓存:", state(resource_id))
        break
    except Exception as error:  # noqa: BLE001 - 依次探测可用模板
        print("失败:", str(error)[:400])
        print("缓存:", state(resource_id))
