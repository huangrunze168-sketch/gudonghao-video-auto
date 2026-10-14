"""按客户端的方式下载"浪漫氛围"模板资源包（用户自己的 Pro 订阅资源）。

资源地址来自剪映自己的材料缓存 material_cache.json 的 item_urls 字段，
带签名且未过期；本脚本只做下载与内容检查，不修改任何官方文件。
"""
import io
import json
from pathlib import Path
import urllib.request
import zipfile

MC = Path(r"C:\Users\Administrator\AppData\Local\JianyingPro\User Data\Cache\lyra-cli\material_cache.json")
OUT = Path(__file__).resolve().parent / "template-pack"
RID = "7591420714515844395"

entry = json.loads(MC.read_text(encoding="utf-8"))["items"][RID]
print("== 关键字段 ==")
for key in ("id", "name", "title", "effect_id", "effect_type", "source", "source_platform",
            "text_template_resource_type", "download_info", "path", "filePath", "md5",
            "requirements", "sdk_extra", "is_vip"):
    print(f"  {key}: {json.dumps(entry.get(key), ensure_ascii=False)[:260]}")

urls = entry.get("item_urls") or []
print(f"\n== item_urls ({len(urls)}) ==")
OUT.mkdir(exist_ok=True)
for index, url in enumerate(urls[:4]):
    print(f"[{index}] {url[:170]}")

for index, url in enumerate(urls[:4]):
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(request, timeout=90) as response:
            data = response.read()
    except Exception as error:  # noqa: BLE001
        print(f"[{index}] 下载失败: {str(error)[:200]}")
        continue
    target = OUT / f"pack-{index}.bin"
    target.write_bytes(data)
    print(f"[{index}] {len(data)} 字节 -> {target.name} | ZIP={data[:2] == b'PK'}")
    if data[:2] == b"PK":
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            names = archive.namelist()
        print(f"     条目 {len(names)}: {names[:20]}")
