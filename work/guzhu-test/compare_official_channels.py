"""用另一条官方通道重建，和我在用通道的渲染结果做像素对比。

剪映 CLI 套歌词动效有两条通道：
  animation add    —— 作用于"已识别的整组歌词"，带 --cover-old（更接近 GUI 的整组应用）
  animation update —— 作用于指定段（本 skill 一直在用）
两者若等价，说明本 skill 的流程没有引入偏差；若有差异，就说明 update 路径漏了什么。
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd()
sys.path[:0] = [str(ROOT / 'skills/guzhu-hao/scripts'), str(ROOT / 'engine')]
import guzhu_batch as gb
import lyra_cli
from guzhu_timeline import Editor, range_of

sys.path.insert(0, str(ROOT / 'engine'))
import jypack_render  # noqa: E402

os.environ['DSH_LYRA_ALLOW_NETWORK'] = '1'

ROOTDIR = Path(gb.draft_root(ROOT))
BASE = ROOTDIR / 'guzhu-animtest-base'
WORK = ROOTDIR / 'guzhu-official-path'
JYPACK = ROOT / 'work/guzhu-buneng-v3/jypack/不再需要答案.jypack'
TEMPLATE = '7413413547289464100'   # 雨雾氛围感
JYPACK_ID = jypack_render.package_timeline_id(JYPACK)
OUT = ROOT / 'work/guzhu-buneng-v3/official-path'

if not (BASE / 'Timelines').is_dir():
    raise SystemExit('缺少基准草稿 %s' % BASE)

if WORK.exists():
    shutil.rmtree(WORK, ignore_errors=True)
shutil.copytree(BASE, WORK)
# 渲染器要求 timeline.id 与 JYPACK 一致
timeline0, source0 = gb.read_draft_timeline(ROOT, WORK)
timeline0['id'] = JYPACK_ID
gb.write_draft_timeline(ROOT, WORK, timeline0, source0)

ref = 'local://' + WORK.name

# 关键：先清掉累积的识别任务，只留一组，否则 animation add 会报
# multiple lyrics recognize tasks found
print('== 先清理识别任务（clear-previous）==')
try:
    timeline_sk, _ = gb.read_draft_timeline(ROOT, WORK)
    skeleton = gb.inspect_template(timeline_sk)
    music = skeleton.main_music[0][1] if skeleton.main_music else None
    if music is None:
        raise RuntimeError('找不到主歌音乐段')
    lyra_cli.lyrics_recognize(str(ROOTDIR), ref, language='zh', mode='segment',
                              seg_id=music['id'], timeout=1800, clear_previous='true')
    gb._mirror_draft(WORK)
    print('  重新识别完成（已清理旧结果）')
except Exception as error:  # noqa: BLE001
    print('  识别失败: %s' % str(error)[:200].replace('\n', ' '))

print('== 通道一：lyrics animation add（整组套用，带 --cover-old）==')
try:
    lyra_cli.draft(['lyrics', 'animation', 'add'], str(ROOTDIR), ref,
                   {'--resource': 'vimo://' + TEMPLATE, '--cover-old': True})
    gb._mirror_draft(WORK)
    print('  animation add 成功')
except Exception as error:  # noqa: BLE001
    print('  animation add 失败: %s' % str(error)[:300].replace('\n', ' '))

# 记录 add 之后的歌词段与字体
timeline, _ = gb.read_draft_timeline(ROOT, WORK)
editor = Editor(timeline)
rows = []
for _t, s in editor.segments():
    node = editor.node(s.get('material_id')) or {}
    if editor.bucket(s.get('material_id')) == 'texts' and node.get('type') != 'subtitle':
        rows.append((range_of(s)[0], gb._recognized_text(node)))
rows.sort()
print('  歌词段 %d 个；前 3 段文本: %s' % (len(rows), [r[1] for r in rows[:3]]))

# 渲染
if OUT.exists():
    shutil.rmtree(OUT, ignore_errors=True)
completed = subprocess.run(
    [sys.executable, str(ROOT / 'engine/jypack_render.py'),
     '--input', str(JYPACK), '--draft-dir', str(WORK), '--out', str(OUT),
     '--width', '1280', '--height', '720', '--fps', '30', '--timeout', '1800'],
    capture_output=True, timeout=2400)
print('  渲染退出码 %s' % completed.returncode)
if completed.returncode != 0:
    print('  %s' % completed.stderr.decode('utf-8', 'replace')[-300:])
    raise SystemExit(1)

official = OUT / 'render.mp4'
mine = ROOT / 'work/guzhu-buneng-v3/font-lock/render.mp4'
print()
print('== 与 update 通道的成片对比 ==')
print('  add 版:    %s (%d bytes)' % (official, official.stat().st_size))
print('  update 版: %s (%d bytes)' % (mine, mine.stat().st_size if mine.is_file() else -1))

# 抽同一批时间点做像素差异
frames = OUT / 'cmp'
frames.mkdir(parents=True, exist_ok=True)
times = [9.5, 12.5, 16.0, 20.0, 26.0]
diffs = []
for second in times:
    a = frames / ('a-%s.png' % second)
    b = frames / ('b-%s.png' % second)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(second), '-i', str(official),
                    '-frames:v', '1', str(a)], capture_output=True)
    if mine.is_file():
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(second), '-i', str(mine),
                        '-frames:v', '1', str(b)], capture_output=True)
    if a.is_file() and b.is_file():
        out = subprocess.run(
            ['ffmpeg', '-v', 'error', '-i', str(a), '-i', str(b),
             '-lavfi', 'psnr', '-f', 'null', '-'],
            capture_output=True)
        text = out.stderr.decode('utf-8', 'replace')
        diffs.append({'t': second, 'psnr': text.strip()[:120]})
        print('  t=%ss  %s' % (second, text.strip()[:100]))

(OUT / 'compare.json').write_text(json.dumps(
    {'template': TEMPLATE, 'add_segments': len(rows),
     'official': str(official), 'mine': str(mine), 'psnr': diffs},
    ensure_ascii=False, indent=2), encoding='utf-8')
print()
print('对比结果已写入 %s' % (OUT / 'compare.json'))
