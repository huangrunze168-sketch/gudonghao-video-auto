"""修正《比恋人多点恨》剩余 ASR 错段并重导出。

`一扇门总有` 是官方 ASR 对「你摔门走」的错误识别，必须改。
其余段核对无误。改完重导出最终成片。
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
from guzhu_timeline import Editor, range_of, retitle

# 段 id -> 正确文本（跨段边界的整句错误无法等长，按段整体改写）
FIXES = {
    '0CF53E33': '你摔门走',   # 原 "一扇门总有"
}
PRODUCED = ROOT / 'work/guzhu-bilianren-v1/locate/jypack/比恋人多点恨.jypack'

root = gb.draft_root(ROOT)
folder = sorted([d for d in Path(root).iterdir() if d.name.startswith('guzhu-')],
                key=lambda p: p.stat().st_mtime_ns, reverse=True)[0]
timeline, source = gb.read_draft_timeline(ROOT, folder)
editor = Editor(timeline)
changes = []
for _track, segment in editor.segments():
    sid = str(segment.get('id') or '')[:8]
    node = editor.node(segment.get('material_id')) or {}
    if editor.bucket(segment.get('material_id')) != 'texts':
        continue
    if node.get('type') == 'subtitle':
        continue
    if sid in FIXES:
        before = str(gb._recognized_text(node))
        retitle(node, FIXES[sid])
        changes.append({'segment': sid, 'before': before, 'after': FIXES[sid]})

gb.write_draft_timeline(ROOT, folder, timeline, source)
print('修正 %d 段：' % len(changes))
for item in changes:
    print('   %s: %s -> %s' % (item['segment'], item['before'], item['after']))

# 对齐 timeline id 后导出
timeline2, source2 = gb.read_draft_timeline(ROOT, folder)
jypack_id = jypack_render.package_timeline_id(PRODUCED)
if timeline2.get('id') != jypack_id:
    timeline2['id'] = jypack_id
    gb.write_draft_timeline(ROOT, folder, timeline2, source2)
    print('已对齐 timeline.id -> %s' % jypack_id)

out = ROOT / 'work/guzhu-bilianren-v1/final'
if out.exists():
    shutil.rmtree(out, ignore_errors=True)
result = subprocess.run(
    [sys.executable, str(ROOT / 'engine/jypack_render.py'),
     '--input', str(PRODUCED), '--draft-dir', str(folder), '--out', str(out),
     '--width', '1280', '--height', '720', '--fps', '30', '--timeout', '1800'],
    capture_output=True, timeout=2400)
print('导出退出码 %s' % result.returncode)
if result.returncode != 0:
    print(result.stderr.decode('utf-8', 'replace')[-300:])
else:
    video = out / 'render.mp4'
    print('成片: %s (%d bytes)' % (video, video.stat().st_size))
    (ROOT / 'work/guzhu-bilianren-v1/final-fixes.json').write_text(
        json.dumps(changes, ensure_ascii=False, indent=2), encoding='utf-8')
