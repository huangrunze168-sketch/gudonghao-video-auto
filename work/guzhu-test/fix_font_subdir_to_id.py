"""把字体子目录名改成 font_id 本身——这是剪映真正解析字体的位置。

官方结构（实测，GUI 正常下载才有）：
    font/<font_id>/
      font.ttf
      .locks/<资源md5>.lock
      <font_id>/                 <- 子目录名就是 font_id
        <原文件名>.ttf
        config.json              <- 紧凑格式 {"effect":{"Link":[{"type":"InfoSticker"}]},"version":"3.1.1"}

此前脚本用了 local000... 占位目录名，所以剪映按 <font_id>/<font_id>/ 找不到字体，
草稿里的 font.path 又指向 0 字节的 font.lock，结果一直回退默认字体。
"""
import os
import shutil
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
FONTDIR = (Path(os.environ['LOCALAPPDATA']) / 'JianyingPro/User Data/Cache'
           / 'lyra-cli' / 'material-cache' / 'font')
FONT_SUFFIX = ('.ttf', '.otf', '.ttc')
COMPACT_CONFIG = '{"effect":{"Link":[{"type":"InfoSticker"}]},"version":"3.1.1"}'

fixed = 0
cleaned = 0
for folder in sorted(FONTDIR.iterdir()):
    if not folder.is_dir():
        continue
    font_id = folder.name
    real = folder / font_id
    subs = [d for d in folder.iterdir() if d.is_dir() and d.name != '.locks']

    # 把非 font_id 的子目录挪成 font_id
    for item in subs:
        if item.name == font_id:
            continue
        if real.exists():
            shutil.rmtree(item, ignore_errors=True)
            cleaned += 1
        else:
            item.rename(real)
            cleaned += 1

    fonts = [f for f in folder.iterdir()
             if f.is_file() and f.suffix.lower() in FONT_SUFFIX and f.stat().st_size > 1024]
    if not fonts:
        continue
    primary = max(fonts, key=lambda f: f.stat().st_size)
    real.mkdir(parents=True, exist_ok=True)
    inner = real / primary.name
    if not inner.is_file() or inner.stat().st_size != primary.stat().st_size:
        shutil.copyfile(primary, inner)
    (real / 'config.json').write_text(COMPACT_CONFIG, encoding='utf-8')
    fixed += 1

print('整理字体目录 %d 个，移动/清理子目录 %d 次' % (fixed, cleaned))

# 复核：<id>/<id>/ 里必须有字体，且不能残留 local000...
good = bad = 0
issues = []
for folder in sorted(FONTDIR.iterdir()):
    if not folder.is_dir():
        continue
    inner = folder / folder.name
    fonts = ([f for f in inner.iterdir()
              if f.is_file() and f.suffix.lower() in FONT_SUFFIX and f.stat().st_size > 1024]
             if inner.is_dir() else [])
    others = [d.name for d in folder.iterdir()
              if d.is_dir() and d.name not in ('.locks', folder.name)]
    if fonts and not others:
        good += 1
    else:
        bad += 1
        if len(issues) < 6:
            issues.append((folder.name, len(fonts), others[:3]))
print('结构正确 %d 个，仍有问题 %d 个' % (good, bad))
if issues:
    print('异常示例: %s' % issues)

# 抽查关键字体
for fid in ['7340606325656654345', '6740435892441190919']:
    print()
    print('=== %s ===' % fid)
    for f in sorted((FONTDIR / fid).rglob('*')):
        if f.is_file():
            print('  %10d  %s' % (f.stat().st_size, f.relative_to(FONTDIR / fid)))
