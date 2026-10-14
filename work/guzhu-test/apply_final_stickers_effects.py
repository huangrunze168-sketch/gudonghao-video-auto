"""应用贴纸缩放 0.5、搞笑贴纸、三个低强度特效，然后导出。"""
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
report = {}

# ---- 1. 贴纸：换成按情绪在线搜的猫狗搞笑表情包，并缩放到 0.5 ----
STICKERS = [
    ('6896119772367342861', '疑惑的猫咪'),
    ('7664170229227949337', '外星小猫-无语'),
    ('7114596400435825959', '笑哭'),
    ('7615857378789215550', '线条小狗-加油'),
    ('7171325230206487839', '猫咪竖大拇指'),
]
for rid, _name in STICKERS:
    execute(ROOT, ['material', 'download', '--type', 'sticker', '--resource-id', rid])

timeline, _ = gb.read_draft_timeline(ROOT, folder)
editor = Editor(timeline)
old = [s for _t, s in editor.segments()
       if editor.bucket(s.get('material_id')) == 'stickers']
groups = sorted([g for g in gb.inspect_template(timeline).groups if g.tts_segment],
                key=lambda g: range_of(g.tts_segment)[0])
if len(groups) != len(STICKERS):
    raise RuntimeError('口播组 %d != 贴纸 %d' % (len(groups), len(STICKERS)))

for segment in old:
    lyra_cli.draft(['sticker', 'remove'], str(root), ref, {'--seg-id': segment['id']})
    gb._mirror_draft(folder)

placed = []
for group, (rid, name) in zip(groups, STICKERS):
    start, duration = range_of(group.tts_segment)
    timeline, _ = gb.read_draft_timeline(ROOT, folder)
    editor = Editor(timeline)
    before = {s['id'] for _t, s in editor.segments()
              if editor.bucket(s.get('material_id')) == 'stickers'}
    lyra_cli.draft(['sticker', 'add'], str(root), ref,
                   {'--resource': 'vimo://' + rid,
                    '--start': '%.6fs' % (start / 1e6),
                    '--duration': '%.6fs' % (duration / 1e6)})
    gb._mirror_draft(folder)
    timeline, _ = gb.read_draft_timeline(ROOT, folder)
    editor = Editor(timeline)
    added = [s for _t, s in editor.segments()
             if editor.bucket(s.get('material_id')) == 'stickers' and s['id'] not in before]
    if len(added) != 1:
        raise RuntimeError('新增贴纸段异常')
    sid = added[0]['id']
    lyra_cli.draft(['sticker', 'translate'], str(root), ref,
                   {'--seg-id': sid, '--x': '0', '--y': '0.42'})
    gb._mirror_draft(folder)
    placed.append({'name': name, 'segment': sid, 'start_us': start})

# 缩放到 0.5：真正生效的是段级 common_keyframes 的 ScaleX/ScaleY
timeline, source = gb.read_draft_timeline(ROOT, folder)
editor = Editor(timeline)
scaled = 0
for _track, segment in editor.segments():
    if editor.bucket(segment.get('material_id')) != 'stickers':
        continue
    for group in segment.get('common_keyframes') or []:
        if 'Scale' not in str(group.get('property_type') or ''):
            continue
        for point in group.get('keyframe_list') or []:
            point['values'] = [0.5]
    segment.setdefault('clip', {})['scale'] = {'x': 0.5, 'y': 0.5}
    scaled += 1
gb.write_draft_timeline(ROOT, folder, timeline, source)
report['stickers'] = {'placed': placed, 'scaled_to': 0.5, 'count': scaled}
print('贴纸：%d 组，缩放 0.5' % scaled)

# ---- 2. 特效：段特效 + 全局效果轨，强度 10 ----
timeline, _ = gb.read_draft_timeline(ROOT, folder)
editor = Editor(timeline)
main = [s for _t, s in editor.segments()
        if editor.bucket(s.get('material_id')) == 'videos' and range_of(s)[0] > 0]
main_id = main[0]['id']
main_start, main_dur = range_of(main[0])

SEG = ('7581434656197741849', '梦幻漏光')
GLOBALS = [('7496779956345654552', '细雨'), ('7666032151833546008', '婆娑光斑')]
for rid, _n in [SEG] + GLOBALS:
    execute(ROOT, ['material', 'download', '--type', 'effect', '--resource-id', rid])
lyra_cli.draft(['video', 'effect', 'add'], str(root), ref,
               {'--seg-id': main_id, '--resource': 'vimo://' + SEG[0]})
gb._mirror_draft(folder)
global_added = []
for rid, name in GLOBALS:
    lyra_cli.draft(['effect', 'add'], str(root), ref,
                   {'--resource': 'vimo://' + rid,
                    '--start': '%.6fs' % (main_start / 1e6),
                    '--duration': '%.6fs' % (main_dur / 1e6)})
    gb._mirror_draft(folder)
    global_added.append(name)
for rid, _n in [SEG] + GLOBALS:
    try:
        lyra_cli.draft(['video', 'effect', 'update'], str(root), ref,
                       {'--seg-id': main_id, '--resource-id': rid,
                        '--params-json': json.dumps({'effects_adjust_intensity': 0.10})})
        gb._mirror_draft(folder)
    except Exception:  # noqa: BLE001
        pass
report['effects'] = {'segment': SEG[1], 'globals': global_added, 'intensity': 0.10}
print('特效：%s + %s，强度 0.10' % (SEG[1], '、'.join(global_added)))

(ROOT / 'work/guzhu-buneng-v3' / 'final-application.json').write_text(
    json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
