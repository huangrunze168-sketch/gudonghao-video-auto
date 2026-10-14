"""纠正《比恋人多点恨》成片里的 ASR 错字（等长替换），然后重导出。

官方 ASR 把「仇人」识别成「超人」、「在一块」识别成「在一快」。
模板是逐词碎片段，所以按段逐段做等长替换，不改变字数与分段。
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd()
sys.path[:0] = [str(ROOT / 'skills/guzhu-hao/scripts'), str(ROOT / 'engine')]
import guzhu_batch as gb
from guzhu_timeline import Editor, range_of, retitle

# 按从长到短匹配，避免短串先命中
REPLACEMENTS = [
    ('超人多点爱', '仇人多点爱'),
    ('超人', '仇人'),
    ('在一快', '在一块'),
    ('不放过', '不放过'),
]
for old, new in REPLACEMENTS:
    if len(old) != len(new):
        raise RuntimeError('替换长度不一致: %s -> %s' % (old, new))

root = gb.draft_root(ROOT)
folder = sorted([d for d in Path(root).iterdir() if d.name.startswith('guzhu-')],
                key=lambda p: p.stat().st_mtime_ns, reverse=True)[0]
print('草稿:', folder.name)

timeline, source = gb.read_draft_timeline(ROOT, folder)
editor = Editor(timeline)
changes = []
for _track, segment in editor.segments():
    node = editor.node(segment.get('material_id')) or {}
    if editor.bucket(segment.get('material_id')) != 'texts':
        continue
    if node.get('type') == 'subtitle':
        continue
    before = str(gb._recognized_text(node))
    after = before
    for old, new in REPLACEMENTS:
        after = after.replace(old, new)
    if after != before:
        retitle(node, after)
        changes.append({'before': before, 'after': after,
                        'range': [int(v) for v in range_of(segment)]})

gb.write_draft_timeline(ROOT, folder, timeline, source)
print('纠正 %d 段：' % len(changes))
for item in changes:
    print('   %s -> %s' % (item['before'].replace('\n', '/'),
                          item['after'].replace('\n', '/')))

out = ROOT / 'work/guzhu-bilianren-v1'
(out / 'typo-fix.json').write_text(
    json.dumps(changes, ensure_ascii=False, indent=2), encoding='utf-8')

# 重导出
jypack = ROOT / 'work/guzhu-bilianren-v1/locate/jypack/比恋人多点恨.jypack'
if not jypack.is_file():
    jypack = next((ROOT / 'work/guzhu-bilianren-v1').rglob('*.jypack'), None)
    print('找到 jypack: %s' % jypack)
target = out / 'final'
if target.exists():
    import shutil
    shutil.rmtree(target, ignore_errors=True)
result = subprocess.run(
    [sys.executable, str(ROOT / 'engine/jypack_render.py'),
     '--input', str(jypack), '--draft-dir', str(folder), '--out', str(target),
     '--width', '1280', '--height', '720', '--fps', '30', '--timeout', '1800'],
    capture_output=True, timeout=2400)
print('导出退出码 %s' % result.returncode)
if result.returncode != 0:
    print(result.stderr.decode('utf-8', 'replace')[-400:])
else:
    video = target / 'render.mp4'
    print('成片: %s (%d bytes)' % (video, video.stat().st_size if video.is_file() else -1))
