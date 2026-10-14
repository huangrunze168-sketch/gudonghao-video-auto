"""逐个模板审计字体依赖：区分"有真实字体文件"与"只剩 lock 的假下载"。"""
import json
import os
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
CACHE = (Path(os.environ['LOCALAPPDATA']) / 'JianyingPro/User Data/Cache'
         / 'lyra-cli' / 'material-cache')
FONTDIR = CACHE / 'font'
LIBDIR = CACHE / 'lyric_animation'
OUT = Path('work/guzhu-templates')

FONT_SUFFIX = ('.ttf', '.otf', '.ttc')


def font_state(font_id):
    """判断字体是否真的可用：有 >1KB 的字体文件才算可用。"""
    folder = FONTDIR / str(font_id)
    if not folder.is_dir():
        return 'missing-dir', 0
    files = [f for f in folder.rglob('*')
             if f.is_file() and f.suffix.lower() in FONT_SUFFIX and f.stat().st_size > 1024]
    if files:
        return 'ok', max(f.stat().st_size for f in files)
    locks = [f for f in folder.rglob('*') if f.is_file()]
    return ('lock-only' if locks else 'empty-dir'), 0


def font_ids_of(style_path):
    try:
        data = json.loads(Path(style_path).read_text(encoding='utf-8', errors='replace'))
    except Exception:  # noqa: BLE001
        return []
    found = set()

    def walk(node):
        if isinstance(node, dict):
            for key, value in node.items():
                if key in ('font_id', 'font_resource_id'):
                    values = value if isinstance(value, list) else [value]
                    for v in values:
                        if str(v).isdigit() and len(str(v)) >= 15:
                            found.add(str(v))
                else:
                    walk(value)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(data)
    return sorted(found)


library = json.loads((OUT / 'library/index.json').read_text(encoding='utf-8'))
ready = {k: v for k, v in library.items() if v.get('download') == 'ok'}

fonts = {}
templates = {}
for rid, info in sorted(ready.items()):
    style = next((LIBDIR / rid).rglob('LyricStyle.json'), None) if (LIBDIR / rid).is_dir() else None
    if style is None:
        templates[rid] = {'title': info.get('title'), 'fonts': [], 'state': 'no-style'}
        continue
    ids = font_ids_of(style)
    states = []
    for fid in ids:
        state, size = font_state(fid)
        states.append(state)
        fonts.setdefault(fid, {'state': state, 'size': size, 'templates': []})
        fonts[fid]['templates'].append(info.get('title'))
    if not ids:
        overall = 'no-font-dep'
    elif all(s == 'ok' for s in states):
        overall = 'ok'
    elif any(s == 'ok' for s in states):
        overall = 'partial'
    else:
        overall = 'missing'
    templates[rid] = {'title': info.get('title'), 'fonts': ids, 'states': states,
                      'state': overall}

summary = {}
for rid, row in templates.items():
    summary[row['state']] = summary.get(row['state'], 0) + 1
print('模板字体状态汇总: %s' % summary)
print('涉及字体 %d 个，其中不可用 %d 个'
      % (len(fonts), sum(1 for v in fonts.values() if v['state'] != 'ok')))
print()
print('== 字体不可用的模板 ==')
for rid, row in sorted(templates.items()):
    if row['state'] in ('missing', 'partial'):
        print('  %-12s %-14s %s  %s' % (row['state'], row['title'], rid, row['fonts']))
print()
print('== 不可用字体清单（按影响模板数）==')
bad = sorted([(k, v) for k, v in fonts.items() if v['state'] != 'ok'],
             key=lambda kv: -len(kv[1]['templates']))
for fid, v in bad[:30]:
    print('  %-20s %-11s 影响 %2d 个模板: %s' % (fid, v['state'], len(v['templates']),
                                             '、'.join(str(t)[:8] for t in v['templates'][:4])))

(OUT / 'font-audit.json').write_text(
    json.dumps({'summary': summary, 'templates': templates, 'fonts': fonts},
               ensure_ascii=False, indent=2), encoding='utf-8')
print()
print('审计结果写入 work/guzhu-templates/font-audit.json')
