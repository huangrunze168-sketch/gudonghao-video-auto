"""枚举本机剪映缓存的贴图（infoSticker）资源及其名称。"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path.home() / "AppData/Local/JianyingPro/User Data/Cache/artistEffect"
rows = []
for res in sorted(ROOT.iterdir()):
    if not res.is_dir():
        continue
    images = list(res.rglob("singleImage.png"))
    lua = list(res.rglob("infoSticker.lua"))
    if not images and not lua:
        continue
    item = {"id": res.name, "name": None, "image": str(images[0]) if images else None,
            "has_lua": bool(lua)}
    for info in res.rglob("heycanInfo.json"):
        try:
            data = json.loads(info.read_text(encoding="utf-8", errors="replace"))
            item["heycan"] = data
        except Exception:  # noqa: BLE001
            pass
    for cfg in res.rglob("config.json"):
        try:
            item["config"] = json.loads(cfg.read_text(encoding="utf-8", errors="replace"))
        except Exception:  # noqa: BLE001
            pass
    rows.append(item)

print("贴图资源数:", len(rows))
for item in rows[:6]:
    print("\nid=%s" % item["id"])
    print("  heycanInfo:", json.dumps(item.get("heycan"), ensure_ascii=False)[:200])
    print("  config    :", json.dumps(item.get("config"), ensure_ascii=False)[:200])

print("\n== 是否有名称字段 ==")
with_name = [r for r in rows if (r.get("heycan") or {}).get("name") or (r.get("config") or {}).get("name")]
print("含 name 的资源数:", len(with_name))

Path(r"C:\Users\Administrator\Documents\剪映\work\guzhu-test\sticker-resources.json").write_text(
    json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
print("已写出 sticker-resources.json")
