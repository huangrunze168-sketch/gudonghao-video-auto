"""TTS 口播再抬 3dB（段音量 +3dB -> +6dB），并复核音轨没有重复。"""
import json
import sys
from pathlib import Path

ROOT = Path.cwd()
sys.path[:0] = [str(ROOT / 'skills/guzhu-hao/scripts'), str(ROOT / 'engine')]
import guzhu_batch as gb
import lyra_cli
from guzhu_timeline import Editor, range_of

root = gb.draft_root(ROOT)
folder = Path(root) / 'guzhu-01'
ref = 'local://guzhu-01'
lines = ['有没有下班到家', '却在楼下多站几分钟', '不是不想回家',
         '只是想把自己还给自己', '懂这首歌的评论区留个句号']

timeline, _ = gb.read_draft_timeline(ROOT, folder)
editor = Editor(timeline)
targets = []
for _track, segment in editor.segments():
    node = editor.node(segment.get('material_id')) or {}
    if (editor.bucket(segment.get('material_id')) == 'audios'
            and str(node.get('name')) in lines):
        targets.append(segment['id'])
if len(targets) != 5:
    raise RuntimeError('TTS 段数不是 5，停止')

for segment_id in targets:
    lyra_cli.draft(['audio', 'volume'], str(root), ref,
                   {'--seg-id': segment_id, '--db': '6'})
    gb._mirror_draft(folder)

# 复核：读回真实音量，并检查同轨是否有重叠
timeline2, _ = gb.read_draft_timeline(ROOT, folder)
editor2 = Editor(timeline2)
report = {'tts': [], 'overlaps': []}
for track in timeline2.get('tracks') or []:
    if track.get('type') != 'audio':
        continue
    rows = []
    for segment in track.get('segments') or []:
        node = editor2.node(segment.get('material_id')) or {}
        start, duration = range_of(segment)
        rows.append((start, duration, segment['id'][:8], str(node.get('name'))))
        if str(node.get('name')) in lines:
            report['tts'].append({'name': str(node.get('name')), 'start_us': start,
                                  'duration_us': duration, 'volume': segment.get('volume')})
    rows.sort()
    for index in range(1, len(rows)):
        previous_end = rows[index - 1][0] + rows[index - 1][1]
        if rows[index][0] < previous_end:
            report['overlaps'].append({'track': track.get('id'), 'a': rows[index - 1][2],
                                       'b': rows[index][2],
                                       'overlap_us': previous_end - rows[index][0]})

(report_path := (ROOT / 'work/guzhu-mingyun-v3' / 'tts-gain.json')).write_text(
    json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print('TTS 音量复核：')
for item in report['tts']:
    print('  %-22s vol=%.4f (%.1fdB)' % (item['name'], item['volume'],
                                         20 * __import__('math').log10(item['volume'])))
print('同轨重叠：%d 处' % len(report['overlaps']))
