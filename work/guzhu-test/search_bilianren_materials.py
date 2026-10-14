"""按《比恋人多点恨》的意境在线搜歌词模板与搞笑贴纸。

歌词气质：爱恨纠缠、嘴硬心软、吵了又抱、分不开、算爱还是算债。
- 歌词模板要浓烈/有力量，不要温柔抒情类；
- 贴纸要按每句话术的情绪搜猫狗、汤姆杰瑞一类搞笑表情包。
"""
import json
import os
import sys
from pathlib import Path

ROOT = Path.cwd()
sys.path[:0] = [str(ROOT / 'skills/guzhu-hao/scripts'), str(ROOT / 'engine')]
from official_materials import execute  # noqa: E402

os.environ['DSH_LYRA_ALLOW_NETWORK'] = '1'
OUT = ROOT / 'work/guzhu-bilianren-v1'
OUT.mkdir(parents=True, exist_ok=True)

TEMPLATE_PROMPTS = ['情绪 拉扯 浓烈', '复古 浓烈 情绪', '摇滚 力量 歌词', '夜色 纠缠 情感']
STICKER_PROMPTS = ['猫 傲娇 表情包', '狗 委屈 表情包', '汤姆 杰瑞 打架 表情包',
                   '猫 拥抱 表情包', '猫 叹气 无奈 表情包']

found = {'templates': {}, 'stickers': {}}

print('=' * 66)
print('歌词模板搜索（按意境）')
print('=' * 66)
for prompt in TEMPLATE_PROMPTS:
    result = execute(ROOT, ['material', 'search', '--type', 'lyric_animation',
                            '--prompt', prompt, '--limit', '8'])
    body = (((result.get('envelope') or {}).get('result') or {}).get('result') or {})
    items = body.get('items') or []
    print('\n[%s] status=%s 命中 %d' % (prompt, result.get('status'), len(items)))
    for item in items[:8]:
        rid = str(item.get('resource_id'))
        title = item.get('title')
        found['templates'].setdefault(rid, {'title': title, 'prompts': []})
        found['templates'][rid]['prompts'].append(prompt)
        print('   %-20s %s' % (rid, title))

print()
print('=' * 66)
print('贴纸搜索（按每句话术的情绪）')
print('=' * 66)
for prompt in STICKER_PROMPTS:
    result = execute(ROOT, ['material', 'search', '--type', 'sticker',
                            '--prompt', prompt, '--limit', '6'])
    body = (((result.get('envelope') or {}).get('result') or {}).get('result') or {})
    items = body.get('items') or []
    print('\n[%s] status=%s 命中 %d' % (prompt, result.get('status'), len(items)))
    for item in items[:6]:
        rid = str(item.get('resource_id'))
        title = item.get('title')
        found['stickers'].setdefault(rid, {'title': title, 'prompts': []})
        found['stickers'][rid]['prompts'].append(prompt)
        print('   %-20s %s' % (rid, title))

(OUT / 'search-results.json').write_text(
    json.dumps(found, ensure_ascii=False, indent=2), encoding='utf-8')
print()
print('模板候选 %d 个，贴纸候选 %d 个 -> %s'
      % (len(found['templates']), len(found['stickers']), OUT / 'search-results.json'))
