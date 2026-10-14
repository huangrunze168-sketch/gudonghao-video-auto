"""定位官方歌词模板缺失的 content.json 应该来自哪里。"""
import io
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "engine"))
import jypack_inspect  # noqa: E402

CACHE = Path(r"C:\Users\Administrator\AppData\Local\JianyingPro\User Data\Cache\artistEffect")
JYPACK = Path(r"C:\Users\Administrator\Desktop\剪映测试\测试.jypack")

print("== artistEffect 模板目录内的文件 ==")
for folder in sorted(CACHE.iterdir())[:12]:
    if not folder.is_dir():
        continue
    for inner in sorted(folder.iterdir()):
        if inner.is_dir():
            names = sorted(p.name for p in inner.iterdir())
            has = "content.json" in names
            print(f"  {folder.name}/{inner.name}: content.json={has} files={names[:8]}")

print()
print("== artistEffect 下所有 content.json ==")
found = list(CACHE.rglob("content.json"))
print("  数量:", len(found))
for path in found[:10]:
    print("  ", path.relative_to(CACHE), path.stat().st_size)

print()
print("== JYPACK 内的候选资源 ==")
try:
    payload = JYPACK.read_bytes()
    decoded, _ = jypack_inspect.decode_container(payload)
    with zipfile.ZipFile(io.BytesIO(decoded)) as archive:
        names = archive.namelist()
    print("  条目总数:", len(names))
    hits = [n for n in names
            if "content.json" in n or "artistEffect" in n or "7591420714515844395" in n
            or "LyricStyle" in n]
    print("  命中:", len(hits))
    for name in hits[:25]:
        print("  ", name)
except Exception as error:  # noqa: BLE001 - 诊断脚本需要看到失败原因
    print("  JYPACK 读取失败:", error)
