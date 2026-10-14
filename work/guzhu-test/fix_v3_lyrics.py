"""纠正官方模板重建后的整句文本，保留段时间、官方字体和动画。"""
import json
import sys
from pathlib import Path

ROOT = Path.cwd()
sys.path[:0] = [str(ROOT / 'skills/guzhu-hao/scripts'), str(ROOT / 'engine')]
import guzhu_batch as gb
from guzhu_timeline import Editor, range_of, retitle

root = Path(gb.draft_root(ROOT))
folders = sorted([d for d in root.iterdir() if d.name.startswith('guzhu-')],
                 key=lambda p: p.stat().st_mtime_ns, reverse=True)
folder = folders[0]
print('草稿:', folder.name)

timeline, source = gb.read_draft_timeline(ROOT, folder)
editor = Editor(timeline)
rows = []
for _track, segment in editor.segments():
    node = editor.node(segment.get('material_id')) or {}
    if editor.bucket(segment.get('material_id')) == 'texts' and node.get('type') != 'subtitle':
        rows.append((range_of(segment)[0], segment, node))
rows.sort(key=lambda row: row[0])

# 保留官方模板的双行排版：换行不能拍平成空格，否则整句会横向溢出。
lines = ['有一些瞬间\n我在命运之外', '楼下站着\n一直在发呆', '屏幕亮起来\n我没理睬',
         '那几分钟\n我才算存在', '你也试过吧\n不想上来', '掏钥匙的手\n慢了半拍',
         '呼一口气\n才把锁打开']
if len(rows) != len(lines):
    raise RuntimeError('歌词段数变化，停止自动修改')

changes = []
for (_start, segment, node), text in zip(rows, lines):
    before = gb._recognized_text(node)
    retitle(node, text)
    changes.append({'id': segment['id'], 'before': before, 'after': text,
                    'range': range_of(segment)})
gb.write_draft_timeline(ROOT, folder, timeline, source)

out = ROOT / 'work/guzhu-mingyun-v3'
out.mkdir(parents=True, exist_ok=True)
(out / 'lyrics-correction.json').write_text(
    json.dumps(changes, ensure_ascii=False, indent=2), encoding='utf-8')
print('已校正七句歌词：')
for item in changes:
    print('  %-14s -> %s' % (str(item['before'])[:12].replace('\n', '/'),
                             item['after'].replace('\n', ' / ')))
