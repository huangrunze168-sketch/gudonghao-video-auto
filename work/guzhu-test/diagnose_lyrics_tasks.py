"""查清 animation add 为什么报 multiple lyrics recognize tasks。

思路：解密草稿，递归找出所有与歌词识别相关的结构，统计有几组"识别任务"，
判断是草稿残留还是 CLI 自身的问题。
"""
import json
import os
import sys
from pathlib import Path

ROOT = Path.cwd()
sys.path[:0] = [str(ROOT / 'engine'), str(ROOT / 'skills/guzhu-hao/scripts')]
import windows_runtime  # noqa: E402

DRAFTS = Path(os.environ['LOCALAPPDATA']) / 'JianyingPro/User Data/Projects/com.lveditor.draft'
KEYS = ('lyric', 'recogn', 'task', 'subtitle', 'asr', 'speech')

for name in ('guzhu-01', 'guzhu-animtest-base'):
    folder = DRAFTS / name
    timelines = sorted((folder / 'Timelines').glob('*/draft_content.json'))
    if not timelines:
        print('%s: 无时间线' % name)
        continue
    source = max(timelines, key=lambda p: p.stat().st_mtime_ns)
    timeline = windows_runtime._decrypt_metadata_in_memory(source)
    print('=' * 70)
    print('草稿 %s' % name)
    hits = []

    def walk(node, path=''):
        if isinstance(node, dict):
            for key, value in node.items():
                low = str(key).lower()
                if any(t in low for t in KEYS):
                    brief = json.dumps(value, ensure_ascii=False)[:160] if not isinstance(
                        value, (str, int, float, bool, type(None))) else str(value)[:160]
                    hits.append(('%s/%s' % (path, key), brief))
                walk(value, '%s/%s' % (path, key))
        elif isinstance(node, list):
            for index, value in enumerate(node):
                walk(value, '%s[%d]' % (path, index))

    walk(timeline)
    print('相关字段 %d 处：' % len(hits))
    for key, brief in hits[:30]:
        print('  %-58s %s' % (key[-58:], brief))

    # 统计 materials 里 lyrics 类素材
    materials = timeline.get('materials') or {}
    print()
    print('materials 桶与数量:')
    for bucket, nodes in materials.items():
        if isinstance(nodes, list) and nodes:
            print('  %-24s %d' % (bucket, len(nodes)))
    # 顶层键
    print()
    print('时间线顶层键: %s' % sorted(timeline.keys()))
    print()
