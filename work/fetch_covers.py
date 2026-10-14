"""下载候选模板封面（首帧转 PNG），供人工挑选。"""
import json
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "work" / "template-covers"

COVERS = [
    ("subtitle_template1", "歌词-梦幻发光上滑字幕",
     "https://p3-heycan-jy-sign.byteimg.com/tos-cn-i-3jr8j4ixpe/d72afd7ccd3d4fc586198b5d92ea1b41~tplv-3jr8j4ixpe-resize:200:200.gif?x-expires=1823095135&x-signature=7KVsWg38aoln4ffRgFp0iKyBCoc%3D"),
    ("subtitle_template2", "歌词-荧光晃动逐字渐显",
     "https://p3-heycan-jy-sign.byteimg.com/tos-cn-i-3jr8j4ixpe/12c82b79ea814b208aba5bab59609e8a~tplv-3jr8j4ixpe-resize:200:200.gif?x-expires=1823095139&x-signature=WufCEvo48BBcqcT6%2Fo4nQX5ts6c%3D"),
    ("subtitle_template3", "卡拉OK-蓝色",
     "https://p3-heycan-jy-sign.byteimg.com/tos-cn-i-3jr8j4ixpe/f26a96df75d9479b836581cc0487afce~tplv-3jr8j4ixpe-resize:200:200.gif?x-expires=1823095144&x-signature=skTKQzYnEf7wxvOoK8c2VAmLIzA%3D"),
    ("subtitle_template4", "网感字幕-复古描边字幕",
     "https://p3-heycan-jy-sign.byteimg.com/tos-cn-i-3jr8j4ixpe/deb5608e08ea49838bc44bbfcea81603~tplv-3jr8j4ixpe-resize:200:200.gif?x-expires=1823095149&x-signature=0Orj38R5tDrVxScuzbL3E24W1Xk%3D"),
    ("subtitle_template5", "AI字幕-小清新手写体",
     "https://p3-heycan-jy-sign.byteimg.com/tos-cn-i-3jr8j4ixpe/a4a03cf50b9647d197fc5cc26fc3ce0e~tplv-3jr8j4ixpe-resize:200:200.gif?x-expires=1823095153&x-signature=4dcjxaSrUfc9EudwL70GuvRyTpo%3D"),
]

OUT.mkdir(parents=True, exist_ok=True)
report = []
for asset_id, title, url in COVERS:
    gif = OUT / f"{asset_id}.gif"
    png = OUT / f"{asset_id}.png"
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        gif.write_bytes(urllib.request.urlopen(request, timeout=40).read())
    except Exception as error:  # noqa: BLE001
        report.append({"asset_id": asset_id, "title": title, "error": str(error)[:200]})
        continue
    completed = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(gif), "-frames:v", "1",
                                "-vf", "scale=360:-1:flags=lanczos", str(png)],
                               capture_output=True, text=True, encoding="utf-8", errors="replace")
    report.append({"asset_id": asset_id, "title": title, "gif": str(gif),
                   "png": str(png) if png.is_file() else None,
                   "error": completed.stderr[:200] if completed.returncode else None})

print(json.dumps(report, ensure_ascii=False, indent=2))
