"""打印模板检查报告的关键结构。"""
import json
import sys
from pathlib import Path

source = Path(sys.argv[1] if len(sys.argv) > 1 else 'work/测试-jypack-report.json')
data = json.loads(source.read_text(encoding='utf-8'))
for key in ('schema', 'source', 'container'):
    print(key, '=', json.dumps(data.get(key), ensure_ascii=False)[:300])
timeline = data.get('timeline') or {}
print('timeline keys:', list(timeline))
print('duration:', timeline.get('duration_seconds'), 'tracks:', timeline.get('track_count'))
print('materials:', json.dumps(timeline.get('material_counts'), ensure_ascii=False))
for key in ('placeholders', 'tts', 'lyrics', 'templates', 'text_templates', 'capabilities',
            'findings', 'assets', 'media', 'images', 'videos'):
    if key in data:
        print('---', key)
        print(json.dumps(data[key], ensure_ascii=False)[:900])
print('顶层键:', list(data))
