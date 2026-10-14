"""找出与纠错后草稿匹配的 JYPACK（按 timeline id），然后渲染成片。"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd()
sys.path[:0] = [str(ROOT / 'skills/guzhu-hao/scripts'), str(ROOT / 'engine')]
import guzhu_batch as gb
import jypack_render

DRAFTS = Path.home() / 'AppData/Local/JianyingPro/User Data/Projects/com.lveditor.draft'
folder = DRAFTS / 'guzhu-01'

timeline, source = gb.read_draft_timeline(ROOT, folder)
draft_id = timeline.get('id')
print('草稿 %s 的 timeline.id = %s' % (folder.name, draft_id))

candidates = [
    Path(r'C:\Users\Administrator\.dsh\attachments\v1\files\1b\1b4df543f999b6d91fd0b4e328a108a2c0bb320ea7474fc1bac469c9176a61f2\测试.jypack'),
    ROOT / 'work/guzhu-bilianren-v1/locate/jypack/比恋人多点恨.jypack',
    ROOT / 'work/guzhu-buneng-v3/jypack/不再需要答案.jypack',
]
match = None
for path in candidates:
    if not path.is_file():
        print('  缺失: %s' % path.name)
        continue
    try:
        tid = jypack_render.package_timeline_id(path)
    except Exception as error:  # noqa: BLE001
        print('  读取失败 %s: %s' % (path.name, str(error)[:80]))
        continue
    flag = ' <== 匹配草稿' if tid == draft_id else ''
    print('  %-34s timeline.id=%s%s' % (path.name[:34], tid, flag))
    if tid == draft_id:
        match = path

if match is None:
    # 草稿 id 与所有 jypack 都不同：把草稿 id 对齐到 build 用的那个 jypack
    build_pack = candidates[0] if candidates[0].is_file() else candidates[1]
    only = match_backup = None
    # 找 build 产出的 jypack（与草稿同名的那个）
    produced = ROOT / 'work/guzhu-bilianren-v1/locate/jypack/比恋人多点恨.jypack'
    if produced.is_file():
        tid = jypack_render.package_timeline_id(produced)
        print()
        print('把草稿 timeline.id 对齐为 build 产出的 jypack: %s' % tid)
        timeline['id'] = tid
        gb.write_draft_timeline(ROOT, folder, timeline, source)
        match = produced
print()
if match is None:
    raise SystemExit('找不到可用 JYPACK')

out = ROOT / 'work/guzhu-bilianren-v1/final'
if out.exists():
    shutil.rmtree(out, ignore_errors=True)
result = subprocess.run(
    [sys.executable, str(ROOT / 'engine/jypack_render.py'),
     '--input', str(match), '--draft-dir', str(folder), '--out', str(out),
     '--width', '1280', '--height', '720', '--fps', '30', '--timeout', '1800'],
    capture_output=True, timeout=2400)
print('导出退出码 %s' % result.returncode)
if result.returncode != 0:
    print(result.stderr.decode('utf-8', 'replace')[-300:])
else:
    video = out / 'render.mp4'
    print('成片: %s (%d bytes)' % (video, video.stat().st_size))
