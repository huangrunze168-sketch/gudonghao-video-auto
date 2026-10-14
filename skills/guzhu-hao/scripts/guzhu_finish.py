"""成片后处理链（只改草稿，最后统一导出一次）。

按 skill 的要求依次处理：
  1. 贴纸替换（在线搜到的表情包）+ 缩放到合适大小
  2. 口播字幕宽度自适应（按最长句）
  3. 歌词段宽度自适应（长句不超出画面）
  4. 口播段真峰值控制
  5. 氛围层：多个低强度特效（全局效果轨）+ 全局调色

用法：python guzhu_finish.py <项目目录名>
"""
import json
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

ROOT = Path.cwd()
sys.path[:0] = [str(ROOT / 'skills/guzhu-hao/scripts'), str(ROOT / 'engine')]
import guzhu_batch as gb
import jypack_render
import lyra_cli
from official_materials import execute
from guzhu_timeline import Editor, range_of, parse_text_content

PROJECT_NAME = sys.argv[1] if len(sys.argv) > 1 else None
if not PROJECT_NAME:
    raise SystemExit('用法: python guzhu_finish.py <项目目录名>')
PROJECT = ROOT / 'work' / PROJECT_NAME
if not PROJECT.is_dir():
    raise SystemExit('项目不存在: %s' % PROJECT)

# ---- 贴纸：逐句情绪对应的在线表情包（每首必须重设） ----
STICKERS = [
    ('7236618118553013565', '哽咽哭哭', '遗憾没说出口'),
    ('7620387011836431678', '发光打伞小猫', '伞还留着人却不见'),
    ('7125428262875991332', '突然安静 猫咪', '逗点变句点'),
    ('7653459436480040216', '忧郁小猫 下雨天', '雨停后没人听了'),
    ('7491547565842763033', '伤心', '评论区留句号'),
]
STICKER_SCALE = 0.5

# ---- 口播字幕：按最长句自适应的基准 ----
SUB_BASE_SCALE = 1.6747     # 19 字恰好占满（实测）
SUB_BASE_CHARS = 19
SUB_TARGET = 0.94

# ---- 歌词：按最长段自适应的基准 ----
LYRIC_TARGET = 0.90         # 歌词目标占宽

# ---- 氛围层 ----
SEGMENT_EFFECT = ('7581434656197741849', '梦幻漏光')
GLOBAL_EFFECTS = [
    ('7685029541189913880', '光斑流动'),
    ('7496779956345654552', '细雨'),
]
INTENSITY = 0.10
ADJUST = {'saturation': 8, 'color-temperature': 6, 'shadow': 5, 'contrast': 4}

PEAK_TARGET_LOUDNESS = -12.0
PEAK_CEILING = -0.5

os_env = 'DSH_LYRA_ALLOW_NETWORK'
import os  # noqa: E402
os.environ[os_env] = '1'

root = gb.draft_root(ROOT)
folder = sorted([d for d in Path(root).iterdir() if d.name.startswith('guzhu-')],
                key=lambda p: p.stat().st_mtime_ns, reverse=True)[0]
ref = 'local://' + folder.name
print('项目 %s，草稿 %s' % (PROJECT_NAME, folder.name))


def measure_width(text):
    """按字数估算相对宽度（等宽近似即可用于比较）。"""
    return len(str(text).replace('\n', ''))


# ============ 1. 贴纸替换 + 缩放 ============
print()
print('== 1. 贴纸 ==')
for rid, title, _why in STICKERS:
    execute(ROOT, ['material', 'download', '--type', 'sticker', '--resource-id', rid])

timeline, _ = gb.read_draft_timeline(ROOT, folder)
editor = Editor(timeline)
old = [s['id'] for _t, s in editor.segments()
       if editor.bucket(s.get('material_id')) == 'stickers']
print('  删除模板预置贴纸 %d 个' % len(old))
for segment_id in old:
    try:
        lyra_cli.draft(['sticker', 'remove'], str(root), ref, {'--seg-id': segment_id})
        gb._mirror_draft(folder)
    except Exception:  # noqa: BLE001
        pass

timeline, _ = gb.read_draft_timeline(ROOT, folder)
editor = Editor(timeline)
groups = sorted([g for g in gb.inspect_template(timeline).groups if g.tts_segment],
                key=lambda g: range_of(g.tts_segment)[0])
