"""按真实歌词校正官方模板重建后的文本，保留段时间、官方字体和动画。"""
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

# 30 秒选段落在 Chorus 1 附近：按每段的实际时长填对应歌词，保留双行排版。
lines = ['后来忙着生活 没空重来\n才发现我早已不再等待',
         '突然某天 我不再需要答案',
         '你爱没爱过 都不必再审判',
         '那些没说完 就停在没说完',
         '把困在门外的自己领回身边',
         '突然某天 我不再需要答案']
if len(rows) != len(lines):
    raise RuntimeError('歌词段数变化（%d），停止自动修改' % len(rows))

changes = []
for (_start, segment, node), text in zip(rows, lines):
    before = gb._recognized_text(node)
    retitle(node, text)
    changes.append({'id': segment['id'], 'start_us': _start,
                    'before': before, 'after': text})
gb.write_draft_timeline(ROOT, folder, timeline, source)

out = ROOT / 'work/guzhu-buneng'
out.mkdir(parents=True, exist_ok=True)
(out / 'lyrics-correction.json').write_text(
    json.dumps(changes, ensure_ascii=False, indent=2), encoding='utf-8')
print('已校正 %d 段歌词：' % len(changes))
for item in changes:
    print('  %7.3f  %s  ->  %s' % (item['start_us'] / 1e6,
                                   str(item['before'])[:16].replace('\n', '/'),
                                   item['after'].replace('\n', ' / ')))
