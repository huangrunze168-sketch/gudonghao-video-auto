"""诊断剩余未成功命令的完整参数与官方原始错误。"""
import glob
import json
import sys

pattern = 'work/functional-test/evidence/functional-execute-*.json'
rows = json.load(open(sorted(glob.glob(pattern))[-1], encoding='utf-8'))['execute']['rows']
targets = {'video-tracking', 'blueprint patch', 'mask add', 'adjust add', 'text effect add',
           'audio-effect add', 'subtitle-recognize', 'text-add-tone', 'material-understand',
           'effect generate', 'measure-box', 'vad', 'recommend', 'similar', 'upgrade',
           'undo', 'redo', 'aigc image2image', 'media understand', 'project import'}
for row in rows:
    joined = ' '.join(row['path'])
    if not any(token in joined for token in targets):
        continue
    print('=' * 70)
    print(joined, '->', row['state'], 'exit', row.get('exit_code'))
    print('args:', row.get('args'))
    print('message:', (row.get('message') or '')[:400])
    print('stdout:', (row.get('stdout') or '')[:500])
