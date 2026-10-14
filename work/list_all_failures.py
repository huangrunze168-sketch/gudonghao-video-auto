"""列出最近报告中所有非 ok 命令及其完整官方消息。"""
import glob
import json

rows = json.load(open(sorted(glob.glob(
    'work/functional-test/evidence/functional-execute-*.json'))[-1], encoding='utf-8'))['execute']['rows']
for row in rows:
    if row['state'] == 'ok':
        continue
    print(f"[{row['state']}] {' '.join(row['path'])}")
    print('   ', (row.get('message') or '').replace('\n', ' ')[:330])
