"""把本机贴图拼成网格图，便于快速浏览并建立风格标签库。"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

from PIL import Image, ImageDraw  # noqa: E402

ROWS = json.loads(Path(r"C:\Users\Administrator\Documents\剪映\work\guzhu-test\sticker-resources.json")
                  .read_text(encoding="utf-8"))
items = [item for item in ROWS if item.get("image")]
CELL = 200
COLS = 8
PER_PAGE = COLS * 8
OUT = Path(r"C:\Users\Administrator\Documents\剪映\work\guzhu-test")
index = []

for page in range(0, len(items), PER_PAGE):
    chunk = items[page:page + PER_PAGE]
    lines = (len(chunk) + COLS - 1) // COLS
    canvas = Image.new("RGB", (COLS * CELL, lines * CELL), (26, 26, 31))
    draw = ImageDraw.Draw(canvas)
    for i, item in enumerate(chunk):
        number = page + i
        index.append({"no": number, "id": item["id"], "image": item["image"]})
        col, row = i % COLS, i // COLS
        x, y = col * CELL, row * CELL
        try:
            art = Image.open(item["image"]).convert("RGBA")
            art.thumbnail((CELL - 30, CELL - 30))
            canvas.paste(art, (x + 16, y + 16), art)
        except Exception as error:  # noqa: BLE001
            draw.text((x + 12, y + 90), "?", fill=(120, 120, 120))
            index[-1]["error"] = str(error)[:60]
        draw.rectangle([x, y, x + CELL - 1, y + CELL - 1], outline=(70, 70, 80))
        draw.text((x + 6, y + 5), str(number), fill=(255, 96, 96))
    path = OUT / ("sticker-sheet-%d.png" % (page // PER_PAGE + 1))
    canvas.save(path)
    print("已生成", path.name, "共", len(chunk), "格")

(OUT / "sticker-index.json").write_text(
    json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
print("贴图总数:", len(index))
