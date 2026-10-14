"""在所有 guzhu-* 草稿里找带缩放关键帧的贴纸段，提取可复用的结构。"""
import json
import os
import sys
from pathlib import Path

ROOT = Path.cwd()
sys.path[:0] = [str(ROOT / 'skills/guzhu-hao/scripts'), str(ROOT / 'engine')]
import guzhu_batch as gb
from guzhu_timeline import Editor, range_of

DRAFTS = Path(gb.draft_root(ROOT))
found = []
for folder in sorted(DRAFTS.iterdir()):
    if not folder.name.startswith('guzhu-') or not (folder / 'Timelines').is_dir():
        continue
    try:
        timeline, _ = gb.read_draft_timeline(ROOT, folder)
    except Exception:  # noqa: BLE001
        continue
    editor = Editor(timeline)
    for _track, segment in editor.segments():
        if editor.bucket(segment.get('material_id')) != 'stickers':
            continue
        for group in segment.get('common_keyframes') or []:
            if 'Scale' not in str(group.get('property_type') or ''):
                continue
            values = [p.get('values') for p in (group.get('keyframe_list') or [])]
            found.append({
                'draft': folder.name,
                'segment': segment['id'][:8],
                'property': group.get('property_type'),
                'group_keys': sorted(group.keys()),
                'point_keys': sorted((group.get('keyframe_list') or [{}])[0].keys()),
                'values': values,
                'group_sample': group,
            })
            break

print('找到 %d 个带缩放关键帧的贴纸段' % len(found))
for item in found[:6]:
    print()
    print("草稿=%s 段=%s property=%s" % (item['draft'], item['segment'], item['property']))
    print("  group 键: %s" % item['group_keys'])
    print("  point 键: %s" % item['point_keys'])
    print("  values: %s" % item['values'])
    print("  完整结构: %s" % json.dumps(item['group_sample'], ensure_ascii=False)[:420])

if found:
    Path('work/guzhu-test/sticker-keyframe-sample.json').write_text(
        json.dumps(found[0]['group_sample'], ensure_ascii=False, indent=2),
        encoding='utf-8')
    print()
    print('样例已保存 work/guzhu-test/sticker-keyframe-sample.json')
