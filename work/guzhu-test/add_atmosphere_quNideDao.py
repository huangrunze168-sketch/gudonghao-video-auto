"""给成片补氛围层，解决"画面太单调"。

做三件事（都走官方命令）：
1. 主画面段挂一个段特效；
2. 再用全局效果轨叠 2–3 个氛围特效（段特效同一时刻只留一个，叠加必须走全局轨）；
3. 用 `draft adjust add` 做一次全局调色（暖调、提饱和、抬阴影）。
强度统一调低（0.1），只做氛围不抢内容。
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd()
sys.path[:0] = [str(ROOT / 'skills/guzhu-hao/scripts'), str(ROOT / 'engine')]
import guzhu_batch as gb
import jypack_render
import lyra_cli
from official_materials import execute
from guzhu_timeline import Editor, range_of

PROJECT = ROOT / 'work/guzhu-quNideDao-v1'
SEGMENT_EFFECT = ('7581434656197741849', '梦幻漏光')
GLOBAL_EFFECTS = [
    ('7685029541189913880', '光斑流动'),
    ('7496779956345654552', '细雨'),
]
INTENSITY = 0.10
ADJUST = {'saturation': 8, 'color-temperature': 6, 'shadow': 5, 'contrast': 4}

root = gb.draft_root(ROOT)
folder = sorted([d for d in Path(root).iterdir() if d.name.startswith('guzhu-')],
                key=lambda p: p.stat().st_mtime_ns, reverse=True)[0]
ref = 'local://' + folder.name
print('草稿:', folder.name)

for rid, name in [SEGMENT_EFFECT] + GLOBAL_EFFECTS:
    outcome = execute(ROOT, ['material', 'download', '--type', 'effect', '--resource-id', rid])
    print('  下载 %-10s %s' % (name, outcome.get('status')))

# 主画面段（时长最长的视频段）
timeline, _ = gb.read_draft_timeline(ROOT, folder)
editor = Editor(timeline)
mains = sorted([s for _t, s in editor.segments()
                if editor.bucket(s.get('material_id')) == 'videos'],
               key=lambda s: -range_of(s)[1])
if not mains:
    raise SystemExit('找不到主画面段')
main = mains[0]
main_id = main['id']
main_start, main_dur = range_of(main)
print('主画面段 %s  %.2f-%.2fs' % (main_id[:8], main_start / 1e6,
                                 (main_start + main_dur) / 1e6))

# 1) 段特效
lyra_cli.draft(['video', 'effect', 'add'], str(root), ref,
               {'--seg-id': main_id, '--resource': 'vimo://' + SEGMENT_EFFECT[0]})
gb._mirror_draft(folder)
print('段特效：%s' % SEGMENT_EFFECT[1])

# 2) 全局效果轨（叠加）
for rid, name in GLOBAL_EFFECTS:
    try:
        lyra_cli.draft(['effect', 'add'], str(root), ref,
                       {'--resource': 'vimo://' + rid,
                        '--start': '%.6fs' % (main_start / 1e6),
                        '--duration': '%.6fs' % (main_dur / 1e6)})
        gb._mirror_draft(folder)
        print('全局特效：%s' % name)
    except Exception as error:  # noqa: BLE001
        print('全局特效 %s 失败：%s' % (name, str(error).replace('\n', ' ')[:120]))

# 3) 降低强度（有 intensity 参数的才生效）
for rid, name in [SEGMENT_EFFECT] + GLOBAL_EFFECTS:
    try:
        lyra_cli.draft(['video', 'effect', 'update'], str(root), ref,
                       {'--seg-id': main_id, '--resource-id': rid,
                        '--params-json': json.dumps({'effects_adjust_intensity': INTENSITY})})
        gb._mirror_draft(folder)
    except Exception:  # noqa: BLE001
        pass
print('强度统一 %.2f（无该参数的特效会忽略）' % INTENSITY)

# 4) 全局调色
try:
    args = {'--start': '%.6fs' % 0, '--duration': '%.6fs' % ((main_start + main_dur) / 1e6)}
    for key, value in ADJUST.items():
        args['--' + key] = str(value)
    lyra_cli.draft(['adjust', 'add'], str(root), ref, args)
    gb._mirror_draft(folder)
    print('全局调色：%s' % ADJUST)
except Exception as error:  # noqa: BLE001
    print('调色失败：%s' % str(error).replace('\n', ' ')[:160])

# 导出
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
