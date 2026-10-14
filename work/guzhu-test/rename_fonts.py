"""把直接下载的字体改成剪映期望的文件名（font.ttf / 原扩展名）。

ZIP 包内的中文文件名会因编码问题显示为乱码，剪映按固定名查找字体文件，
因此统一重命名为 font.<原扩展名>；内容已通过官方 md5 校验，不受文件名影响。
"""
import json
import os
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
CACHE = (Path(os.environ['LOCALAPPDATA']) / 'JianyingPro/User Data/Cache'
         / 'lyra-cli' / 'material-cache' / 'font')
FONT_SUFFIX = ('.ttf', '.otf', '.ttc')

audit = json.loads(Path('work/guzhu-templates/font-audit.json').read_text(encoding='utf-8'))
ids = sorted(audit['fonts'])

renamed = 0
kept = 0
for fid in ids:
    folder = CACHE / fid
    if not folder.is_dir():
        continue
    fonts = [f for f in folder.iterdir()
             if f.is_file() and f.suffix.lower() in FONT_SUFFIX and f.stat().st_size > 1024]
    if not fonts:
        continue
    primary = max(fonts, key=lambda f: f.stat().st_size)
    target = folder / ('font' + primary.suffix.lower())
    if primary.name == target.name:
        kept += 1
        continue
    if target.exists():
        target.unlink()
    primary.rename(target)
    renamed += 1
    print('%-20s %s -> %s (%d bytes)' % (fid, primary.name[:34], target.name,
                                         target.stat().st_size))

print()
print('重命名 %d 个，本就规范 %d 个' % (renamed, kept))

# 复核：每个模板的字体是否都有 >1KB 的 font.* 文件
templates = audit['templates']
ok = partial = broken = 0
still = []
for _rid, row in templates.items():
    font_ids = row.get('fonts') or []
    if not font_ids:
        continue
    states = []
    for fid in font_ids:
        folder = CACHE / fid
        good = False
        if folder.is_dir():
            good = any(f.is_file() and f.name.lower().startswith('font')
                       and f.suffix.lower() in FONT_SUFFIX and f.stat().st_size > 1024
                       for f in folder.iterdir())
        states.append(good)
        if not good:
            still.append(fid)
    if all(states):
        ok += 1
    elif any(states):
        partial += 1
    else:
        broken += 1
print('复核：模板字体齐全 %d，部分缺失 %d，全缺 %d' % (ok, partial, broken))
uniq = sorted(set(still))
print('仍缺字体 %d 个（去重）: %s' % (len(uniq), uniq))
Path('work/guzhu-templates/font-rename-report.json').write_text(
    json.dumps({'renamed': renamed, 'kept': kept, 'ok_templates': ok,
                'partial_templates': partial, 'broken_templates': broken,
                'still_missing_fonts': uniq}, ensure_ascii=False, indent=2), encoding='utf-8')
