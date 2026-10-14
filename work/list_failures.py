"""列出最近一次执行报告里非 ok 的命令与官方消息。"""
import glob
import json
import sys

state = sys.argv[1] if len(sys.argv) > 1 else None
pattern = 'work/functional-test/evidence/functional-execute-*.json'
rows = json.load(open(sorted(glob.glob(pattern))[-1], encoding='utf-8'))['execute']['rows']
for row in rows:
    if row['state'] == 'ok':
        continue
    if state and row['state'] != state:
        continue
    message = (row.get('message') or '').replace('\n', ' ')[:110]
    print(f"{row['state'][:18]:18s} {' '.join(row['path']):34s} {message}")
