"""贴纸缩放到 2.0 倍（改段级关键帧），并把三个氛围特效强度设为 10。"""
import json
import sys
from pathlib import Path

ROOT = Path.cwd()
sys.path[:0] = [str(ROOT / 'skills/guzhu-hao/scripts'), str(ROOT / 'engine')]
import guzhu_batch as gb
import lyra_cli
from guzhu_timeline import Editor, range_of

root = gb.draft_root(ROOT)
folder = sorted([d for d in Path(root).iterdir() if d.name.startswith('guzhu-')],
                key=lambda p: p.stat().st_mtime_ns, reverse=True)[0]
ref = 'local://' + folder.name

# ---- 1. 贴纸放大 2.0：真正生效的是段级 common_keyframes 里的 ScaleX/ScaleY ----
TARGET_SCALE = 2.0
timeline, source = gb.read_draft_timeline(ROOT, folder)
editor = Editor(timeline)
report = {'sticker_scale': TARGET_SCALE, 'stickers': [], 'effect_intensity': []}
for _track, segment in editor.segments():
    if editor.bucket(segment.get('material_id')) != 'stickers':
        continue
    changed = []
    for group in segment.get('common_keyframes') or []:
        prop = str(group.get('property_type') or '')
        if 'Scale' not in prop:
            continue
        for point in group.get('keyframe_list') or []:
            before = list(point.get('values') or [])
            point['values'] = [TARGET_SCALE]
            changed.append({'property': prop, 'before': before, 'after': [TARGET_SCALE]})
    # clip.scale 同步（不影响渲染，但保持草稿一致）
    segment.setdefault('clip', {})['scale'] = {'x': TARGET_SCALE, 'y': TARGET_SCALE}
    report['stickers'].append({'segment': segment['id'][:8], 'keyframes': changed})
gb.write_draft_timeline(ROOT, folder, timeline, source)
print('贴纸关键帧已设为 %.1f：' % TARGET_SCALE)
for item in report['stickers']:
    print('  %s 改了 %d 个关键帧组' % (item['segment'], len(item['keyframes'])))

# ---- 2. 特效强度设为 10（0-1 归一，10 即 0.10）----
INTENSITY = 0.10
timeline2, _ = gb.read_draft_timeline(ROOT, folder)
editor2 = Editor(timeline2)
main = [s for _t, s in editor2.segments()
        if editor2.bucket(s.get('material_id')) == 'videos' and range_of(s)[0] > 0]
main_id = main[0]['id']
SEG_FX = ['7581434656197741849']            # 梦幻漏光（段特效，有 intensity）
GLOBAL_FX = ['7496779956345654552', '7666032151833546008']  # 细雨 / 婆娑光斑（全局轨）

for rid in SEG_FX + GLOBAL_FX:
    try:
        result = lyra_cli.draft(['video', 'effect', 'update'], str(root), ref,
                                {'--seg-id': main_id, '--resource-id': rid,
                                 '--params-json': json.dumps(
                                     {'effects_adjust_intensity': INTENSITY})})
        gb._mirror_draft(folder)
        report['effect_intensity'].append({'resource_id': rid, 'intensity': INTENSITY,
                                           'result': str(result)[:100]})
        print('  特效 %s intensity=%s' % (rid, INTENSITY))
    except Exception as error:  # noqa: BLE001
        report['effect_intensity'].append({'resource_id': rid, 'intensity': INTENSITY,
                                           'error': str(error)[:160]})
        print('  特效 %s 设强度失败：%s' % (rid, str(error)[:120]))

# ---- 3. 回读 ----
timeline3, _ = gb.read_draft_timeline(ROOT, folder)
editor3 = Editor(timeline3)
verify = []
for _t, s in editor3.segments():
    if editor3.bucket(s.get('material_id')) == 'stickers':
        vals = [pt.get('values') for g in (s.get('common_keyframes') or [])
                for pt in (g.get('keyframe_list') or [])]
        verify.append({'sticker': s['id'][:8], 'scale_values': vals})
report['verify_stickers'] = verify
print()
print('回读贴纸关键帧值:', verify[:2])
for m in timeline3.get('materials', {}).get('video_effects') or []:
    if m.get('resource_id') in SEG_FX + GLOBAL_FX:
        print('  %-8s adjust_params=%s' % (m.get('name'),
              json.dumps([(p['name'], p['value']) for p in m.get('adjust_params') or []], ensure_ascii=False)))

out = ROOT / 'work/guzhu-buneng-v3'
(out / 'scale2-and-intensity.json').write_text(
    json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
