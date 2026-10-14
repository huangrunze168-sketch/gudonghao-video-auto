"""补正《不再需要答案》歌词（KTV 复古字幕模板识别出的重复字/缺字）。"""
import json
import sys
from pathlib import Path

ROOT = Path.cwd()
sys.path[:0] = [str(ROOT / 'skills/guzhu-hao/scripts'), str(ROOT / 'engine')]
import guzhu_batch as gb
from guzhu_timeline import Editor, range_of, retitle

root = Path(gb.draft_root(ROOT))
folder = sorted([d for d in root.iterdir() if d.name.startswith('guzhu-')],
                key=lambda p: p.stat().st_mtime_ns, reverse=True)[0]
print('草稿:', folder.name)

timeline, source = gb.read_draft_timeline(ROOT, folder)
editor = Editor(timeline)
rows = []
for _track, segment in editor.segments():
    node = editor.node(segment.get('material_id')) or {}
    if editor.bucket(segment.get('material_id')) == 'texts' and node.get('type') != 'subtitle':
        rows.append((range_of(segment)[0], segment, node))
rows.sort(key=lambda row: row[0])

# 按段的时间与歌词原文逐段补正（官方识别把"突然某天"漏成"突然某"、"需要"重复成"需需要"）
fixes = ['突然某天 我不再', '需要答案', '你爱没爱过 都', '不必再审判',
         '那些没说完', '就停在没说完', '把困在门外的', '自己领回身边',
         '突然某天 我不再', '需要答案', '承认有些人只', '陪一段']
if len(rows) != len(fixes):
    raise RuntimeError('歌词段数变化（%d vs %d），停止' % (len(rows), len(fixes)))

changes = []
for (_start, segment, node), text in zip(rows, fixes):
    before = gb._recognized_text(node)
    retitle(node, text)
    changes.append({'id': segment['id'], 'start_us': _start,
                    'before': before, 'after': text})
gb.write_draft_timeline(ROOT, folder, timeline, source)

out = ROOT / 'work/guzhu-buneng-v3'
out.mkdir(parents=True, exist_ok=True)
(out / 'lyrics-correction.json').write_text(
    json.dumps(changes, ensure_ascii=False, indent=2), encoding='utf-8')
print('已补正 %d 段：' % len(changes))
for item in changes:
    flag = '补正' if str(item['before']) != item['after'] else '一致'
    print('  %7.3f  %-4s %-14s -> %s' % (item['start_us'] / 1e6, flag,
                                         str(item['before'])[:12], item['after']))
