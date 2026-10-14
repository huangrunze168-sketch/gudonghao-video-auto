"""列出 config 里的歌词/字幕任务组，找出让 animation add 报多组的原因。"""
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT / 'engine'))
import windows_runtime  # noqa: E402

DRAFTS = Path(os.environ['LOCALAPPDATA']) / 'JianyingPro/User Data/Projects/com.lveditor.draft'

for name in ('guzhu-01',):
    folder = DRAFTS / name
    source = max((folder / 'Timelines').glob('*/draft_content.json'),
                 key=lambda p: p.stat().st_mtime_ns)
    timeline = windows_runtime._decrypt_metadata_in_memory(source)
    config = timeline.get('config') or {}
    print('草稿 %s' % name)
    print('config 的键: %s' % sorted(config.keys()))
    print()
    for key in ('lyrics_taskinfo', 'subtitle_taskinfo'):
        arr = config.get(key)
        if not isinstance(arr, list):
            print('%s: 非数组 (%s)' % (key, type(arr).__name__))
            continue
        print('%s: %d 组' % (key, len(arr)))
        for index, item in enumerate(arr):
            content = item.get('content') if isinstance(item, dict) else None
            text = content if isinstance(content, str) else json.dumps(content, ensure_ascii=False)
            asr = re.search(r'"asr_id"\s*:\s*"([^"]+)"', text or '')
            lang = re.search(r'"language"\s*:\s*"([^"]+)"', text or '')
            utter = len(re.findall(r'"utterances"', text or ''))
            keys = sorted(item.keys()) if isinstance(item, dict) else []
            print('   [%d] asr_id=%-38s language=%-8s 长度=%-6d keys=%s'
                  % (index, (asr.group(1) if asr else '?')[:38],
                     (lang.group(1) if lang else '?')[:8], len(text or ''), keys))
        print()
    # 文字素材引用的识别 id
    texts = (timeline.get('materials') or {}).get('texts') or []
    ids = {}
    for node in texts:
        rid = node.get('recognize_task_id')
        if rid:
            ids[rid] = ids.get(rid, 0) + 1
    print('文字素材引用的 recognize_task_id: %s' % ids)
    print('文字素材数: %d' % len(texts))