if len(groups) != len(STICKERS):
    raise SystemExit('口播组 %d != 贴纸 %d' % (len(groups), len(STICKERS)))
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
    if added:
        lyra_cli.draft(['sticker', 'translate'], str(root), ref,
                       {'--seg-id': added[0]['id'], '--x': '0', '--y': '0.42'})
        gb._mirror_draft(folder)
        print('  放置 %-16s (%s)' % (title[:16], why))

# 统一缩放
def make_scale_group(property_type, scale):
    return {
        'id': str(uuid.uuid4()).upper(),
        'material_id': '',
        'property_type': property_type,
        'keyframe_list': [{
            'id': str(uuid.uuid4()).upper(),
            'left_control': {'x': 0.0, 'y': 0.0},
            'right_control': {'x': 0.0, 'y': 0.0},
            'values': [scale],
        }],
    }


timeline, source = gb.read_draft_timeline(ROOT, folder)
editor = Editor(timeline)
scaled = 0
for _track, segment in editor.segments():
    if editor.bucket(segment.get('material_id')) != 'stickers':
        continue
    kept = [g for g in (segment.get('common_keyframes') or [])
            if 'Scale' not in str(g.get('property_type') or '')]
    segment['common_keyframes'] = kept + [
        make_scale_group('KFTypeScaleX', STICKER_SCALE),
        make_scale_group('KFTypeScaleY', STICKER_SCALE),
    ]
    scaled += 1
gb.write_draft_timeline(ROOT, folder, timeline, source)
print('  贴纸缩放 %.2f（%d 段）' % (STICKER_SCALE, scaled))

# ============ 2. 口播字幕宽度自适应 ============
print()
print('== 2. 口播字幕 ==')
timeline, source = gb.read_draft_timeline(ROOT, folder)
editor = Editor(timeline)
subs = []
for _track, segment in editor.segments():
    node = editor.node(segment.get('material_id')) or {}
    if editor.bucket(segment.get('material_id')) != 'texts':
        continue
    if node.get('type') != 'subtitle':
        continue
    content = parse_text_content(node.get('content')) or {}
    subs.append((segment, content, str(content.get('text') or '')))
if subs:
    longest = max(measure_width(t) for _s, _c, t in subs)
    scale = max(0.8, min(SUB_BASE_SCALE,
                         SUB_BASE_SCALE * SUB_BASE_CHARS / longest * SUB_TARGET / 1.0))
    for segment, _content, _text in subs:
        clip = segment.setdefault('clip', {})
        clip['scale'] = {'x': scale, 'y': scale}
    gb.write_draft_timeline(ROOT, folder, timeline, source)
    print('  最长 %d 字 → scale %.4f（%d 段）' % (longest, scale, len(subs)))

# ============ 3. 歌词宽度（默认不动，只记录） ============
print()
print('== 3. 歌词宽度 ==')
timeline, source = gb.read_draft_timeline(ROOT, folder)
editor = Editor(timeline)
lyrics = []
for _track, segment in editor.segments():
    node = editor.node(segment.get('material_id')) or {}
    if editor.bucket(segment.get('material_id')) != 'texts':
        continue
    if node.get('type') == 'subtitle':
        continue
    content = parse_text_content(node.get('content')) or {}
    lyrics.append((segment, str(content.get('text') or '')))
if lyrics:
    counts = [measure_width(t) for _s, t in lyrics if measure_width(t) > 0]
    longest = max(counts) if counts else 1
    print('  歌词段 %d 个，最长 %d 字' % (len(lyrics), longest))
    print('  注意：**不改歌词段的 clip.scale**——模板的竖排/多色位置由 transform 决定，'
          '整体缩放会把边上的字推出画面（实测左侧竖排被切）。')
    print('  若某模板确实超宽，应换模板而不是缩放。')

# ============ 4. 口播真峰值控制 ============
print()
print('== 4. 峰值控制 ==')
timeline, _ = gb.read_draft_timeline(ROOT, folder)
editor = Editor(timeline)
voices = []
for _track, segment in editor.segments():
    node = editor.node(segment.get('material_id')) or {}
    if str(node.get('type')) == 'text_to_audio':
        voices.append(segment['id'])
