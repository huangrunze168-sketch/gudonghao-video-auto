"""按每句话术的情绪在线更换贴纸：官方下载 + 替换素材 + 官方缩放。"""
import json
import os
import sys
from pathlib import Path

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT / 'skills/guzhu-hao/scripts'))
sys.path.insert(0, str(ROOT / 'engine'))
import guzhu_batch as gb
import lyra_cli
from official_materials import execute
from guzhu_timeline import Editor, range_of

os.environ['DSH_LYRA_ALLOW_NETWORK'] = '1'

root = gb.draft_root('.')
folder = sorted([d for d in Path(root).iterdir() if d.name.startswith('guzhu-')],
                key=lambda p: p.stat().st_mtime_ns, reverse=True)[0]
ref = 'local://' + folder.name
print('草稿:', folder.name)

# 每句话术配一个契合情绪的在线贴纸，避免沿用模板里的搞笑表情包
pairs = [
    ('7618101594965478706', '等下班'),
    ('7436961804237933836', '享受独处'),
    ('7215840456385629451', '叹气'),
    ('7436961764689988883', '独处时光'),
    ('7410221196421172480', '静享慢时光'),
]

downloaded = []
for rid, title in pairs:
    result = execute('.', ['material', 'download', '--type', 'sticker', '--resource-id', rid])
    if 'envelope' not in result:
        print('  下载失败 %s: %s' % (rid, str(result.get('error'))[:130]))
        continue
    path = Path(result['envelope']['result']['result']['path'])
    downloaded.append({'id': rid, 'name': title, 'path': str(path)})
print('在线下载成功 %d/%d' % (len(downloaded), len(pairs)))

timeline, source = gb.read_draft_timeline('.', folder)
editor = Editor(timeline)
segments = sorted([s for _t, s in editor.segments()
                   if editor.bucket(s.get('material_id')) == 'stickers'],
                  key=lambda s: range_of(s)[0])
by_id = {m['id']: m for m in timeline['materials']['stickers']}

replaced = 0
for segment, item in zip(segments, downloaded):
    node = by_id.get(segment.get('material_id'))
    if node is None:
        continue
    node['name'] = item['name']
    node['path'] = item['path']
    node['resource_id'] = item['id']
    node['sticker_id'] = item['id']
    node.pop('icon_url', None)
    node.pop('preview_cover_url', None)
    replaced += 1
gb.write_draft_timeline('.', folder, timeline, source)
print('替换贴纸素材 %d 个（段的时间、位置与缩放保持不变）' % replaced)

# 不同来源的贴纸像素差异较大，用官方关键帧把显示尺寸统一回模板基准
for segment in segments:
    try:
        lyra_cli.draft(['keyframe', 'add'], str(root), ref,
                       {'--seg-id': segment['id'], '--animated-property': 'scale',
                        '--points': '0s:0.22x,5s:0.22x'})
        gb._mirror_draft(folder)
    except Exception as error:
        print('  缩放失败 %s: %s' % (segment['id'][:8], str(error)[:100]))

Path('work/guzhu-mingyun-v2/sticker-replacement.json').write_text(
    json.dumps({'draft': folder.name, 'pairs': pairs, 'replaced': replaced},
               ensure_ascii=False, indent=2), encoding='utf-8')
print('完成')
