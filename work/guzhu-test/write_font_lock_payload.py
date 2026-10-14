"""把真实字体内容写进 font.lock —— 渲染器就是从 font.path (=font.lock) 读字体。

证据：删掉 0 字节的 font.lock 后，原生渲染直接报
    "草稿引用的本地资源不存在: .../font/<id>/font.lock"
说明草稿里 font.path 指向 font.lock，渲染器按该路径读字体文件。
此前 font.lock 是 0 字节（假下载残留），所以静默回退默认字体。
这里把同目录下的真实字体重命名为/复制为 font.lock。
"""
import os
import shutil
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
FONTDIR = (Path(os.environ['LOCALAPPDATA']) / 'JianyingPro/User Data/Cache'
           / 'lyra-cli' / 'material-cache' / 'font')
FONT_SUFFIX = ('.ttf', '.otf', '.ttc')

done = 0
skipped = 0
for folder in sorted(FONTDIR.iterdir()):
    if not folder.is_dir():
        continue
    # 候选字体：排除 font.lock 自身与子目录里的副本
    candidates = [f for f in folder.iterdir()
                  if f.is_file() and f.suffix.lower() in FONT_SUFFIX
                  and f.stat().st_size > 1024]
    if not candidates:
        skipped += 1
        continue
    primary = max(candidates, key=lambda f: f.stat().st_size)
    lock = folder / 'font.lock'
    if lock.is_file() and lock.stat().st_size == primary.stat().st_size:
        done += 1
        continue
    shutil.copyfile(primary, lock)
    done += 1
    print('%-20s font.lock <- %s (%d bytes)' % (folder.name, primary.name,
                                                primary.stat().st_size))

print()
print('写入 font.lock %d 个，无字体可写 %d 个' % (done, skipped))
