"""放大贴纸，并按歌词意境叠加多个低强度画面特效。"""
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
print('草稿:', folder.name)

# ---- 1. 贴纸放大：直接写 clip.scale（关键帧通道实测写不进 common_keyframes）----
STICKER_SCALE = 0.75
timeline, source = gb.read_draft_timeline(ROOT, folder)
editor = Editor(timeline)
scaled = []
for _track, segment in editor.segments():
    if editor.bucket(segment.get('material_id')) != 'stickers':
        continue
    clip = segment.setdefault('clip', {})
    clip['scale'] = {'x': STICKER_SCALE, 'y': STICKER_SCALE}
    scaled.append(segment['id'])
gb.write_draft_timeline(ROOT, folder, timeline, source)
print('贴纸放大到 %.2f：%d 个' % (STICKER_SCALE, len(scaled)))

# ---- 2. 按歌词意境叠加多个低强度画面特效 ----
EFFECTS = [
    ('7496779956345654552', '细雨'),
    ('7666032151833546008', '婆娑光斑'),
    ('7581434656197741849', '梦幻漏光'),
]
timeline2, _ = gb.read_draft_timeline(ROOT, folder)
editor2 = Editor(timeline2)
main = [s for _t, s in editor2.segments()
        if editor2.bucket(s.get('material_id')) == 'videos' and range_of(s)[0] > 0]
if len(main) != 1:
    raise RuntimeError('主视频段数量异常：%d' % len(main))
main_id = main[0]['id']

added = []
for rid, name in EFFECTS:
    r = execute(ROOT, ['material', 'download', '--type', 'effect', '--resource-id', rid])
    if 'envelope' not in r:
        print('  特效 %s 下载失败，跳过' % name)
        continue
    lyra_cli.draft(['video', 'effect', 'add'], str(root), ref,
                   {'--seg-id': main_id, '--resource': 'vimo://' + rid})
    gb._mirror_draft(folder)
    added.append({'resource_id': rid, 'name': name})
    print('  已加特效：%s' % name)

# ---- 3. 回读确认每个特效真实引用在视频段上 ----
timeline3, _ = gb.read_draft_timeline(ROOT, folder)
editor3 = Editor(timeline3)
nodes = {m['id']: m for m in timeline3.get('materials', {}).get('video_effects') or []}
target = next((s for _t, s in editor3.segments() if s['id'] == main_id), None)
applied = [nodes[r].get('name') for r in (target or {}).get('extra_material_refs', [])
           if r in nodes]
print('主视频段实际引用特效：%s' % applied)

out = ROOT / 'work/guzhu-buneng-v3'
report = {'draft': str(folder), 'sticker_scale': STICKER_SCALE,
          'sticker_segments': scaled, 'effects_added': added,
          'effects_on_main': applied}
(out / 'sticker-and-effects.json').write_text(
    json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
