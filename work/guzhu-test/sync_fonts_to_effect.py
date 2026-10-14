"""把字体同步到剪映渲染实际读取的 Cache/effect/<id>/ 目录。

官方正常下载一个字体时会同时写两处：
  lyra-cli/material-cache/font/<id>/font.ttf
  Cache/effect/<id>/<原文件名>.ttf        <-- 草稿的 font.path 指向这里
绕过 CLI 直接下载时只写了前者，所以渲染仍然回退默认字体。
这里把已有的字体文件补一份到 effect 目录。
"""
import json
import os
import shutil
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
CACHE = Path(os.environ['LOCALAPPDATA']) / 'JianyingPro/User Data/Cache'
FONTDIR = CACHE / 'lyra-cli' / 'material-cache' / 'font'
EFFECT = CACHE / 'effect'
FONT_SUFFIX = ('.ttf', '.otf', '.ttc')

audit = json.loads(Path('work/guzhu-templates/font-audit.json').read_text(encoding='utf-8'))
ids = sorted(audit['fonts'])

copied = 0
skipped = 0
for fid in ids:
    src_dir = FONTDIR / fid
    if not src_dir.is_dir():
        continue
    fonts = [f for f in src_dir.iterdir()
             if f.is_file() and f.suffix.lower() in FONT_SUFFIX and f.stat().st_size > 1024]
    if not fonts:
        continue
    primary = max(fonts, key=lambda f: f.stat().st_size)
    dst_dir = EFFECT / fid
    # effect 目录已经自带字体就不要覆盖
    existing = ([f for f in dst_dir.iterdir()
                 if f.is_file() and f.suffix.lower() in FONT_SUFFIX and f.stat().st_size > 1024]
                if dst_dir.is_dir() else [])
    if existing:
        skipped += 1
        continue
    dst_dir.mkdir(parents=True, exist_ok=True)
    target = dst_dir / primary.name
    if target.exists():
        target.unlink()
    shutil.copyfile(primary, target)
    copied += 1
    print('%-20s -> effect/%s/%s (%d bytes)' % (fid, fid, primary.name,
                                                target.stat().st_size))

print()
print('复制到 effect 目录 %d 个，已有 %d 个' % (copied, skipped))

# 复核：模板的字体是否都能在 effect 目录找到
templates = audit['templates']
ok = partial = broken = 0
missing = []
for _rid, row in templates.items():
    font_ids = row.get('fonts') or []
    if not font_ids:
        continue
    states = []
    for fid in font_ids:
        good = False
        for base in (EFFECT / fid, CACHE / 'artistEffect' / fid):
            if base.is_dir() and any(f.is_file() and f.suffix.lower() in FONT_SUFFIX
                                     and f.stat().st_size > 1024 for f in base.iterdir()):
                good = True
                break
        states.append(good)
        if not good:
            missing.append(fid)
    if all(states):
        ok += 1
    elif any(states):
        partial += 1
    else:
        broken += 1
print('复核（含 effect 目录）：模板字体齐全 %d，部分 %d，全缺 %d' % (ok, partial, broken))
uniq = sorted(set(missing))
print('仍缺字体 %d 个: %s' % (len(uniq), uniq))
Path('work/guzhu-templates/font-effect-sync.json').write_text(
    json.dumps({'copied': copied, 'skipped': skipped, 'ok_templates': ok,
                'partial_templates': partial, 'broken_templates': broken,
                'still_missing': uniq}, ensure_ascii=False, indent=2), encoding='utf-8')
