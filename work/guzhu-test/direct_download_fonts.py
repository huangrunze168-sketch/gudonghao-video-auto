"""用官方 CDN 地址直接下载字体包，用 Python 解压，绕过 CLI 的解压 bug。

官方 CLI 的 `material download --type font` 报：
  upstream -100202 / resource_pool -7002 / download -1008 / cannot unzip file
即服务端返回的字体包在 CLI 侧解压失败（包内中文文件名编码问题）。
字体包本身是好的——用官方 query 拿到的签名 URL 可以直接下载，再用 Python 的
zipfile 解压即可（不依赖 CLI 的解压路径）。这不是本地替代：地址仍来自官方接口。
"""
import hashlib
import io
import json
import os
import sys
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path.cwd()
sys.path[:0] = [str(ROOT / 'skills/guzhu-hao/scripts'), str(ROOT / 'engine')]
from official_materials import execute  # noqa: E402

os.environ['DSH_LYRA_ALLOW_NETWORK'] = '1'

CACHE = Path(os.environ['LOCALAPPDATA']) / 'JianyingPro/User Data/Cache/lyra-cli/material-cache'
FONTDIR = CACHE / 'font'
OUT = ROOT / 'work/guzhu-templates'

audit = json.loads((OUT / 'font-audit.json').read_text(encoding='utf-8'))
bad = sorted([fid for fid, v in audit['fonts'].items() if v.get('state') != 'ok'])
print('待补字体 %d 个' % len(bad))

FONT_SUFFIX = ('.ttf', '.otf', '.ttc')


def state_of(font_id):
    folder = FONTDIR / str(font_id)
    if not folder.is_dir():
        return 'missing-dir', 0
    files = [f for f in folder.rglob('*')
             if f.is_file() and f.suffix.lower() in FONT_SUFFIX and f.stat().st_size > 1024]
    return ('ok', max(f.stat().st_size for f in files)) if files else ('lock-only', 0)


results_path = OUT / 'font-direct-download.json'
results = {}
if results_path.is_file():
    try:
        results = json.loads(results_path.read_text(encoding='utf-8'))
    except ValueError:
        results = {}

ok = fail = 0
for pos, fid in enumerate(bad, 1):
    if state_of(fid)[0] == 'ok':
        ok += 1
        continue
    if results.get(fid, {}).get('status') == 'ok':
        ok += 1
        continue
    try:
        q = execute(ROOT, ['material', 'query', '--type', 'font', '--resource-id', fid])
        body = (((q.get('envelope') or {}).get('result') or {}).get('result') or {})
        items = body.get('items') or []
        if not items:
            results[fid] = {'status': 'query-empty'}
            fail += 1
            print('[%d/%d] %-20s 查询无结果' % (pos, len(bad), fid), flush=True)
            continue
        item = items[0]
        urls = item.get('download_urls') or []
        md5 = str(item.get('md5') or '').lower()
        if not urls:
            results[fid] = {'status': 'no-url'}
            fail += 1
            print('[%d/%d] %-20s 无下载地址' % (pos, len(bad), fid), flush=True)
            continue
        data = urllib.request.urlopen(urls[0], timeout=180).read()
        got = hashlib.md5(data).hexdigest().lower()
        if md5 and got != md5:
            results[fid] = {'status': 'md5-mismatch', 'expected': md5, 'got': got}
            fail += 1
            print('[%d/%d] %-20s MD5 不匹配' % (pos, len(bad), fid), flush=True)
            continue
        archive = zipfile.ZipFile(io.BytesIO(data))
        names = [n for n in archive.namelist() if n.lower().endswith(FONT_SUFFIX)]
        if not names:
            results[fid] = {'status': 'no-font-in-zip',
                            'entries': archive.namelist()[:6]}
            fail += 1
            print('[%d/%d] %-20s 包内无字体文件' % (pos, len(bad), fid), flush=True)
            continue
        target = FONTDIR / fid
        target.mkdir(parents=True, exist_ok=True)
        written = []
        for name in names:
            content = archive.read(name)
            if len(content) <= 1024:
                continue
            dest = target / Path(name.replace('\\', '/')).name
            dest.write_bytes(content)
            written.append({'name': dest.name, 'bytes': len(content)})
        if not written:
            results[fid] = {'status': 'empty-font'}
            fail += 1
            continue
        state, size = state_of(fid)
        results[fid] = {'status': 'ok' if state == 'ok' else 'written-but-%s' % state,
                        'files': written, 'md5': md5}
        ok += 1
        print('[%d/%d] %-20s 成功 %s (%d bytes)' % (pos, len(bad), fid,
                                                   written[0]['name'], written[0]['bytes']),
              flush=True)
    except Exception as error:  # noqa: BLE001
        results[fid] = {'status': 'exception', 'error': str(error)[:180]}
        fail += 1
        print('[%d/%d] %-20s 异常 %s' % (pos, len(bad), fid, str(error)[:70]), flush=True)
    results_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')

print()
print('直接下载完成：成功 %d，失败 %d' % (ok, fail))

# 复核每个模板的字体状态
templates = audit['templates']
fixed = partial = broken = 0
for _rid, row in templates.items():
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
print('复核后模板字体状态：齐全 %d，部分 %d，全缺 %d' % (fixed, partial, broken))
(OUT / 'font-audit-after.json').write_text(
    json.dumps({'fixed': fixed, 'partial': partial, 'broken': broken,
                'ok': ok, 'fail': fail}, ensure_ascii=False, indent=2), encoding='utf-8')
