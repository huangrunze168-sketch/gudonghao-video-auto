"""把字体缓存里的 md5 子目录改成真实 md5（取自 .locks/<md5>.lock）。"""
import json
import os
import shutil
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
FONTDIR = (Path(os.environ['LOCALAPPDATA']) / 'JianyingPro/User Data/Cache'
           / 'lyra-cli' / 'material-cache' / 'font')
FONT_SUFFIX = ('.ttf', '.otf', '.ttc')
PLACEHOLDER = 'local0000000000000000000000000000'

fixed = []
for folder in sorted(FONTDIR.iterdir()):
    if not folder.is_dir():
        continue
    # 真实 md5：优先取 .locks 里的 lock 文件名
    real = None
    locks = folder / '.locks'
    if locks.is_dir():
        for f in locks.iterdir():
            if f.suffix == '.lock' and len(f.stem) == 32:
                real = f.stem
                break
    if real is None:
        for item in folder.iterdir():
            if item.is_dir() and len(item.name) == 32 and item.name != PLACEHOLDER:
                real = item.name
                break
    if real is None:
        continue
    # 把占位符目录 / 其它 32 位目录统一成 real
    for item in list(folder.iterdir()):
        if not item.is_dir() or item.name == '.locks':
            continue
        if item.name == real:
            continue
        target = folder / real
        target.mkdir(parents=True, exist_ok=True)
        for child in item.iterdir():
            dest = target / child.name
            if dest.exists():
                dest.unlink()
            shutil.move(str(child), str(dest))
        try:
            item.rmdir()
        except OSError:
            shutil.rmtree(item, ignore_errors=True)
        fixed.append({'font_id': folder.name, 'from': item.name, 'to': real})
        print('%-20s %s -> %s' % (folder.name, item.name[:12], real[:12]))

print()
print('修正 md5 目录 %d 个' % len(fixed))

# 复核：每个字体的 md5 目录里是否有真字体
bad = []
for folder in sorted(FONTDIR.iterdir()):
    if not folder.is_dir():
        continue
    if (folder / 'font.lock').exists():
        bad.append((folder.name, 'font.lock 残留'))
        continue
    subs = [d for d in folder.iterdir() if d.is_dir() and d.name != '.locks']
    if not subs:
        bad.append((folder.name, '无 md5 目录'))
        continue
    ok = any(f.is_file() and f.suffix.lower() in FONT_SUFFIX and f.stat().st_size > 1024
             for s in subs for f in s.iterdir())
    if not ok:
        bad.append((folder.name, 'md5 目录内无字体'))
print('结构异常字体 %d 个: %s' % (len(bad), bad[:8]))
Path('work/guzhu-templates/font-md5-fix.json').write_text(
    json.dumps({'fixed': fixed, 'bad': bad}, ensure_ascii=False, indent=2), encoding='utf-8')
