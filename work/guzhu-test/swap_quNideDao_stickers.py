"""把片头贴纸换成这首歌在线搜到的（每首必须重新设计，不能沿用上一首）。

修复点：批次里的 `media.stickers: "auto"` 会沿用模板预置贴纸（实测长期是同一批
二哈/猫和老鼠），导致两首成片贴纸一模一样。这里删掉旧贴纸，按本首歌的词情绪
用在线搜到的表情包逐句替换。
"""
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

OUT_DIR = ROOT / 'work/guzhu-quNideDao-v1'

# 逐句贴纸：按《去你的岛》每句话术的情绪在线搜到的猫狗表情包
STICKERS = [
    ('7026294368722013471', '哭喊找妈妈 猫咪表情包', '告别来不及说'),
    ('7066408200244858115', '想你', '把话藏进梦里'),
    ('7027116380591901989', '乖巧微笑', '钥匙攥在自己手里'),
    ('7206704173629410616', '闭眼睡觉蓝猫', '岛上没有白天'),
    ('7006666235559562510', '小猫求抱抱', '评论区留个句号'),
]

root = gb.draft_root(ROOT)
folder = sorted([d for d in Path(root).iterdir() if d.name.startswith('guzhu-')],
                key=lambda p: p.stat().st_mtime_ns, reverse=True)[0]
ref = 'local://' + folder.name
print('草稿:', folder.name)

# 先把用到的贴纸下载到官方缓存
for rid, title, _why in STICKERS:
    outcome = execute(ROOT, ['material', 'download', '--type', 'sticker',
                             '--resource-id', rid])
    print('  下载 %-22s %s' % (title[:22], outcome.get('status')))

# 删除模板预置的旧贴纸
timeline, _ = gb.read_draft_timeline(ROOT, folder)
editor = Editor(timeline)
old = [s['id'] for _t, s in editor.segments()
       if editor.bucket(s.get('material_id')) == 'stickers']
print('删除旧贴纸 %d 个' % len(old))
for segment_id in old:
    try:
        lyra_cli.draft(['sticker', 'remove'], str(root), ref, {'--seg-id': segment_id})
        gb._mirror_draft(folder)
    except Exception as error:  # noqa: BLE001
        print('    删除 %s 失败: %s' % (segment_id[:8], str(error)[:80]))

# 按口播组逐句加新贴纸
timeline, _ = gb.read_draft_timeline(ROOT, folder)
editor = Editor(timeline)
groups = sorted([g for g in gb.inspect_template(timeline).groups if g.tts_segment],
                key=lambda g: range_of(g.tts_segment)[0])
print('口播组 %d 个，贴纸 %d 个' % (len(groups), len(STICKERS)))
if len(groups) != len(STICKERS):
    raise SystemExit('口播组与贴纸数量不一致')

placed = []
for group, (rid, title, why) in zip(groups, STICKERS):
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
    if not added:
        print('  %s 未加入' % title)
        continue
    segment_id = added[0]['id']
    lyra_cli.draft(['sticker', 'translate'], str(root), ref,
                   {'--seg-id': segment_id, '--x': '0', '--y': '0.42'})
    gb._mirror_draft(folder)
    placed.append({'title': title, 'why': why, 'segment': segment_id, 'start_us': start})
    print('  已放置 %-22s (%s)' % (title[:22], why))

print()
print('新贴纸 %d 个' % len(placed))
