"""重新核对 108 个模板的字体匹配：递归提取模板声明的全部字体，与草稿实际使用对比。

之前的检测只看 `text_style.font_id`，导致 46 个模板被判为"未声明"（实为声明在别处）。
本脚本递归扫描 LyricStyle.json 里所有字体类字段，得到完整的声明集合，
再判断草稿实际使用的字体是否落在声明集合内 —— 不在集合内才是真正的"回退默认字体"。
"""
import json
import os
import sys
from pathlib import Path

ROOT = Path.cwd()
sys.path[:0] = [str(ROOT / 'skills/guzhu-hao/scripts'), str(ROOT / 'engine')]
CACHE = (Path(os.environ['LOCALAPPDATA']) / 'JianyingPro/User Data/Cache'
         / 'lyra-cli' / 'material-cache')
LYRICDIR = CACHE / 'lyric_animation'
FONTDIR = CACHE / 'font'
FONT_SUFFIX = ('.ttf', '.otf', '.ttc')

FONT_KEYS = ('font_id', 'font_resource_id', 'fontid')


def collect_fonts(node, found):
    """递归收集任意层级里的字体 id。"""
    if isinstance(node, dict):
        for key, value in node.items():
            if key.lower() in FONT_KEYS:
                values = value if isinstance(value, list) else [value]
                for v in values:
                    if str(v).isdigit() and 15 <= len(str(v)) <= 20:
                        found.add(str(v))
            else:
                collect_fonts(value, found)
    elif isinstance(node, list):
        for v in node:
            collect_fonts(v, found)
    return found


def style_of(tid):
    folder = LYRICDIR / tid
    if not folder.is_dir():
        return None
    path = next(folder.rglob('LyricStyle.json'), None)
    if path is None:
        return None
    try:
        return json.loads(path.read_text(encoding='utf-8', errors='replace'))
    except Exception:  # noqa: BLE001
        return None


def font_available(fid):
    """字体是否真的可用：font.lock 有内容（渲染就认这个）。"""
    lock = FONTDIR / str(fid) / 'font.lock'
    if lock.is_file() and lock.stat().st_size > 1024:
        return 'ok', lock.stat().st_size
    folder = FONTDIR / str(fid)
    if folder.is_dir():
        files = [f for f in folder.rglob('*') if f.is_file()
                 and f.suffix.lower() in FONT_SUFFIX and f.stat().st_size > 1024]
        if files:
            return 'font-only', max(f.stat().st_size for f in files)
        return 'empty', 0
    return 'missing', 0


results = json.loads((ROOT / 'work/guzhu-templates/visual108/render-results.json')
                     .read_text(encoding='utf-8'))
report = []
summary = {'match': 0, 'mismatch': 0, 'no-decl': 0, 'render-failed': 0}
for rid, row in sorted(results.items(), key=lambda kv: str(kv[1].get('title'))):
    title = row.get('title')
    if row.get('status') != 'ok':
        summary['render-failed'] += 1
        report.append({'id': rid, 'title': title, 'verdict': 'render-failed',
                       'status': row.get('status')})
        continue
    data = style_of(rid)
    declared = sorted(collect_fonts(data, set())) if data else []
    used = {str(k): str(v) for k, v in (row.get('draft_fonts') or {}).items()}
    if not declared:
        summary['no-decl'] += 1
        report.append({'id': rid, 'title': title, 'verdict': 'no-declaration',
                       'declared': [], 'used': sorted(used)})
        continue
    hit = [f for f in used if f in declared]
    miss = [f for f in used if f not in declared]
    fonts_state = {f: font_available(f)[0] for f in sorted(used)}
    verdict = 'match' if hit and not miss else ('mismatch' if miss and not hit else
                                                ('match' if hit else 'mismatch'))
    summary[verdict] += 1
    report.append({'id': rid, 'title': title, 'verdict': verdict,
                   'declared': declared, 'used_matched': sorted(hit),
                   'used_unexpected': sorted(miss), 'font_state': fonts_state})

print('== 汇总 ==')
for key, value in summary.items():
    print('  %-14s %d' % (key, value))
print()
print('== 真正不匹配（草稿用了模板未声明的字体）==')
for item in report:
    if item['verdict'] == 'mismatch':
        print('  %-14s 声明=%s' % (item['title'], item['declared']))
        print('      实际用了=%s  字体状态=%s' % (item['used_unexpected'],
                                              {k: v for k, v in item['font_state'].items()
                                               if k in item['used_unexpected']}))
print()
print('== 模板未声明字体（检测不到基准）==')
for item in report:
    if item['verdict'] == 'no-declaration':
        print('  %-14s 实际用了=%s' % (item['title'], item['used']))

out = ROOT / 'work/guzhu-templates/font-match-audit.json'
out.write_text(json.dumps({'summary': summary, 'report': report},
                          ensure_ascii=False, indent=2), encoding='utf-8')
print()
print('已写入 %s' % out)
