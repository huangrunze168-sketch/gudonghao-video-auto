"""把在线下载的歌词模板同步到官方套用时会查找的缓存位置。

`material download` 落到 `Cache/artistEffect/<id>/<hash>/`，
而 `draft lyrics animation update` 读的是
`Cache/lyra-cli/material-cache/lyric_animation/<id>/<id>/<hash>/`。
两处落点不同，不补这一步就会报 `failed to read LyricStyle.json`。
"""
import json
import os
import shutil
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
ROOT = Path.cwd()
base = Path(os.environ['LOCALAPPDATA']) / 'JianyingPro/User Data/Cache'
src_root = base / 'artistEffect'
dst_root = base / 'lyra-cli' / 'material-cache' / 'lyric_animation'

candidates = json.loads((ROOT / 'work/guzhu-mingyun-v2/online-lyric-candidates.json')
                        .read_text(encoding='utf-8'))
copied = skipped = 0
for rid in candidates:
    src = src_root / rid
    if not src.is_dir():
        continue
    dst = dst_root / rid / rid
    if dst.is_dir() and next(dst.rglob('LyricStyle.json'), None):
        skipped += 1
        continue
    shutil.copytree(src, dst, dirs_exist_ok=True)
    copied += 1
print('同步 %d 个模板到官方歌词缓存位置（已存在 %d 个）' % (copied, skipped))
