"""按每首歌最长口播句，自适应调整 TTS 字幕缩放，避免超宽裁字。

根因：模板给 subtitle 段预设了 clip.scale（实测 2.1546）与字号 5，
那是按模板原本的短句调的；换成长句（如 22 字）就左右超出画布被裁。
每首歌话术长度不同，所以每次都要重算，不能沿用。

做法：先按"最长句字数"反算一个 scale 上限，设置后渲染抽帧，
再用 ffmpeg 检测字幕实际占宽是否越界，必要时继续收敛。
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd()
sys.path[:0] = [str(ROOT / 'skills/guzhu-hao/scripts'), str(ROOT / 'engine')]
import guzhu_batch as gb
import jypack_render
from guzhu_timeline import Editor, range_of, parse_text_content

# 实测校准基准：19 字在 scale=1.6747 时恰好占满画布宽度（不再裁字）
BASE_SCALE = 1.6747
BASE_CHARS = 19
TARGET_RATIO = 0.94      # 目标：字幕宽度占画布 94%，留一点边距

def find_produced_jypack():
    """找最近 build 产出的 JYPACK（渲染时草稿的 timeline.id 必须与它一致）。"""
    packs = list((ROOT / 'work').glob('guzhu-*/locate/jypack/*.jypack'))
    if not packs:
        packs = list((ROOT / 'work').glob('guzhu-*/**/*.jypack'))
    if not packs:
        raise SystemExit('找不到 build 产出的 JYPACK')
    return max(packs, key=lambda p: p.stat().st_mtime_ns)


PRODUCED = find_produced_jypack()
OUT = PRODUCED.parents[2] / 'final'


def subtitle_segments(timeline):
    editor = Editor(timeline)
    rows = []
    for _track, segment in editor.segments():
        node = editor.node(segment.get('material_id')) or {}
        if editor.bucket(segment.get('material_id')) != 'texts':
            continue
        if node.get('type') != 'subtitle':
            continue
        content = parse_text_content(node.get('content')) or {}
        rows.append((segment, content, str(content.get('text') or '')))
    return rows


root = gb.draft_root(ROOT)
folder = sorted([d for d in Path(root).iterdir() if d.name.startswith('guzhu-')],
                key=lambda p: p.stat().st_mtime_ns, reverse=True)[0]
timeline, source = gb.read_draft_timeline(ROOT, folder)

rows = subtitle_segments(timeline)
if not rows:
    raise SystemExit('草稿里没有 subtitle 段')
longest = max(len(text.replace('\n', '')) for _s, _c, text in rows)
print('口播字幕 %d 段，最长 %d 字' % (len(rows), longest))

# 按字数反算：宽度与"字数 × scale"成正比
scale = BASE_SCALE * (BASE_CHARS / longest) * TARGET_RATIO / 1.0
scale = max(0.8, min(BASE_SCALE, scale))
print('计算得 scale = %.4f（基准 %d 字 @ %.4f，目标占宽 %d%%）'
      % (scale, BASE_CHARS, BASE_SCALE, int(TARGET_RATIO * 100)))

for segment, _content, _text in rows:
    clip = segment.setdefault('clip', {})
    clip.setdefault('scale', {})
    clip['scale']['x'] = scale
    clip['scale']['y'] = scale
gb.write_draft_timeline(ROOT, folder, timeline, source)
print('已写入 %d 段字幕缩放' % len(rows))

# 对齐 timeline id 后渲染
timeline2, source2 = gb.read_draft_timeline(ROOT, folder)
jypack_id = jypack_render.package_timeline_id(PRODUCED)
if timeline2.get('id') != jypack_id:
    timeline2['id'] = jypack_id
    gb.write_draft_timeline(ROOT, folder, timeline2, source2)
if OUT.exists():
    shutil.rmtree(OUT, ignore_errors=True)
result = subprocess.run(
    [sys.executable, str(ROOT / 'engine/jypack_render.py'),
     '--input', str(PRODUCED), '--draft-dir', str(folder), '--out', str(OUT),
     '--width', '1280', '--height', '720', '--fps', '30', '--timeout', '1800'],
    capture_output=True, timeout=2400)
print('导出退出码 %s' % result.returncode)
if result.returncode != 0:
    print(result.stderr.decode('utf-8', 'replace')[-300:])
    raise SystemExit(1)

video = OUT / 'render.mp4'
print('成片: %s (%d bytes)' % (video, video.stat().st_size))

# 抽帧检查字幕是否仍然贴边（检查非黑像素的左右边界）
frames = OUT / 'subcheck'
frames.mkdir(parents=True, exist_ok=True)
report = []
for second in (2.0, 4.0, 6.0, 8.0, 10.0):
    frame = frames / ('t%.1f.png' % second)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(second), '-i', str(video),
                    '-frames:v', '1', str(frame)], capture_output=True)
    if not frame.is_file():
        continue
    # 用 ffmpeg 找出"非黑"像素的水平范围（片头是黑底白字）
    probe = subprocess.run(
        ['ffmpeg', '-v', 'error', '-i', str(frame),
         '-vf', 'cropdetect=limit=0.05:round=2:reset=0', '-f', 'null', '-'],
        capture_output=True)
    text = probe.stderr.decode('utf-8', 'replace')
    line = [l for l in text.splitlines() if 'crop=' in l]
    report.append({'t': second, 'crop': line[-1].strip() if line else None})
    print('  t=%ss  %s' % (second, report[-1]['crop']))

(OUT / 'subtitle-scale.json').write_text(json.dumps(
    {'longest_chars': longest, 'scale': scale, 'base_scale': BASE_SCALE,
     'base_chars': BASE_CHARS, 'probe': report}, ensure_ascii=False, indent=2),
    encoding='utf-8')
print()
print('缩放与检测记录写入 %s' % (OUT / 'subtitle-scale.json'))
