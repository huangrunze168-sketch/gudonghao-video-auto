"""按官方模板明确 font_id 清单逐项下载，记录实体，不修改成片草稿。"""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / 'skills/guzhu-hao/scripts'))
from guzhu_anim import animation_catalog, effect_pool
from official_materials import execute

names = effect_pool().get('text_templates') or {}
records = []
fonts = {}

def collect(node):
    result = set()
    if isinstance(node, dict):
        for key, value in node.items():
            if key == 'font_id':
                values = value if isinstance(value, list) else [value]
                result.update(str(v) for v in values if str(v).isdigit())
            else:
                result.update(collect(value))
    elif isinstance(node, list):
        for value in node:
            result.update(collect(value))
    return result

for item in animation_catalog():
    rid = item['id']
    if rid not in names:
        continue
    data = json.loads(Path(item['style']).read_text(encoding='utf-8'))
    deps = sorted(collect(data))
    record = {'id': rid, 'name': names[rid], 'font_ids': deps}
    records.append(record)
    for fid in deps:
        if fid in fonts:
            continue
        result = execute('.', ['material', 'download', '--type', 'font', '--resource-id', fid,
                               '--resource-dir', str(Path(__import__('tempfile').gettempdir())/'jy-font-verify'/fid)])
        files = list((Path(__import__('tempfile').gettempdir())/'jy-font-verify'/fid).rglob('*'))
        result['font_entities'] = [{'path': str(p), 'bytes': p.stat().st_size} for p in files
                                  if p.is_file() and p.suffix.lower() in ('.ttf','.otf','.ttc') and p.stat().st_size > 0]
        fonts[fid] = result
        print(fid, result['status'], len(result['font_entities']), flush=True)
        Path('work/guzhu-test/font-verification.json').write_text(json.dumps({'templates': records, 'fonts': fonts},ensure_ascii=False,indent=2),encoding='utf-8')
Path('work/guzhu-test/font-verification.json').write_text(json.dumps({'templates': records, 'fonts': fonts},ensure_ascii=False,indent=2),encoding='utf-8')
