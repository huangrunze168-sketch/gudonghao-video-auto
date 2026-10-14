"""给垫乐加淡出、副歌加淡入，并检查歌词文本（不依赖 native_audio 开关）。"""
import json
import sys
from pathlib import Path

ROOT = Path.cwd()
sys.path[:0] = [str(ROOT / 'skills/guzhu-hao/scripts'), str(ROOT / 'engine')]
import guzhu_batch as gb
import lyra_cli
from guzhu_timeline import Editor, range_of

root = gb.draft_root(ROOT)
folder = sorted([d for d in Path(root).iterdir() if d.name.startswith('guzhu-')],
                key=lambda p: p.stat().st_mtime_ns, reverse=True)[0]
ref = 'local://' + folder.name
print('草稿:', folder.name)

timeline, _ = gb.read_draft_timeline(ROOT, folder)
skeleton = gb.inspect_template(timeline)
report = {'draft': str(folder), 'fades': []}

# 垫乐尾部淡出：口播说完时音乐不是"啪"地断掉
for _track, segment, _mid in skeleton.intro_music:
    lyra_cli.draft(['audio', 'fade'], str(root), ref,
                   {'--seg-id': segment['id'], '--out': '600ms'})
    gb._mirror_draft(folder)
    report['fades'].append({'track': 'intro', 'seg': segment['id'], 'out': '600ms'})

# 副歌淡入 + 结尾淡出
for _track, segment, _mid in skeleton.main_music:
    lyra_cli.draft(['audio', 'fade'], str(root), ref,
                   {'--seg-id': segment['id'], '--in': '500ms', '--out': '1200ms'})
    gb._mirror_draft(folder)
    report['fades'].append({'track': 'main', 'seg': segment['id'],
                            'in': '500ms', 'out': '1200ms'})

# 回读确认
timeline2, _ = gb.read_draft_timeline(ROOT, folder)
editor2 = Editor(timeline2)
report['verify'] = []
for track in timeline2.get('tracks') or []:
    if track.get('type') != 'audio':
        continue
    for segment in track.get('segments') or []:
        node = editor2.node(segment.get('material_id')) or {}
        report['verify'].append({'name': str(node.get('name')),
                                 'range': range_of(segment),
                                 'fade': segment.get('audio_fade')})
print('淡入淡出:')
for item in report['fades']:
    print('  %s' % item)
print()
print('回读验证:')
for item in report['verify']:
    print('  %-26s fade=%s' % (item['name'][:24], item['fade']))

# 顺便列出歌词段文本，准备校正
rows = []
for _t, s in editor2.segments():
    n = editor2.node(s.get('material_id')) or {}
    if editor2.bucket(s.get('material_id')) == 'texts' and n.get('type') != 'subtitle':
        rows.append((range_of(s)[0], gb._recognized_text(n)))
rows.sort()
report['lyrics'] = [{'start_us': st, 'text': tx} for st, tx in rows]
print()
print('歌词段 %d 个:' % len(rows))
for st, tx in rows:
    print('  %7.3f  %s' % (st / 1e6, str(tx).replace(chr(10), ' / ')))

out = ROOT / 'work/guzhu-buneng-v3'
out.mkdir(parents=True, exist_ok=True)
(out / 'fade-and-lyrics.json').write_text(
    json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
