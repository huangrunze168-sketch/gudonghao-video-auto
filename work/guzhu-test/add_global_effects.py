"""用官方全局（轨道）特效通道再叠两个低强度氛围特效，然后导出。"""
import json
import os
import sys
from pathlib import Path

ROOT = Path.cwd()
sys.path[:0] = [str(ROOT / 'skills/guzhu-hao/scripts'), str(ROOT / 'engine')]
import guzhu_batch as gb
import lyra_cli
from official_materials import execute
from guzhu_timeline import Editor, range_of

os.environ['DSH_LYRA_ALLOW_NETWORK'] = '1'

root = gb.draft_root(ROOT)
folder = sorted([d for d in Path(root).iterdir() if d.name.startswith('guzhu-')],
                key=lambda p: p.stat().st_mtime_ns, reverse=True)[0]
ref = 'local://' + folder.name

timeline, _ = gb.read_draft_timeline(ROOT, folder)
editor = Editor(timeline)
main = [s for _t, s in editor.segments()
        if editor.bucket(s.get('material_id')) == 'videos' and range_of(s)[0] > 0]
main_start, main_dur = range_of(main[0])
print('主画面段: %.3fs 起，%.3fs 长' % (main_start / 1e6, main_dur / 1e6))

report = {'global_effects': []}
# 段特效同一时刻只保留一个，所以其余氛围特效走全局（轨道）通道叠加
for rid, name in [('7496779956345654552', '细雨'),
                  ('7666032151833546008', '婆娑光斑')]:
    r = execute(ROOT, ['material', 'download', '--type', 'effect', '--resource-id', rid])
    if 'envelope' not in r:
        print('  下载失败 %s' % name)
        continue
    try:
        result = lyra_cli.draft(['effect', 'add'], str(root), ref,
                                {'--resource': 'vimo://' + rid,
                                 '--start': '%.6fs' % (main_start / 1e6),
                                 '--duration': '%.6fs' % (main_dur / 1e6)})
        gb._mirror_draft(folder)
        report['global_effects'].append({'name': name, 'id': rid, 'result': str(result)[:120]})
        print('  全局特效已加：%s' % name)
    except Exception as error:  # noqa: BLE001
        print('  全局特效 %s 失败：%s' % (name, str(error)[:160]))
        report.setdefault('failures', []).append({'name': name, 'error': str(error)[:200]})

timeline2, _ = gb.read_draft_timeline(ROOT, folder)
nodes = {m['id']: m for m in timeline2.get('materials', {}).get('video_effects') or []}
all_effects = [m.get('name') for m in (timeline2.get('materials') or {}).get('video_effects') or []]
editor2 = Editor(timeline2)
seg_applied = []
for _t, s in editor2.segments():
    if editor2.bucket(s.get('material_id')) != 'videos':
        continue
    refs = [nodes[r].get('name') for r in (s.get('extra_material_refs') or []) if r in nodes]
    if refs:
        seg_applied.append({'segment': s['id'][:8], 'range': range_of(s), 'effects': refs})
report['effect_materials'] = all_effects
report['segment_effects'] = seg_applied
print()
print('特效素材总数: %s' % all_effects)
print('段引用: %s' % seg_applied)

out = ROOT / 'work/guzhu-buneng-v3'
(out / 'effects-report.json').write_text(
    json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
