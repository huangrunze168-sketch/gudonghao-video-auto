"""把贴纸缩放从 2.0 调回 0.8（改段级关键帧 ScaleX/ScaleY）。"""
import json
import sys
from pathlib import Path

ROOT = Path.cwd()
sys.path[:0] = [str(ROOT / 'skills/guzhu-hao/scripts'), str(ROOT / 'engine')]
import guzhu_batch as gb
from guzhu_timeline import Editor, range_of

TARGET = 0.8
root = gb.draft_root(ROOT)
folder = sorted([d for d in Path(root).iterdir() if d.name.startswith('guzhu-')],
                key=lambda p: p.stat().st_mtime_ns, reverse=True)[0]
print('草稿:', folder.name)

timeline, source = gb.read_draft_timeline(ROOT, folder)
editor = Editor(timeline)
rows = []
for _track, segment in editor.segments():
    if editor.bucket(segment.get('material_id')) != 'stickers':
        continue
    node = editor.node(segment.get('material_id')) or {}
    groups = 0
    for group in segment.get('common_keyframes') or []:
        if 'Scale' not in str(group.get('property_type') or ''):
            continue
        for point in group.get('keyframe_list') or []:
            point['values'] = [TARGET]
            groups += 1
    segment.setdefault('clip', {})['scale'] = {'x': TARGET, 'y': TARGET}
    rows.append({'name': str(node.get('name'))[:16], 'segment': segment['id'][:8],
                 'keyframe_points': groups, 'range': range_of(segment)})
gb.write_draft_timeline(ROOT, folder, timeline, source)

print('贴纸缩放设为 %.2f：' % TARGET)
for item in rows:
    print('  %-16s %s  关键帧点=%d' % (item['name'], item['segment'], item['keyframe_points']))

out = ROOT / 'work/guzhu-buneng-v3'
(out / 'sticker-scale-08.json').write_text(
    json.dumps({'scale': TARGET, 'stickers': rows}, ensure_ascii=False, indent=2),
    encoding='utf-8')
