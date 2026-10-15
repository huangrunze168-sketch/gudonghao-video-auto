"""诊断：套模板后（不做文本覆盖）草稿里的歌词段结构。

目的：搞清两个问题的根因
  1. 官方识别出的段有多少、哪些是"整句"、哪些是碎片；
  2. 为什么 `_recognized_text` 对某些段会返回 JSON 串（导致之前纠错脚本把 JSON 写进文本）。
只做只读分析，不修改源草稿。
"""
import json
import shutil
import sys
from pathlib import Path

ROOT = Path.cwd()
sys.path[:0] = [str(ROOT / 'skills/guzhu-hao/scripts'), str(ROOT / 'engine')]
import guzhu_batch as gb
import lyra_cli
from guzhu_timeline import Editor, range_of, parse_text_content

import os
os.environ['DSH_LYRA_ALLOW_NETWORK'] = '1'

JYPACK = ROOT / 'work/guzhu-zaijian-v1/locate/jypack/再也不见.jypack'
TEMPLATE = '7602473145622072595'   # 文艺复古
WORK_NAME = 'guzhu-diag-lyrics'
DRAFTS = Path(gb.draft_root(ROOT))
WORK = DRAFTS / WORK_NAME

if not JYPACK.is_file():
    raise SystemExit('找不到 jypack: %s' % JYPACK)

if WORK.exists():
    shutil.rmtree(WORK, ignore_errors=True)
folder, count = gb.install_draft(JYPACK, DRAFTS, WORK_NAME)
print('装包: %s (%d 文件)' % (folder.name, count))
folder = Path(folder)
ref = 'local://' + folder.name

# 找主歌音乐段
timeline, _ = gb.read_draft_timeline(ROOT, folder)
skeleton = gb.inspect_template(timeline)
music = skeleton.main_music[0][1] if skeleton.main_music else None
if music is None:
    raise SystemExit('找不到主歌音乐段')

print('官方识别…')
lyra_cli.lyrics_recognize(str(DRAFTS), ref, language='zh', mode='segment',
                          seg_id=music['id'], timeout=1800)
gb._mirror_draft(folder)

def dump(tag):
    timeline, _ = gb.read_draft_timeline(ROOT, folder)
    editor = Editor(timeline)
    rows = []
    for _track, segment in editor.segments():
        mid = segment.get('material_id')
        if editor.bucket(mid) != 'texts':
            continue
        node = editor.node(mid) or {}
        if node.get('type') == 'subtitle':
            continue
        content = parse_text_content(node.get('content'))
        rows.append({
            'id': segment['id'][:8],
            'range': [round(v / 1e6, 2) for v in range_of(segment)],
            'recognized': str(gb._recognized_text(node))[:40],
            'parsed_text': str((content or {}).get('text'))[:40],
            'content_type': type(node.get('content')).__name__,
            'content_head': str(node.get('content'))[:80],
            'has_words': bool(node.get('words')),
            'styles': len((content or {}).get('styles') or []),
        })
    rows.sort(key=lambda r: r['range'][0])
    print()
    print('===== %s：歌词段 %d 个 =====' % (tag, len(rows)))
    print('%-9s %-15s %-22s %-22s %-7s %s' % ('id', '时间段', 'recognized', 'parsed_text',
                                              'words', 'content类型'))
    for r in rows:
        print('%-9s %-15s %-22s %-22s %-7s %s' % (
            r['id'], '%s-%s' % (r['range'][0], r['range'][1]),
            r['recognized'][:22], r['parsed_text'][:22],
            r['has_words'], r['content_type']))
    # 检查有没有 recognized 是 JSON 的
    bad = [r for r in rows if r['recognized'].startswith('{') or r['content_type'] != 'str']
    print()
    print('内容异常的段: %d 个' % len(bad))
    for r in bad[:5]:
        print('   %s  content_type=%s  head=%s' % (r['id'], r['content_type'],
                                                  r['content_head'][:70]))
    return rows

before = dump('套模板前（官方识别结果）')

print()
print('套用歌词模板 %s …' % TEMPLATE)
timeline, _ = gb.read_draft_timeline(ROOT, folder)
editor = Editor(timeline)
texts = sorted([s for _t, s in editor.segments()
                if editor.bucket(s.get('material_id')) == 'texts'
                and (editor.node(s.get('material_id')) or {}).get('type') != 'subtitle'],
               key=lambda s: range_of(s)[0])
lyra_cli.lyrics_animation_update(str(DRAFTS), ref, texts[0]['id'], 'vimo://' + TEMPLATE)
gb._mirror_draft(folder)

after = dump('套模板后（未做文本覆盖）')

# 保存对比数据
out = ROOT / 'work/guzhu-zaijian-v1/lyrics-structure.json'
out.write_text(json.dumps({'before': before, 'after': after}, ensure_ascii=False, indent=2),
               encoding='utf-8')
print()
print('结构数据已写入 %s' % out)
