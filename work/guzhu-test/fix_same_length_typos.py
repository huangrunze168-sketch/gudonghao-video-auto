"""只做等长同音字替换：不改字数、不改分段、不改段结构。

雨雾氛围感模板重建出的 6 段与整句歌词天然对齐，错的只是 ASR 同音字。
等长替换不会破坏模板动画的分段骨架。
"""
import json
import sys
from pathlib import Path

ROOT = Path.cwd()
sys.path[:0] = [str(ROOT / 'skills/guzhu-hao/scripts'), str(ROOT / 'engine')]
import guzhu_batch as gb
from guzhu_timeline import Editor, range_of, retitle

# 官方 ASR 的同音错字 -> 用户歌词原文（长度必须一致）
REPLACEMENTS = [
    ("都不必在身旁", "都不必再审判"),   # 5字 -> 5字
    ("承认有些人只配一段", "承认有些人只陪一段"),  # 11字 -> 11字
]
for old, new in REPLACEMENTS:
    if len(old) != len(new):
        raise RuntimeError("替换前后长度不一致，会破坏分段：%s -> %s" % (old, new))

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
        if len(after.replace('\n', '')) != len(before.replace('\n', '')):
            raise RuntimeError('替换改变了字数，停止')
        retitle(node, after)
        changes.append({'segment': segment['id'][:8], 'before': before.replace('\n', '/'),
                        'after': after.replace('\n', '/'),
                        'range': [int(v) for v in range_of(segment)]})

gb.write_draft_timeline(ROOT, folder, timeline, source)
out = ROOT / 'work/guzhu-buneng-v3'
(out / 'same-length-fix.json').write_text(
    json.dumps(changes, ensure_ascii=False, indent=2), encoding='utf-8')
print('等长替换 %d 处：' % len(changes))
for item in changes:
    print('  %s  %s  ->  %s' % (item['segment'], item['before'], item['after']))
