"""按"画面中间显眼"标准，为字号大的歌词模板补齐字体依赖。

用户的明确要求：歌词模板要选中间显眼的。实测 12 号小字 + layout_spread 分散布局
在成片里几乎没有存在感，而节奏摇滚(30)、ChineseCalligraphy(25)、ColorBold(22)、
多彩手写(21)、ktv(20) 这类大字模板此前因缺字体被依赖检查挡掉。
"""
import json
import os
import sys
from pathlib import Path

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT / 'skills/guzhu-hao/scripts'))
sys.path.insert(0, str(ROOT / 'engine'))
from official_materials import execute
from guzhu_anim import animation_catalog, animation_dependencies_ready, animation_prominence

os.environ['DSH_LYRA_ALLOW_NETWORK'] = '1'

# 收集所有歌词模板里"显眼"（字号够大、非分散布局）的，去重其字体依赖
targets = {}
fonts = set()
for item in animation_catalog():
    ok, size, title = animation_prominence(item.get('style'))
    if not ok:
        continue
    targets[item['id']] = {'size': size, 'title': title, 'style': item['style']}
    try:
        data = json.loads(Path(item['style']).read_text(encoding='utf-8', errors='replace'))
    except Exception:
        continue

    def walk(node):
        if isinstance(node, dict):
            for key, value in node.items():
                if key == 'font_id':
                    values = value if isinstance(value, list) else [value]
                    fonts.update(str(v) for v in values if str(v).isdigit())
                else:
                    walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(data)

print('显眼模板 %d 个，涉及字体 %d 个' % (len(targets), len(fonts)))
results = {}
for fid in sorted(fonts):
    r = execute('.', ['material', 'download', '--type', 'font', '--resource-id', fid])
    ok = 'envelope' in r
    results[fid] = {'status': r['status'], 'ok': ok}
    print('  %s %s' % (fid, r['status']), flush=True)

ready = [i for i in animation_catalog()
         if animation_dependencies_ready(i.get('style'))
         and animation_prominence(i.get('style'))[0]]
print()
print('现在"依赖齐全且显眼"的模板: %d 个' % len(ready))
for item in ready:
    ok, size, title = animation_prominence(item['style'])
    print('  字号=%-3s %-20s %s' % (size, item['id'], title))

Path('work/guzhu-mingyun-v2/prominent-templates.json').write_text(
    json.dumps({'targets': targets, 'fonts': results,
                'ready': [i['id'] for i in ready]}, ensure_ascii=False, indent=2),
    encoding='utf-8')
