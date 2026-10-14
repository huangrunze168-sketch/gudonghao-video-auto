"""对备用库全部歌词模板逐个做视觉验收：套用 → 原生渲染 → 抽帧 → 汇总。

文本质量已在 rebuild-quality.json 测过；本脚本补上"实际画面"这一层：
每个模板渲染完整成片后抽若干帧，供人工/程序检查切字、错位、重叠、观感。
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

os.environ['DSH_LYRA_ALLOW_NETWORK'] = '1'

ROOTDIR = Path(gb.draft_root(ROOT))
BASE = ROOTDIR / 'guzhu-animtest-base'
WORK = ROOTDIR / 'guzhu-visual-work'
OUT = ROOT / 'work/guzhu-templates/visual'
FRAMES = OUT / 'frames'
OUT.mkdir(parents=True, exist_ok=True)
FRAMES.mkdir(parents=True, exist_ok=True)
JYPACK = ROOT / 'work/guzhu-buneng-v3/jypack/不再需要答案.jypack'
FRAME_TIMES = [10, 13, 16, 20, 25]

if not (BASE / 'Timelines').is_dir():
    raise SystemExit('基准草稿不存在，请先运行 test_template_rebuild.py 建立基准')

library = json.loads((ROOT / 'work/guzhu-templates/library/index.json').read_text(encoding='utf-8'))
# 只测文本质量里成功套用的模板（失败的套不上，没有画面可看）
quality = json.loads((ROOT / 'work/guzhu-templates/rebuild-quality.json').read_text(encoding='utf-8'))
targets = {k: v for k, v in quality.items() if v.get('status') == 'ok'}
print('待做视觉验收的模板: %d 个' % len(targets))

results_path = OUT / 'visual-results.json'
results = {}
if results_path.is_file():
    try:
        results = json.loads(results_path.read_text(encoding='utf-8'))
    except ValueError:
        results = {}

for pos, (rid, info) in enumerate(sorted(targets.items()), 1):
    if rid in results and (FRAMES / rid).is_dir():
        continue
    title = info.get('title') or (library.get(rid) or {}).get('title')
    frame_dir = FRAMES / rid
    if frame_dir.exists():
        shutil.rmtree(frame_dir, ignore_errors=True)
    frame_dir.mkdir(parents=True, exist_ok=True)
    render_dir = OUT / 'render' / rid
    if render_dir.exists():
        shutil.rmtree(render_dir, ignore_errors=True)

    if WORK.exists():
        shutil.rmtree(WORK, ignore_errors=True)
    try:
        shutil.copytree(BASE, WORK)
        timeline, _ = gb.read_draft_timeline(ROOT, WORK)
        editor = Editor(timeline)
        texts = sorted([s for _t, s in editor.segments()
                        if editor.bucket(s.get('material_id')) == 'texts'
                        and (editor.node(s.get('material_id')) or {}).get('type') != 'subtitle'],
                       key=lambda s: range_of(s)[0])
        if not texts:
            results[rid] = {'title': title, 'status': 'no-lyrics'}
            continue
        lyra_cli.lyrics_animation_update(str(ROOTDIR), 'local://' + WORK.name,
                                        texts[0]['id'], 'vimo://' + rid)
        gb._mirror_draft(WORK)
        completed = subprocess.run(
            [sys.executable, str(ROOT / 'engine/jypack_render.py'),
             '--input', str(JYPACK), '--draft-dir', str(WORK),
             '--out', str(render_dir), '--width', '1280', '--height', '720',
             '--fps', '30', '--timeout', '1800'],
            capture_output=True, timeout=2400)
        video = render_dir / 'render.mp4'
        if completed.returncode != 0 or not video.is_file():
            results[rid] = {'title': title, 'status': 'render-failed',
                            'error': completed.stderr.decode('utf-8', 'replace')[-200:]}
            print('[%d/%d] %-12s 渲染失败' % (pos, len(targets), title), flush=True)
            continue
        made = []
        for index, second in enumerate(FRAME_TIMES):
            frame = frame_dir / ('f%d.png' % index)
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(second),
                            '-i', str(video), '-frames:v', '1', str(frame)],
                           capture_output=True, timeout=120)
            if frame.is_file():
                made.append(frame.name)
        results[rid] = {'title': title, 'status': 'ok', 'frames': made,
                        'similarity': info.get('similarity'),
                        'segments': info.get('segments'),
                        'overlaps': info.get('overlaps')}
        print('[%d/%d] %-12s 帧=%d' % (pos, len(targets), title, len(made)), flush=True)
    except Exception as error:  # noqa: BLE001
        results[rid] = {'title': title, 'status': 'failed',
                        'error': str(error)[:180].replace('\n', ' ')}
        print('[%d/%d] %-12s 失败: %s' % (pos, len(targets), title, str(error)[:80]), flush=True)
    finally:
        if WORK.exists():
            shutil.rmtree(WORK, ignore_errors=True)
        if render_dir.exists():
            shutil.rmtree(render_dir, ignore_errors=True)
    results_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')

ok = sum(1 for v in results.values() if v.get('status') == 'ok')
print()
print('视觉验收完成：成功 %d / %d' % (ok, len(targets)))
print('截图目录: %s' % FRAMES)
