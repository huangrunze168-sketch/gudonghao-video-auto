"""清理累积的歌词/字幕任务组，让 animation add 可用。

根因：反复套模板与识别让 config.lyrics_taskinfo 累积到 11 组、subtitle_taskinfo 3 组，
animation add 无法确定用哪一组，于是报 multiple lyrics recognize tasks found。
只保留文字素材实际引用的那组任务。
"""
import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path.cwd()
sys.path[:0] = [str(ROOT / 'engine'), str(ROOT / 'skills/guzhu-hao/scripts')]
import windows_runtime  # noqa: E402

DRAFTS = Path(os.environ['LOCALAPPDATA']) / 'JianyingPro/User Data/Projects/com.lveditor.draft'
NAME = 'guzhu-01'
folder = DRAFTS / NAME


def load():
    source = max((folder / 'Timelines').glob('*/draft_content.json'),
                 key=lambda p: p.stat().st_mtime_ns)
    return windows_runtime._decrypt_metadata_in_memory(source), source


timeline, source = load()
config = timeline.setdefault('config', {})
texts = (timeline.get('materials') or {}).get('texts') or []

used_ids = {}
for node in texts:
    rid = str(node.get('recognize_task_id') or '')
    if rid:
        used_ids[rid] = used_ids.get(rid, 0) + 1
print('文字素材引用的 recognize_task_id: %s' % used_ids)
print()

for key in ('lyrics_taskinfo', 'subtitle_taskinfo'):
    arr = config.get(key)
    if not isinstance(arr, list):
        continue
    print('%s 共 %d 组' % (key, len(arr)))
    for index, item in enumerate(arr):
        task_id = str(item.get('id') or '')
        hit = task_id in used_ids
        print('   [%d] id=%-40s type=%-8s 素材引用=%s'
              % (index, task_id[:40], str(item.get('type'))[:8], 'YES' if hit else '-'))
    print()

# 只保留被素材引用的组，并按任务 id 去重；一组都没匹配就保留第一组
changed = {}
for key in ('lyrics_taskinfo', 'subtitle_taskinfo'):
    arr = config.get(key)
    if not isinstance(arr, list) or len(arr) <= 1:
        continue
    keep = []
    seen = set()
    for item in arr:
        task_id = str(item.get('id') or '')
        if task_id in used_ids and task_id not in seen:
            keep.append(item)
            seen.add(task_id)
    if not keep:
        keep = [arr[0]]
    changed[key] = (len(arr), len(keep))
    config[key] = keep

print('清理计划: %s' % changed)
if not changed:
    print('无需清理')
    raise SystemExit(0)

# 备份再写回
backup = ROOT / 'work/guzhu-test/taskinfo-backup.json'
backup.write_text(json.dumps({'name': NAME}, ensure_ascii=False), encoding='utf-8')
shutil.copyfile(source, source.with_suffix('.json.bak'))

payload = json.dumps(timeline, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
source.unlink()
windows_runtime._encrypt_metadata_from_memory(payload, source)
print('已清理并写回（原文件备份为 %s）' % source.with_suffix('.json.bak').name)

# 复核
timeline2, _ = load()
config2 = timeline2.get('config') or {}
print('复核: lyrics_taskinfo=%d 组, subtitle_taskinfo=%d 组'
      % (len(config2.get('lyrics_taskinfo') or []),
         len(config2.get('subtitle_taskinfo') or [])))
