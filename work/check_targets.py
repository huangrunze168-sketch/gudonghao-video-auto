"""核对用户列出的各项命令的最新真实状态。"""
import glob
import json

rows = json.load(open(sorted(glob.glob(
    'work/functional-test/evidence/functional-execute-*.json'))[-1], encoding='utf-8'))['execute']['rows']
want = ('subtitle-recognize', 'lyrics recognize', 'text-add-tone', 'video-tracking',
        'blueprint patch', 'image2image', 'aigc query', 'understand', 'effect generate',
        'measure-box', 'vad', 'sticker add', 'mask add', 'audio-effect add',
        'text effect add', 'adjust add', 'keyframe add', 'history undo', 'history redo',
        'recommend', 'similar', 'upgrade')
for row in rows:
    joined = ' '.join(row['path'])
    if any(word in joined for word in want):
        message = (row.get('message') or '').replace('\n', ' ')[:95]
        print(f"{row['state']:20s} {joined:40s} {message}")
