"""108 个歌词模板逐个渲染验收：套用 → 原生渲染 → 抽帧 → 汇总。

修复上次 0 帧的问题：jypack_render 要求 --out 是**不存在**的目录。
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
from guzhu_timeline import Editor, range_of, parse_text_content

sys.path.insert(0, str(ROOT / 'engine'))
import jypack_render  # noqa: E402 - 复用它的 timeline id 读取

os.environ['DSH_LYRA_ALLOW_NETWORK'] = '1'

# 渲染器要求草稿的 timeline.id 与 JYPACK 一致，复制出的副本必须对齐这个 id
JYPACK_TIMELINE_ID = jypack_render.package_timeline_id(
    ROOT / 'work/guzhu-buneng-v3/jypack/不再需要答案.jypack')

ROOTDIR = Path(gb.draft_root(ROOT))
BASE = ROOTDIR / 'guzhu-animtest-base'
WORK = ROOTDIR / 'guzhu-full-visual'
JYPACK = ROOT / 'work/guzhu-buneng-v3/jypack/不再需要答案.jypack'
CACHE = Path(os.environ['LOCALAPPDATA']) / 'JianyingPro/User Data/Cache/lyra-cli/material-cache'
FONTDIR = CACHE / 'font'
OUT = ROOT / 'work/guzhu-templates/visual108'
FRAMES = OUT / 'frames'
FRAME_TIMES = [10, 16, 26]

if not (BASE / 'Timelines').is_dir():
    raise SystemExit('基准草稿不存在：%s' % BASE)

# 目标模板：备用库里成功下载的全部模板
library = json.loads((ROOT / 'work/guzhu-templates/library/index.json').read_text(encoding='utf-8'))
targets = {k: v for k, v in library.items() if v.get('download') == 'ok'}
print('待渲染模板 %d 个' % len(targets))

OUT.mkdir(parents=True, exist_ok=True)
FRAMES.mkdir(parents=True, exist_ok=True)
results_path = OUT / 'render-results.json'
results = {}
if results_path.is_file():
    try:
        results = json.loads(results_path.read_text(encoding='utf-8'))
    except ValueError:
        results = {}


def template_font(tid):
    style = next((CACHE / 'lyric_animation' / tid).rglob('LyricStyle.json'), None)
    if style is None:
        return None
    try:
        data = json.loads(style.read_text(encoding='utf-8', errors='replace'))
    except Exception:  # noqa: BLE001
        return None
    font = (data.get('text_style') or {}).get('font_id')
    if isinstance(font, list):
        font = font[0] if font else None
    return str(font) if font else None


def draft_font_of(folder):
    """读草稿里歌词段实际引用的字体 id 与路径。"""
    timeline, _ = gb.read_draft_timeline(ROOT, folder)
    editor = Editor(timeline)
    found = {}
    for _track, segment in editor.segments():
        node = editor.node(segment.get('material_id')) or {}
        if editor.bucket(segment.get('material_id')) != 'texts':
            continue
        if node.get('type') == 'subtitle':
            continue
        content = parse_text_content(node.get('content')) or {}
        for style in content.get('styles') or []:
            f = style.get('font') or {}
            if f.get('id'):
                found.setdefault(str(f['id']), str(f.get('path') or ''))
    return found


for pos, (rid, info) in enumerate(sorted(targets.items()), 1):
    title = info.get('title')
    frame_dir = FRAMES / rid
    if results.get(rid, {}).get('status') == 'ok' and frame_dir.is_dir() \
            and len(list(frame_dir.glob('*.png'))) == len(FRAME_TIMES):
        continue
    if frame_dir.exists():
        shutil.rmtree(frame_dir, ignore_errors=True)
    frame_dir.mkdir(parents=True, exist_ok=True)
    render_dir = OUT / 'render' / rid
    if render_dir.exists():
        shutil.rmtree(render_dir, ignore_errors=True)
    if WORK.exists():
        shutil.rmtree(WORK, ignore_errors=True)

    row = {'title': title, 'template_font': template_font(rid)}
    try:
        shutil.copytree(BASE, WORK)
        # 渲染器按 timeline.id 找草稿：副本必须对齐成 JYPACK 的 id
        timeline0, source0 = gb.read_draft_timeline(ROOT, WORK)
        timeline0['id'] = JYPACK_TIMELINE_ID
        gb.write_draft_timeline(ROOT, WORK, timeline0, source0)
        timeline, _ = gb.read_draft_timeline(ROOT, WORK)
        editor = Editor(timeline)
        texts = sorted([s for _t, s in editor.segments()
                        if editor.bucket(s.get('material_id')) == 'texts'
                        and (editor.node(s.get('material_id')) or {}).get('type') != 'subtitle'],
                       key=lambda s: range_of(s)[0])
        if not texts:
            row['status'] = 'no-lyrics'
            results[rid] = row
            continue
        lyra_cli.lyrics_animation_update(str(ROOTDIR), 'local://' + WORK.name,
                                        texts[0]['id'], 'vimo://' + rid)
        gb._mirror_draft(WORK)
        row['draft_fonts'] = draft_font_of(WORK)
        # --out 必须不存在
        completed = subprocess.run(
            [sys.executable, str(ROOT / 'engine/jypack_render.py'),
             '--input', str(JYPACK), '--draft-dir', str(WORK),
             '--out', str(render_dir), '--width', '960', '--height', '540',
             '--fps', '24', '--timeout', '1800'],
            capture_output=True, timeout=2400)
        video = render_dir / 'render.mp4'
        if completed.returncode != 0 or not video.is_file():
            row['status'] = 'render-failed'
            row['error'] = completed.stderr.decode('utf-8', 'replace')[-200:]
            print('[%d/%d] %-12s 渲染失败' % (pos, len(targets), title), flush=True)
            results[rid] = row
            continue
        made = []
        for index, second in enumerate(FRAME_TIMES):
            frame = frame_dir / ('f%d.png' % index)
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(second),
                            '-i', str(video), '-frames:v', '1', str(frame)],
                           capture_output=True, timeout=120)
            if frame.is_file():
                made.append(frame.name)
        row['status'] = 'ok'
        row['frames'] = made
        row['font_matched'] = (row['template_font'] in (row.get('draft_fonts') or {}))
        print('[%d/%d] %-12s 帧=%d 模板字体=%s 匹配=%s'
              % (pos, len(targets), title, len(made), row['template_font'],
                 row.get('font_matched')), flush=True)
    except Exception as error:  # noqa: BLE001
        row['status'] = 'failed'
        row['error'] = str(error)[:200].replace('\n', ' ')
        print('[%d/%d] %-12s 失败 %s' % (pos, len(targets), title, str(error)[:60]), flush=True)
    finally:
        if WORK.exists():
            shutil.rmtree(WORK, ignore_errors=True)
        if render_dir.exists():
            shutil.rmtree(render_dir, ignore_errors=True)
    results[rid] = row
    results_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')

ok = [v for v in results.values() if v.get('status') == 'ok']
matched = [v for v in ok if v.get('font_matched')]
print()
print('渲染成功 %d / %d；模板字体与草稿字体一致 %d 个'
      % (len(ok), len(targets), len(matched)))
print('截图目录: %s' % FRAMES)
