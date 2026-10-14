"""批量测试备用库模板的歌词重建质量。

对每个模板：在干净草稿副本上套用 → 读重建文本 → 与用户歌词比对。
指标：相似度、重复字、同起点重叠数、段数、总字数。
"""
import difflib
import json
import os
import re
import shutil
import sys
from pathlib import Path

ROOT = Path.cwd()
sys.path[:0] = [str(ROOT / 'skills/guzhu-hao/scripts'), str(ROOT / 'engine')]
import guzhu_batch as gb
import lyra_cli
from guzhu_timeline import Editor, range_of

os.environ['DSH_LYRA_ALLOW_NETWORK'] = '1'

ROOTDIR = Path(gb.draft_root(ROOT))
BASE = ROOTDIR / 'guzhu-animtest-base'
WORK = ROOTDIR / 'guzhu-animtest-work'
OUT = ROOT / 'work/guzhu-templates'

LYRICS = ROOT / 'work/guzhu-test/lyrics-buneng.txt'
LINES, _CHORUS = gb.__dict__['parse_lyric_lines'](str(LYRICS)) if 'parse_lyric_lines' in gb.__dict__ else (None, None)
if LINES is None:
    from guzhu_lyrics import parse_lyric_lines
    LINES, _CHORUS = parse_lyric_lines(str(LYRICS))

# 只比对选段覆盖到的那部分歌词（Chorus 1 起）
TARGET = re.sub(r'\s+', '', ''.join(LINES[12:19]))
print('目标歌词（选段区间）: %s' % TARGET[:60])


def squeeze(value):
    return re.sub(r'\s+', '', str(value or ''))


def evaluation(folder):
    timeline, _ = gb.read_draft_timeline(ROOT, folder)
    editor = Editor(timeline)
    rows, bad = [], 0
    for _track, segment in editor.segments():
        node = editor.node(segment.get('material_id')) or {}
        if editor.bucket(segment.get('material_id')) != 'texts':
            continue
        if node.get('type') == 'subtitle':
            continue
        text = str(gb._recognized_text(node))
        if '{' in text or 'styles' in text:
            bad += 1
            continue
        rows.append((range_of(segment)[0], squeeze(text)))
    rows.sort()
    joined = ''.join(text for _s, text in rows)
    starts = {}
    for start, _text in rows:
        key = round(start / 1000)
        starts[key] = starts.get(key, 0) + 1
    overlaps = sum(1 for v in starts.values() if v > 1)
    dup_pairs = sum(1 for ch in '我你在的说了就门外领回' if ch * 2 in joined)
    matcher = difflib.SequenceMatcher(None, joined, TARGET, autojunk=False)
    return {
        'segments': len(rows), 'chars': len(joined), 'bad_json': bad,
        'overlaps': overlaps, 'dup_pairs': dup_pairs,
        'similarity': round(matcher.ratio(), 4),
        'joined_head': joined[:70],
    }


library = json.loads((OUT / 'library/index.json').read_text(encoding='utf-8'))
ready = {k: v for k, v in library.items() if v.get('download') == 'ok'}
print('待测模板 %d 个' % len(ready))

# 准备基准草稿：装包 + **官方歌词识别**（只做一次）
if not (BASE / 'Timelines').is_dir():
    if BASE.exists():
        shutil.rmtree(BASE)
    jypack = ROOT / 'work/guzhu-buneng-v3/jypack/不再需要答案.jypack'
    folder, count = gb.install_draft(jypack, ROOTDIR, 'guzhu-animtest-base')
    print('基准草稿: %s (%d 文件)' % (folder.name, count))
    BASE = Path(folder)
    # 必须先识别，否则没有歌词段，套模板必然 no-lyrics-segment
    timeline, _ = gb.read_draft_timeline(ROOT, BASE)
    skeleton = gb.inspect_template(timeline)
    music = skeleton.main_music[0][1] if skeleton.main_music else None
    if music is None:
        raise RuntimeError('基准草稿里没有主歌音乐段')
    lyra_cli.lyrics_recognize(str(ROOTDIR), 'local://' + BASE.name,
                              language='zh', mode='segment', seg_id=music['id'],
                              timeout=1800)
    gb._mirror_draft(BASE)
    probe_timeline, _ = gb.read_draft_timeline(ROOT, BASE)
    probe_editor = Editor(probe_timeline)
    got = sum(1 for _t, s in probe_editor.segments()
              if probe_editor.bucket(s.get('material_id')) == 'texts'
              and (probe_editor.node(s.get('material_id')) or {}).get('type') != 'subtitle')
    print('基准草稿识别出歌词段: %d' % got)
    if not got:
        raise RuntimeError('基准草稿识别后仍没有歌词段，停止')

results = {}
if (OUT / 'rebuild-quality.json').is_file():
    try:
        results = json.loads((OUT / 'rebuild-quality.json').read_text(encoding='utf-8'))
    except ValueError:
        results = {}

for pos, (rid, info) in enumerate(sorted(ready.items()), 1):
    if rid in results:
        continue
    title = info.get('title')
    if WORK.exists():
        shutil.rmtree(WORK, ignore_errors=True)
    shutil.copytree(BASE, WORK)
    ref = 'local://' + WORK.name
    try:
        timeline, _ = gb.read_draft_timeline(ROOT, WORK)
        editor = Editor(timeline)
        texts = sorted([s for _t, s in editor.segments()
                        if editor.bucket(s.get('material_id')) == 'texts'
                        and (editor.node(s.get('material_id')) or {}).get('type') != 'subtitle'],
                       key=lambda s: range_of(s)[0])
        if not texts:
            results[rid] = {'title': title, 'status': 'no-lyrics-segment'}
            continue
        lyra_cli.lyrics_animation_update(str(ROOTDIR), ref, texts[0]['id'], 'vimo://' + rid)
        gb._mirror_draft(WORK)
        row = evaluation(WORK)
        row.update({'title': title, 'status': 'ok'})
        results[rid] = row
        print('[%d/%d] %-20s %-12s 相似=%.3f 段=%d 重叠=%d 重复=%d'
              % (pos, len(ready), rid, title, row['similarity'], row['segments'],
                 row['overlaps'], row['dup_pairs']), flush=True)
    except Exception as error:  # noqa: BLE001
        results[rid] = {'title': title, 'status': 'failed',
                        'error': str(error)[:180].replace('\n', ' ')}
        print('[%d/%d] %-20s %-12s 失败' % (pos, len(ready), rid, title), flush=True)
    (OUT / 'rebuild-quality.json').write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')

shutil.rmtree(WORK, ignore_errors=True)
ok = [v for v in results.values() if v.get('status') == 'ok']
ok.sort(key=lambda v: (-v['similarity'], v['dup_pairs'], v['overlaps']))
print()
print('完成 %d 个（成功 %d）' % (len(results), len(ok)))
print()
print('== 重建最准确的 20 个 ==')
for v in ok[:20]:
    print('  相似=%.3f 段=%-3d 重叠=%d 重复=%d  %-22s %s'
          % (v['similarity'], v['segments'], v['overlaps'], v['dup_pairs'],
             v.get('title'), v.get('joined_head', '')[:24]))
