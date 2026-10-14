"""渲染 animation add 通道（官方式整组套用）的结果，与 update 通道逐帧对比。

add 通道此前不可用，原因是草稿累积了多组 lyrics/subtitle 任务记录；
清理后已可用。这里渲染 add 版，与 update 版（font-lock 那版）做像素对比，
用客观指标回答"两条官方通道是否等价"。
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
from guzhu_timeline import Editor, range_of

sys.path.insert(0, str(ROOT / 'engine'))
import jypack_render  # noqa: E402

ROOTDIR = Path(gb.draft_root(ROOT))
SRC = ROOTDIR / 'guzhu-01'
WORK = ROOTDIR / 'guzhu-add-version'
JYPACK = ROOT / 'work/guzhu-buneng-v3/jypack/不再需要答案.jypack'
JYPACK_ID = jypack_render.package_timeline_id(JYPACK)
OUT = ROOT / 'work/guzhu-buneng-v3/add-version'

if not (SRC / 'Timelines').is_dir():
    raise SystemExit('找不到源草稿 %s' % SRC)

if WORK.exists():
    shutil.rmtree(WORK, ignore_errors=True)
shutil.copytree(SRC, WORK)
timeline0, source0 = gb.read_draft_timeline(ROOT, WORK)
timeline0['id'] = JYPACK_ID
gb.write_draft_timeline(ROOT, WORK, timeline0, source0)

timeline, _ = gb.read_draft_timeline(ROOT, WORK)
editor = Editor(timeline)
texts = sorted([s for _t, s in editor.segments()
                if editor.bucket(s.get('material_id')) == 'texts'
                and (editor.node(s.get('material_id')) or {}).get('type') != 'subtitle'],
               key=lambda s: range_of(s)[0])
print('add 版草稿歌词段: %d 个' % len(texts))

if OUT.exists():
    shutil.rmtree(OUT, ignore_errors=True)
completed = subprocess.run(
    [sys.executable, str(ROOT / 'engine/jypack_render.py'),
     '--input', str(JYPACK), '--draft-dir', str(WORK), '--out', str(OUT / 'render'),
     '--width', '1280', '--height', '720', '--fps', '30', '--timeout', '1800'],
    capture_output=True, timeout=2400)
print('渲染退出码 %s' % completed.returncode)
video = OUT / 'render' / 'render.mp4'
if completed.returncode != 0 or not video.is_file():
    print(completed.stderr.decode('utf-8', 'replace')[-300:])
    raise SystemExit(1)

mine_update = ROOT / 'work/guzhu-buneng-v3/font-lock/render.mp4'
print()
print('add 版   : %d bytes' % video.stat().st_size)
if mine_update.is_file():
    print('update 版: %d bytes' % mine_update.stat().st_size)
print()
frames = OUT / 'cmp'
frames.mkdir(parents=True, exist_ok=True)
report = []
for second in (9.5, 12.5, 16.0, 20.0, 26.0):
    a = frames / ('add-%s.png' % second)
    b = frames / ('upd-%s.png' % second)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(second), '-i', str(video),
                    '-frames:v', '1', str(a)], capture_output=True)
    psnr = None
    if mine_update.is_file():
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(second), '-i', str(mine_update),
                        '-frames:v', '1', str(b)], capture_output=True)
        if a.is_file() and b.is_file():
            res = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(a), '-i', str(b),
                                  '-lavfi', 'psnr', '-f', 'null', '-'], capture_output=True)
            text = res.stderr.decode('utf-8', 'replace').strip()
            psnr = text
            print('  t=%ss  %s' % (second, text[:110]))
    report.append({'t': second, 'psnr': psnr})

(OUT / 'compare.json').write_text(json.dumps(
    {'add_version': str(video), 'update_version': str(mine_update), 'psnr': report},
    ensure_ascii=False, indent=2), encoding='utf-8')
print()
print('对比写入 %s' % (OUT / 'compare.json'))
