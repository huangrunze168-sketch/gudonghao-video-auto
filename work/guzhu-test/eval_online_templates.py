"""下载在线歌词模板候选，按"中间显眼 + 字体依赖齐全"评估排序。"""
import json
import os
import sys
from pathlib import Path

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT / 'skills/guzhu-hao/scripts'))
sys.path.insert(0, str(ROOT / 'engine'))
from official_materials import execute
from guzhu_anim import animation_prominence, animation_dependencies_ready

os.environ['DSH_LYRA_ALLOW_NETWORK'] = '1'

cands = json.loads((ROOT / 'work/guzhu-mingyun-v2/online-lyric-candidates.json')
                   .read_text(encoding='utf-8'))
rows = []
for rid, info in cands.items():
    r = execute('.', ['material', 'download', '--type', 'lyric_animation', '--resource-id', rid])
    if 'envelope' not in r:
        rows.append({'id': rid, 'name': info['title'], 'size': None,
                     'prominent': False, 'ready': False, 'note': '下载失败'})
        print('  下载失败 %s %s' % (rid, info['title']), flush=True)
        continue
    p = Path(r['envelope']['result']['result']['path'])
    f = next(p.rglob('LyricStyle.json'), None)
    if f is None:
        rows.append({'id': rid, 'name': info['title'], 'size': None,
                     'prominent': False, 'ready': False, 'note': '无 LyricStyle'})
        continue
    ok, size, title = animation_prominence(str(f))
    ready = animation_dependencies_ready(str(f))
    rows.append({'id': rid, 'name': info['title'], 'style_title': title,
                 'size': size, 'prominent': ok, 'ready': ready})
    print('  %-6s %-6s 字号=%-4s %-20s %s'
          % ('显眼' if ok else '不显眼', '字体齐' if ready else '缺字体', size, rid, info['title']),
          flush=True)

rows.sort(key=lambda r: (not r.get('prominent'), not r.get('ready'), -(r.get('size') or 0)))
(ROOT / 'work/guzhu-mingyun-v2/online-lyric-eval.json').write_text(
    json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf-8')
print()
best = [r for r in rows if r.get('prominent') and r.get('ready')]
print('【显眼且字体齐全】%d 个:' % len(best))
for r in best:
    print('   字号=%-4s %-20s %s' % (r['size'], r['id'], r['name']))
print()
prom = [r for r in rows if r.get('prominent')]
print('【显眼（含缺字体）】%d 个' % len(prom))
