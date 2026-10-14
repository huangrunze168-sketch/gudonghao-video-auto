"""用真实 md5 重建字体子目录，并清掉此前脚本造的 local000... 假目录。

官方的结构（GUI 正常下载才是这样）：
    font/<id>/font.ttf
    font/<id>/.locks/<md5>.lock
    font/<id>/<md5>/<原文件名>.ttf
    font/<id>/<md5>/config.json      # 紧凑格式，109 字节

剪映按 <md5>/ 目录解析字体；此前用占位目录名 local000... 所以仍然回退默认字体。
"""
import json
import os
import shutil
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
FONTDIR = (Path(os.environ['LOCALAPPDATA']) / 'JianyingPro/User Data/Cache'
           / 'lyra-cli' / 'material-cache' / 'font')
FONT_SUFFIX = ('.ttf', '.otf', '.ttc')
PLACEHOLDER = 'local' + '0' * 32
COMPACT_CONFIG = '{"effect":{"Link":[{"type":"InfoSticker"}]},"version":"3.1.1"}'

renamed = 0
dropped = 0
skipped = 0
for folder in sorted(FONTDIR.iterdir()):
    if not folder.is_dir():
        continue
    # 真实 md5：取 .locks 里的 lock 文件名
    md5 = None
    locks = folder / '.locks'
    if locks.is_dir():
        for f in sorted(locks.iterdir()):
            if f.is_file() and f.name.endswith('.lock') and len(f.stem) == 32:
                md5 = f.stem
                break
    subs = [d for d in folder.iterdir() if d.is_dir() and d.name != '.locks']
    if md5 is None:
        skipped += 1
        continue
    real_dir = folder / md5
    for item in subs:
        if item.name == md5:
            continue
        if real_dir.exists():
            # 已经有真实 md5 目录（官方结构），假的直接删
            shutil.rmtree(item, ignore_errors=True)
            dropped += 1
            print('%-20s 删除假目录 %s' % (folder.name, item.name[:16]))
        else:
            item.rename(real_dir)
            renamed += 1
            print('%-20s %s -> 真实 md5 %s' % (folder.name, item.name[:16], md5[:16]))
    # 保证真实目录里有字体与 config.json
    fonts = [f for f in folder.iterdir()
             if f.is_file() and f.suffix.lower() in FONT_SUFFIX and f.stat().st_size > 1024]
    if not fonts:
        continue
    primary = max(fonts, key=lambda f: f.stat().st_size)
    real_dir.mkdir(parents=True, exist_ok=True)
    inner = real_dir / primary.name
    if not inner.is_file():
        shutil.copyfile(primary, inner)
    cfg = real_dir / 'config.json'
    cfg.write_text(COMPACT_CONFIG, encoding='utf-8')

print()
print('重命名为真实 md5 %d 个，删除假目录 %d 个，无 md5 可依据 %d 个' % (renamed, dropped, skipped))

# 复核结构
ok = bad = 0
examples = []
for folder in sorted(FONTDIR.iterdir()):
    if not folder.is_dir():
        continue
    fonts = [f for f in folder.iterdir()
             if f.is_file() and f.suffix.lower() in FONT_SUFFIX and f.stat().st_size > 1024]
    if not fonts:
        continue
    subs = [d for d in folder.iterdir() if d.is_dir() and d.name != '.locks']
    good = False
    for s in subs:
        if len(s.name) == 32 and any(f.is_file() and f.suffix.lower() in FONT_SUFFIX
                                     and f.stat().st_size > 1024 for f in s.iterdir()):
            good = True
    if good:
        ok += 1
    else:
        bad += 1
        if len(examples) < 6:
            examples.append((folder.name, [s.name[:12] for s in subs]))
print('结构正确 %d 个，仍不正确 %d 个' % (ok, bad))
if examples:
    print('异常示例: %s' % examples)
