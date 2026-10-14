"""方案 1：保留口播 +8dB 段增益，再叠一道官方真峰值上限（--true-peak-ceiling）。

问题：口播 +8dB 后成片真峰值 +0.1 dBFS，超过 0dBTP。
做法：只对 5 个口播段（text_to_audio）应用官方 `draft algo loudness-normalize`，
带 `--true-peak-ceiling`（官方会为满足上限而降低目标），
背景垫乐与副歌段完全不动，保持三条通道的既有关系。
"""
import json
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

ROOT = Path.cwd()
sys.path[:0] = [str(ROOT / 'skills/guzhu-hao/scripts'), str(ROOT / 'engine')]
import guzhu_batch as gb
import jypack_render
import lyra_cli
from guzhu_timeline import Editor, range_of

TARGET_LOUDNESS = -12.0    # 片头口播目标响度；比 -11 低 1dB 以压住峰值
CEILING = -0.5             # 真峰值上限 dBTP（留余量给 AAC 过冲）
# 实测：本机 11.5.0.14471 的 --true-peak-ceiling 未真正生效
# （设 -0.2 / -0.5 后峰值仍 +0.01 ~ +0.02dB），
# 所以靠降低 --target-loudness 来获得实际余量，效果可复现。

# 可选：python guzhu_peak_ceiling.py <项目目录名>
# 不传时取最近 build 的项目；传了就不会误伤别的项目
PROJECT_ARG = sys.argv[1] if len(sys.argv) > 1 else None


def find_produced_jypack():
    """找 build 阶段产出的 JYPACK（渲染时草稿的 timeline.id 必须与它一致）。"""
    if PROJECT_ARG:
        packs = list((ROOT / 'work' / PROJECT_ARG).glob('locate/jypack/*.jypack'))
        if not packs:
            packs = list((ROOT / 'work' / PROJECT_ARG).glob('**/*.jypack'))
    else:
        packs = []
    if not packs:
        packs = list((ROOT / 'work').glob('guzhu-*/locate/jypack/*.jypack'))
    if not packs:
        packs = list((ROOT / 'work').glob('guzhu-*/**/*.jypack'))
    if not packs:
        raise SystemExit('找不到 build 产出的 JYPACK，请先跑 build')
    return max(packs, key=lambda p: p.stat().st_mtime_ns)


PRODUCED = find_produced_jypack()
OUT = PRODUCED.parents[2] / 'final'

root = gb.draft_root(ROOT)
folder = sorted([d for d in Path(root).iterdir() if d.name.startswith('guzhu-')],
                key=lambda p: p.stat().st_mtime_ns, reverse=True)[0]
ref = 'local://' + folder.name

timeline, _ = gb.read_draft_timeline(ROOT, folder)
editor = Editor(timeline)
voices = []
for _track, segment in editor.segments():
    node = editor.node(segment.get('material_id')) or {}
    if str(node.get('type')) != 'text_to_audio':
        continue
    voices.append(segment['id'])
print('口播段 %d 个：%s' % (len(voices), [v[:8] for v in voices]))

folder_full = Path(gb.draft_root(ROOT)) / folder.name
workspace = Path(tempfile.gettempdir()) / ('guzhu-ceil-%s' % uuid.uuid4().hex[:8])
done = 0
results = []
try:
    gb._project_script(ROOT, 'draftediting_runtime.py', ['init', '--workspace', str(workspace)])
    gb._project_script(ROOT, 'draftediting_runtime.py',
                       ['sync', '--workspace', str(workspace), '--ref', ref,
                        '--draft-root', str(gb.draft_root(ROOT))])
    for segment_id in voices:
        try:
            outcome = lyra_cli.draft(
                ['algo', 'loudness-normalize'], str(gb.draft_root(ROOT)), ref,
                {'--seg-id': segment_id, '--enable': 'true',
                 '--target-loudness': str(TARGET_LOUDNESS),
                 '--true-peak-ceiling': str(CEILING)},
                workspace=workspace)
            done += 1
            payload = (((outcome or {}).get('envelope') or {}).get('result') or {})
            results.append({'segment': segment_id[:8], 'result': str(payload)[:200]})
            print('  %s 已应用 ceiling' % segment_id[:8])
        except Exception as error:  # noqa: BLE001
            print('  %s 失败: %s' % (segment_id[:8], str(error).replace('\n', ' ')[:160]))
    if done:
        gb._mirror_draft(folder_full)
finally:
    shutil.rmtree(workspace, ignore_errors=True)

print('成功 %d / %d 段' % (done, len(voices)))
if not done:
    raise SystemExit('ceiling 未应用到任何口播段')

# 对齐 timeline id 后重导出
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
print('成片: %s' % (OUT / 'render.mp4'))

(OUT / 'ceiling-report.json').write_text(json.dumps(
    {'target_loudness': TARGET_LOUDNESS, 'ceiling': CEILING,
     'voice_segments': len(voices), 'applied': done, 'detail': results},
    ensure_ascii=False, indent=2), encoding='utf-8')
