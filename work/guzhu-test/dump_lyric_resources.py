"""枚举本机剪映的歌词动效资源，导出可用于匹配的元数据。"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path.home() / "AppData/Local/JianyingPro/User Data/Cache/artistEffect"
rows = []
for res in sorted(ROOT.iterdir()):
    if not res.is_dir():
        continue
    styles = list(res.rglob("LyricStyle.json"))
    if not styles:
        continue
    item = {"id": res.name, "title": None, "track_type": None,
            "fonts": [], "config": None, "paths": [str(p.parent) for p in styles]}
    try:
        style = json.loads(styles[0].read_text(encoding="utf-8", errors="replace"))
        item["title"] = style.get("title")
        item["track_type"] = style.get("text_track_type")
        item["platform"] = style.get("platform")
        style_text = style.get("text_style") or {}
        item["single_word"] = style_text.get("enable_single_word")
        item["random_color"] = style_text.get("text_color_random")
    except Exception as error:  # noqa: BLE001
        item["error"] = str(error)[:60]
    for font in res.rglob("*.ttf"):
        item["fonts"].append(font.name)
    for font in res.rglob("*.TTF"):
        item["fonts"].append(font.name)
    for cfg in res.rglob("config.json"):
        try:
            item["config"] = json.loads(cfg.read_text(encoding="utf-8", errors="replace"))
        except Exception:  # noqa: BLE001
            pass
    rows.append(item)

print("歌词资源总数:", len(rows))
lyrics = [item for item in rows if item.get("track_type") == "lyrics"]
print("其中 text_track_type=lyrics:", len(lyrics), " 其他:", len(rows) - len(lyrics))
print()
for item in rows:
    print("id=%-20s title=%-22s type=%-8s single_word=%s fonts=%s"
          % (item["id"], item["title"], item["track_type"],
             item.get("single_word"), ",".join(item["fonts"])[:60] or "-"))
    if item.get("config"):
        print("      config:", json.dumps(item["config"], ensure_ascii=False)[:150])

Path(r"C:\Users\Administrator\Documents\剪映\work\guzhu-test\lyric-resources.json").write_text(
    json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
print("\n已写出 lyric-resources.json")
