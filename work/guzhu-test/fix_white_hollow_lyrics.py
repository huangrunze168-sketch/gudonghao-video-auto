"""校正「白色镂空」模板重建出的 35 段歌词（按时间段对齐原文）。"""
import json
import sys
from pathlib import Path

ROOT = Path.cwd()
sys.path[:0] = [str(ROOT / 'skills/guzhu-hao/scripts'), str(ROOT / 'engine')]
import guzhu_batch as gb
from guzhu_timeline import Editor, range_of, retitle

root = gb.draft_root(ROOT)
folder = sorted([d for d in Path(root).iterdir() if d.name.startswith('guzhu-')],
                key=lambda p: p.stat().st_mtime_ns, reverse=True)[0]
timeline, source = gb.read_draft_timeline(ROOT, folder)
editor = Editor(timeline)
rows = []
for _track, segment in editor.segments():
    node = editor.node(segment.get('material_id')) or {}
    if editor.bucket(segment.get('material_id')) == 'texts' and node.get('type') != 'subtitle':
        rows.append((range_of(segment)[0], segment, node))
rows.sort(key=lambda row: row[0])

# 按段落实际顺序对齐《不再需要答案》Chorus 1 的原文，去掉重复字、补回漏字
fixes = ['突然某天', '突然某天', '我不再', '需要答案',
         '你爱没爱过 都', '你爱没爱过 都', '不必再审判', '不必再审判',
         '那些', '那些', '那些', '没说完 就停在', '没说完 就停在',
         '没说完', '没说完', '没说完',
         '把困', '把困', '在门外的', '在门外的', '自己领回', '自己领回', '身边', '身边',
         '突然某天', '我不再需要', '答案',
         '承认', '承认', '有些', '有些', '人只陪一', '人只陪一', '一段', '一段']
if len(rows) != len(fixes):
    raise RuntimeError('段数变化（%d vs %d），停止' % (len(rows), len(fixes)))

changes = []
for (_start, segment, node), text in zip(rows, fixes):
    before = gb._recognized_text(node)
    retitle(node, text)
    changes.append({'id': segment['id'], 'start_us': _start,
                    'before': before, 'after': text})
gb.write_draft_timeline(ROOT, folder, timeline, source)

out = ROOT / 'work/guzhu-buneng-v3'
(out / 'white-hollow-correction.json').write_text(
    json.dumps(changes, ensure_ascii=False, indent=2), encoding='utf-8')
fixed = sum(1 for c in changes if str(c['before']) != c['after'])
print('已校正 %d 段（其中 %d 段有改动）' % (len(changes), fixed))
