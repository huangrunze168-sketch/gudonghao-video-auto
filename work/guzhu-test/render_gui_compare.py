"""用「雨雾氛围感」渲染《有一些瞬间 我在命运之外》，与用户提供的官方截图对比。

用户的截图来自剪映 GUI：橙色行「有一些瞬间我」+ 白色行「在命运之外」。
这里用同一个模板跑同素材，抽帧并排比对，验证 CLI 输出是否与 GUI 一致。
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
import jypack_render  # noqa: E402

os.environ['DSH_LYRA_ALLOW_NETWORK'] = '1'

ROOTDIR = Path(gb.draft_root(ROOT))
JYPACK = ROOT / 'work/guzhu-mingyun/jypack/有一些瞬间_我在命运之外.jypack'
WORK = ROOTDIR / 'guzhu-cmp-gui'
TEMPLATE = '7413413547289464100'   # 雨雾氛围感（与用户截图同款）
OUT = ROOT / 'work/guzhu-templates/gui-compare'

if not JYPACK.is_file():
    raise SystemExit('找不到 jypack: %s' % JYPACK)
JYPACK_ID = jypack_render.package_timeline_id(JYPACK)

if WORK.exists():
    shutil.rmtree(WORK, ignore_errors=True)
folder, count = gb.install_draft(JYPACK, ROOTDIR, 'guzhu-cmp-gui')
WORK = Path(folder)
print('装包完成: %s (%d 文件)' % (WORK.name, count))

# 对齐 timeline id 供渲染器识别
timeline0, source0 = gb.read_draft_timeline(ROOT, WORK)
timeline0['id'] = JYPACK_ID
gb.write_draft_timeline(ROOT, WORK, timeline0, source0)

# 看包里是否自带歌词
timeline, _ = gb.read_draft_timeline(ROOT, WORK)
editor = Editor(timeline)
texts = []
for _t, s in editor.segments():
    node = editor.node(s.get('material_id')) or {}
    if editor.bucket(s.get('material_id')) == 'texts' and node.get('type') != 'subtitle':
        content = parse_text_content(node.get('content')) or {}
        texts.append((range_of(s)[0], str(content.get('text') or '')))
texts.sort()
print('包里歌词段: %d 个' % len(texts))
for start, text in texts[:6]:
    print('   %7.3f  %s' % (start / 1e6, text[:26]))

ref = 'local://' + WORK.name
if texts:
    print()
    print('== 套用雨雾氛围感 ==')
    # 用首段 id 套用（与该 skill 既有流程一致）
    timeline, _ = gb.read_draft_timeline(ROOT, WORK)
    editor = Editor(timeline)
    first = sorted([s for _t, s in editor.segments()
                    if editor.bucket(s.get('material_id')) == 'texts'
                    and (editor.node(s.get('material_id')) or {}).get('type') != 'subtitle'],
                   key=lambda s: range_of(s)[0])[0]
    lyra_cli.lyrics_animation_update(str(ROOTDIR), ref, first['id'], 'vimo://' + TEMPLATE)
    gb._mirror_draft(WORK)
    print('  套用完成')

# 渲染
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
    print(completed.stderr.decode('utf-8', 'replace')[-400:])
    raise SystemExit(1)

# 全片抽帧，找含"有一些瞬间"那句的位置
frames = OUT / 'frames'
frames.mkdir(parents=True, exist_ok=True)
made = []
for index in range(0, 40):
    second = index * 1.5
    frame = frames / ('t%04.1f.png' % second)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(second), '-i', str(video),
                    '-frames:v', '1', str(frame)], capture_output=True)
    if frame.is_file():
        made.append(str(frame))
print('抽帧 %d 张 -> %s' % (len(made), frames))
print('产物: %s' % video)
(OUT / 'info.json').write_text(json.dumps(
    {'jypack': str(JYPACK), 'template': TEMPLATE, 'draft': str(WORK),
     'video': str(video), 'frames': made, 'segments': len(texts)},
    ensure_ascii=False, indent=2), encoding='utf-8')
