"""归类 functional_test 执行报告里的失败原因。"""
import collections
import glob
import json
import re
import sys

pattern = sys.argv[1] if len(sys.argv) > 1 else 'work/functional-test/evidence/functional-execute-*.json'
latest = sorted(glob.glob(pattern))[-1]
rows = json.load(open(latest, encoding='utf-8'))['execute']['rows']
print('report', latest, 'rows', len(rows))

buckets = collections.Counter()
examples = {}
for row in rows:
    if row['state'] == 'ok':
        continue
    message = (row.get('message') or '')[:200]
    if re.search(r'RequiredError|is required', message):
        key = 'REQUIRED 缺失: ' + (re.search(r'([\w-]+) is required', message).group(1)
                                   if re.search(r'([\w-]+) is required', message) else '?')
    elif 'not found' in message or 'not exist' in message:
        key = '目标不存在'
    elif 'requires' in message:
        key = '缺少前置条件: ' + message.split('requires')[1].strip()[:40]
    elif 'invalid' in message or 'unsupported' in message:
        key = '参数取值/格式不被接受'
    elif 'permission' in message:
        key = '权限'
    elif row['state'] == 'timeout':
        key = '命令超时'
    else:
        key = row['state'] + ': ' + (message[:60] or '(空消息)')
    buckets[key] += 1
    examples.setdefault(key, []).append(' '.join(row['path']) + ' :: ' + message[:120])

for key, count in buckets.most_common(40):
    print(f'{count:4d}  {key}')
    for item in examples[key][:3]:
        print('        ', item)
