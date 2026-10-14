"""打印最近的 functional_test 证据摘要。"""
import glob
import json
import sys

pattern = sys.argv[1] if len(sys.argv) > 1 else 'work/functional-test/evidence/functional-execute-*.json'
latest = sorted(glob.glob(pattern))[-1]
data = json.load(open(latest, encoding='utf-8'))
print('report', latest)
print('context', json.dumps(data.get('context', {}), ensure_ascii=False)[:300])
rows = data.get('execute', {}).get('rows', [])
print('summary', json.dumps(data.get('execute', {}).get('summary', {}), ensure_ascii=False))
for row in rows:
    print(f"{row['state']:16s} exit={str(row.get('exit_code')):5s} {' '.join(row['path'])}")
    print('     args', row['args'])
    if row['state'] != 'ok':
        print('     msg', (row.get('message') or '')[:200])
