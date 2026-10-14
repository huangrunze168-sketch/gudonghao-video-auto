"""按这首歌每句话术的情绪，用官方在线贴纸替换模板自带的本地贴纸。"""
import json
import os
import sys
from pathlib import Path

ROOT = Path.cwd()
sys.path[:0] = [str(ROOT / 'skills/guzhu-hao/scripts'), str(ROOT / 'engine')]
import guzhu_batch as gb
import lyra_cli
from official_materials import execute
from guzhu_timeline import Editor, range_of

os.environ['DSH_LYRA_ALLOW_NETWORK'] = '1'

root = gb.draft_root(ROOT)
folder = Path(root) / 'guzhu-01'
ref = 'local://guzhu-01'

# 按这首歌的歌词气质重新选的在线贴纸，不是上一首那一批，也不是本地贴纸池。
pairs = [
    ('7537971070951918873', '无奈'),
    ('7563857958946524440', '无语无奈'),
    ('7266054014586981692', '一半释然'),
    ('7141246767634369826', '想开了'),
    ('7307617907427511563', '评论区留言吧'),
]

report = {'draft': str(folder), 'pairs': pairs, 'added': [], 'downloads': []}
for rid, _name in pairs:
    r = execute(ROOT, ['material', 'download', '--type', 'sticker', '--resource-id', rid])
    if 'envelope' not in r:
        raise RuntimeError('在线贴纸下载失败 %s: %s' % (rid, r.get('error')))
    report['downloads'].append({'id': rid, 'path': r['envelope']['result']['result']['path']})

timeline, _ = gb.read_draft_timeline(ROOT, folder)
editor = Editor(timeline)
old = [s for _t, s in editor.segments()
       if editor.bucket(s.get('material_id')) == 'stickers']
groups = sorted([g for g in gb.inspect_template(timeline).groups if g.tts_segment],
                key=lambda g: range_of(g.tts_segment)[0])
if len(groups) != len(pairs):
    raise RuntimeError('口播组数 %d 与贴纸数 %d 不一致' % (len(groups), len(pairs)))

# 清掉模板自带的本地贴纸，逐组按该句时长加官方在线贴纸
for segment in old:
    lyra_cli.draft(['sticker', 'remove'], str(root), ref, {'--seg-id': segment['id']})
    gb._mirror_draft(folder)

for group, (rid, name) in zip(groups, pairs):
    start, duration = range_of(group.tts_segment)
    timeline, _ = gb.read_draft_timeline(ROOT, folder)
    editor = Editor(timeline)
    before = {s['id'] for _t, s in editor.segments()
              if editor.bucket(s.get('material_id')) == 'stickers'}
    lyra_cli.draft(['sticker', 'add'], str(root), ref,
                   {'--resource': 'vimo://' + rid,
                    '--start': '%.6fs' % (start / 1e6),
                    '--duration': '%.6fs' % (duration / 1e6)})
    gb._mirror_draft(folder)
    timeline, _ = gb.read_draft_timeline(ROOT, folder)
    editor = Editor(timeline)
    added = [s for _t, s in editor.segments()
             if editor.bucket(s.get('material_id')) == 'stickers' and s['id'] not in before]
    if len(added) != 1:
        raise RuntimeError('新增贴纸段数量异常：%d' % len(added))
    sid = added[0]['id']
    lyra_cli.draft(['sticker', 'translate'], str(root), ref,
                   {'--seg-id': sid, '--x': '0', '--y': '0.42'})
    gb._mirror_draft(folder)
    lyra_cli.draft(['keyframe', 'add'], str(root), ref,
                   {'--seg-id': sid, '--animated-property': 'scale',
                    '--points': '0s:0.22x,%.6fs:0.22x' % (duration / 1e6)})
    gb._mirror_draft(folder)
    report['added'].append({'name': name, 'resource_id': rid, 'segment': sid,
                            'start_us': start, 'duration_us': duration})

out = ROOT / 'work/guzhu-buneng-v2'
out.mkdir(parents=True, exist_ok=True)
(out / 'stickers-online.json').write_text(
    json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print('已按新话术情绪替换 %d 组在线贴纸：' % len(report['added']))
for item in report['added']:
    print('  %-14s %7.3fs  %s' % (item['name'], item['start_us'] / 1e6, item['resource_id']))
