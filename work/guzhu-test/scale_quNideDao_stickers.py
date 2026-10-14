"""按官方关键帧结构给贴纸段设置缩放（段级 common_keyframes 的 KFTypeScaleX/Y）。

结构取自其它草稿里可用的贴纸关键帧：
  {"id": uuid, "material_id": "", "property_type": "KFTypeScaleX",
   "keyframe_list": [{"id": uuid, "left_control": {x,y}, "right_control": {x,y},
                      "values": [scale]}]}

新贴纸默认用素材原始尺寸，有的（"想你"白猫）会铺满画面遮挡内容，
必须显式缩放。
"""
import json
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

ROOT = Path.cwd()
sys.path[:0] = [str(ROOT / 'skills/guzhu-hao/scripts'), str(ROOT / 'engine')]
import guzhu_batch as gb
import jypack_render
from guzhu_timeline import Editor

SCALE = float(sys.argv[1]) if len(sys.argv) > 1 else 0.5
PROJECT = ROOT / 'work/guzhu-quNideDao-v1'


def make_group(property_type, scale):
    def point():
        return {
            'id': str(uuid.uuid4()).upper(),
            'left_control': {'x': 0.0, 'y': 0.0},
            'right_control': {'x': 0.0, 'y': 0.0},
            'values': [scale],
        }
    return {
        'id': str(uuid.uuid4()).upper(),
        'keyframe_list': [point()],
        'material_id': '',
        'property_type': property_type,
    }


root = gb.draft_root(ROOT)
folder = sorted([d for d in Path(root).iterdir() if d.name.startswith('guzhu-')],
                key=lambda p: p.stat().st_mtime_ns, reverse=True)[0]
print('草稿 %s，目标缩放 %.2f' % (folder.name, SCALE))

timeline, source = gb.read_draft_timeline(ROOT, folder)
editor = Editor(timeline)
count = 0
for _track, segment in editor.segments():
    if editor.bucket(segment.get('material_id')) != 'stickers':
        continue
    kept = [g for g in (segment.get('common_keyframes') or [])
            if 'Scale' not in str(g.get('property_type') or '')]
    segment['common_keyframes'] = kept + [
        make_group('KFTypeScaleX', SCALE),
        make_group('KFTypeScaleY', SCALE),
    ]
    count += 1
gb.write_draft_timeline(ROOT, folder, timeline, source)
print('已为 %d 个贴纸段写入缩放关键帧' % count)

produced = max(PROJECT.glob('locate/jypack/*.jypack'), key=lambda p: p.stat().st_mtime_ns)
timeline2, source2 = gb.read_draft_timeline(ROOT, folder)
jypack_id = jypack_render.package_timeline_id(produced)
if timeline2.get('id') != jypack_id:
    timeline2['id'] = jypack_id
    gb.write_draft_timeline(ROOT, folder, timeline2, source2)

OUT = PROJECT / 'final'
if OUT.exists():
    shutil.rmtree(OUT, ignore_errors=True)
result = subprocess.run(
    [sys.executable, str(ROOT / 'engine/jypack_render.py'),
     '--input', str(produced), '--draft-dir', str(folder), '--out', str(OUT),
     '--width', '1280', '--height', '720', '--fps', '30', '--timeout', '1800'],
    capture_output=True, timeout=2400)
print('导出退出码 %s' % result.returncode)
if result.returncode != 0:
    print(result.stderr.decode('utf-8', 'replace')[-300:])
    raise SystemExit(1)
video = OUT / 'render.mp4'
print('成片: %s (%d bytes)' % (video, video.stat().st_size))
