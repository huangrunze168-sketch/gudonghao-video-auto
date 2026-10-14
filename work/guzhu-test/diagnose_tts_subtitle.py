"""诊断 TTS 口播字幕的样式：字号、字体、宽度是否超出画布。

现象：口播字幕左右被切（如"的时候想全删了 爱的时候又怕手机丢"）。
每首歌话术长度不同，字号必须逐首按最长句重算。
"""
import json
import sys
from pathlib import Path

ROOT = Path.cwd()
sys.path[:0] = [str(ROOT / 'skills/guzhu-hao/scripts'), str(ROOT / 'engine')]
import guzhu_batch as gb
from guzhu_timeline import Editor, range_of, parse_text_content

root = gb.draft_root(ROOT)
folder = sorted([d for d in Path(root).iterdir() if d.name.startswith('guzhu-')],
                key=lambda p: p.stat().st_mtime_ns, reverse=True)[0]
timeline, _ = gb.read_draft_timeline(ROOT, folder)
canvas = timeline.get('canvas_config') or {}
print('草稿 %s' % folder.name)
print('画布: %sx%s (ratio %s)' % (canvas.get('width'), canvas.get('height'),
                                 canvas.get('ratio')))
print()

editor = Editor(timeline)
rows = []
for _track, segment in editor.segments():
    node = editor.node(segment.get('material_id')) or {}
    if editor.bucket(segment.get('material_id')) != 'texts':
        continue
    content = parse_text_content(node.get('content')) or {}
    text = str(content.get('text') or '')
    styles = content.get('styles') or []
    sizes = [s.get('size') for s in styles if isinstance(s, dict)]
    fonts = [(s.get('font') or {}).get('id') for s in styles if isinstance(s, dict)]
    rows.append({
        'type': node.get('type'),
        'text': text,
        'chars': len(text.replace('\n', '')),
        'size': sizes,
        'font': fonts,
        'range': [int(v) for v in range_of(segment)],
        'clip': segment.get('clip'),
    })
rows.sort(key=lambda r: r['range'][0])

print('文字段共 %d 个' % len(rows))
print()
print('%-4s %-9s %-5s %-8s %s' % ('序号', '类型', '字数', '字号', '文本'))
for index, row in enumerate(rows):
    print('%-4d %-9s %-5d %-8s %s' % (index, row['type'], row['chars'],
                                     row['size'], row['text'][:30].replace('\n', '/')))
    if row['clip']:
        print('        clip=%s' % json.dumps(row['clip'], ensure_ascii=False)[:150])

# 找出最长的口播句与所用字号，估算像素宽度
print()
print('=== 口播字幕的字号与文本 ===')
for row in rows:
    if row['text'] and row['chars'] >= 6 and row['type'] != 'lyric':
        print('  字数=%-3d 字号=%-8s %s' % (row['chars'], row['size'], row['text'][:40]))
