"""核对最近报告中目标命令的最终状态。"""
import glob
import json

rows = json.load(open(sorted(glob.glob(
    'work/functional-test/evidence/functional-execute-*.json'))[-1], encoding='utf-8'))['execute']['rows']
want = ('algo query', 'algo wait', 'material download', 'filter remove', 'filter update',
        'effect remove', 'effect update', 'video-tracking', 'material topic',
        'template add', 'blueprint patch', 'recommend', 'similar', 'upgrade',
        'lint command', 'effect generate', 'material-understand', 'understand')
for row in rows:
    joined = ' '.join(row['path'])
    if any(word in joined for word in want):
        message = (row.get('message') or '').replace('\n', ' ')[:88]
        print(f"{row['state']:22s} {joined:38s} {message}")
