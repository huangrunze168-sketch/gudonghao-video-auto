"""补下字体审计中标记为不可用的字体，并复核下载结果。"""
import json
import os
import sys
from pathlib import Path

ROOT = Path.cwd()
sys.path[:0] = [str(ROOT / 'skills/guzhu-hao/scripts'), str(ROOT / 'engine')]
from official_materials import execute

os.environ['DSH_LYRA_ALLOW_NETWORK'] = '1'

OUT = ROOT / 'work/guzhu-templates'
audit = json.loads((OUT / 'font-audit.json').read_text(encoding='utf-8'))
FONTDIR = (Path(os.environ['LOCALAPPDATA']) / 'JianyingPro/User Data/Cache'
           / 'lyra-cli' / 'material-cache' / 'font')

bad = sorted([fid for fid, v in audit['fonts'].items() if v.get('state') != 'ok'])
print('待补字体 %d 个' % len(bad))

results = {}
report_path = OUT / 'font-download.json'
if report_path.is_file():
    try:
        results = json.loads(report_path.read_text(encoding='utf-8'))
    except ValueError:
        results = {}


def state_of(font_id):
    folder = FONTDIR / str(font_id)
    if not folder.is_dir():
        return 'missing-dir', 0
    files = [f for f in folder.rglob('*')
             if f.is_file() and f.suffix.lower() in ('.ttf', '.otf', '.ttc')
             and f.stat().st_size > 1024]
    return ('ok', max(f.stat().st_size for f in files)) if files else ('lock-only', 0)


ok = 0
for pos, fid in enumerate(bad, 1):
    before, _size = state_of(fid)
    if before == 'ok':
        results[fid] = {'status': 'already-ok'}
        ok += 1
        continue
    if results.get(fid, {}).get('status') == 'downloaded':
        ok += 1
        continue
    try:
        r = execute(ROOT, ['material', 'download', '--type', 'font', '--resource-id', fid])
        after, size = state_of(fid)
        status = 'downloaded' if after == 'ok' else ('failed-still-%s' % after)
        results[fid] = {'status': status, 'size': size,
                        'cli': r.get('status'),
                        'error': str(r.get('error') or '')[:120]}
        print('[%d/%d] %-20s %s%s' % (pos, len(bad), fid, status,
                                      (' %d bytes' % size) if size else ''), flush=True)
        if after == 'ok':
            ok += 1
    except Exception as error:  # noqa: BLE001
        results[fid] = {'status': 'exception', 'error': str(error)[:150]}
        print('[%d/%d] %-20s 异常' % (pos, len(bad), fid), flush=True)
    report_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')

print()
print('补下完成：可用 %d / %d' % (ok, len(bad)))
still = [fid for fid in bad if state_of(fid)[0] != 'ok']
print('仍不可用 %d 个: %s' % (len(still), still[:12]))

# 按字体重新统计受影响的模板
templates = audit['templates']
fixed = partial = broken = 0
for rid, row in templates.items():
    ids = row.get('fonts') or []
    if not ids:
        continue
    states = [state_of(fid)[0] for fid in ids]
    if all(s == 'ok' for s in states):
        fixed += 1
    elif any(s == 'ok' for s in states):
        partial += 1
    else:
        broken += 1
print()
print('补下后模板字体状态：齐全 %d，部分 %d，全缺 %d' % (fixed, partial, broken))
(OUT / 'font-audit-after.json').write_text(
    json.dumps({'fixed': fixed, 'partial': partial, 'broken': broken,
                'still_missing': still}, ensure_ascii=False, indent=2), encoding='utf-8')