import tempfile  # noqa: E402
workspace = Path(tempfile.gettempdir()) / ('guzhu-peak-%s' % uuid.uuid4().hex[:8])
applied = 0
try:
    gb._project_script(ROOT, 'draftediting_runtime.py', ['init', '--workspace', str(workspace)])
    gb._project_script(ROOT, 'draftediting_runtime.py',
                       ['sync', '--workspace', str(workspace), '--ref', ref,
                        '--draft-root', str(root)])
    for segment_id in voices:
        try:
            lyra_cli.draft(['algo', 'loudness-normalize'], str(root), ref,
                           {'--seg-id': segment_id, '--enable': 'true',
                            '--target-loudness': str(PEAK_TARGET_LOUDNESS),
                            '--true-peak-ceiling': str(PEAK_CEILING)},
                           workspace=workspace)
            applied += 1
        except Exception:  # noqa: BLE001
            pass
    if applied:
        gb._mirror_draft(folder)
finally:
    shutil.rmtree(workspace, ignore_errors=True)
print('  口播段 %d/%d 已应用（target %.1f LUFS, ceiling %.1f）'
      % (applied, len(voices), PEAK_TARGET_LOUDNESS, PEAK_CEILING))

# ============ 5. 氛围层 ============
print()
print('== 5. 氛围层 ==')
for rid, name in [SEGMENT_EFFECT] + GLOBAL_EFFECTS:
    execute(ROOT, ['material', 'download', '--type', 'effect', '--resource-id', rid])

timeline, _ = gb.read_draft_timeline(ROOT, folder)
editor = Editor(timeline)
mains = sorted([s for _t, s in editor.segments()
                if editor.bucket(s.get('material_id')) == 'videos'],
               key=lambda s: -range_of(s)[1])
main = mains[0]
main_id = main['id']
main_start, main_dur = range_of(main)
lyra_cli.draft(['video', 'effect', 'add'], str(root), ref,
               {'--seg-id': main_id, '--resource': 'vimo://' + SEGMENT_EFFECT[0]})
gb._mirror_draft(folder)
print('  段特效：%s' % SEGMENT_EFFECT[1])
for rid, name in GLOBAL_EFFECTS:
    try:
        lyra_cli.draft(['effect', 'add'], str(root), ref,
                       {'--resource': 'vimo://' + rid,
                        '--start': '%.6fs' % (main_start / 1e6),
                        '--duration': '%.6fs' % (main_dur / 1e6)})
        gb._mirror_draft(folder)
        print('  全局特效：%s' % name)
    except Exception as error:  # noqa: BLE001
        print('  全局特效 %s 失败：%s' % (name, str(error)[:80]))
for rid, _name in [SEGMENT_EFFECT] + GLOBAL_EFFECTS:
    try:
        lyra_cli.draft(['video', 'effect', 'update'], str(root), ref,
                       {'--seg-id': main_id, '--resource-id': rid,
                        '--params-json': json.dumps({'effects_adjust_intensity': INTENSITY})})
        gb._mirror_draft(folder)
    except Exception:  # noqa: BLE001
        pass
try:
    args = {'--start': '0s',
            '--duration': '%.6fs' % ((main_start + main_dur) / 1e6)}
    for key, value in ADJUST.items():
        args['--' + key] = str(value)
    lyra_cli.draft(['adjust', 'add'], str(root), ref, args)
    gb._mirror_draft(folder)
    print('  全局调色：%s' % ADJUST)
except Exception as error:  # noqa: BLE001
    print('  调色失败：%s' % str(error)[:120])

# ============ 6. 导出 ============
print()
print('== 6. 导出 ==')
produced = max(PROJECT.glob('locate/jypack/*.jypack'), key=lambda p: p.stat().st_mtime_ns)
timeline2, source2 = gb.read_draft_timeline(ROOT, folder)
jypack_id = jypack_render.package_timeline_id(produced)
if timeline2.get('id') != jypack_id:
    timeline2['id'] = jypack_id
    gb.write_draft_timeline(ROOT, folder, timeline2, source2)
OUT = PROJECT / 'final'
if OUT.exists():
    shutil.rmtree(OUT, ignore_errors=True)
result = subprocess.run(
    [sys.executable, str(ROOT / 'engine/jypack_render.py'),
     '--input', str(produced), '--draft-dir', str(folder), '--out', str(OUT),
     '--width', '1280', '--height', '720', '--fps', '30', '--timeout', '1800'],
    capture_output=True, timeout=2400)
print('导出退出码 %s' % result.returncode)
if result.returncode != 0:
    print(result.stderr.decode('utf-8', 'replace')[-300:])
    raise SystemExit(1)
video = OUT / 'render.mp4'
print('成片: %s (%d bytes)' % (video, video.stat().st_size))
