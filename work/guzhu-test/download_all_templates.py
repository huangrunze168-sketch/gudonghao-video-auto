"""批量下载官方全部歌词模板，建立备用库并生成索引。

流程：
1. 读取已枚举的主题清单（105 个模板）；
2. 逐个用官方 `material download` 下载；
3. 同步到官方套用时会读取的缓存位置；
4. 读每个模板的 LyricStyle.json 生成索引（名称/字号/风格/依赖字体数）。
"""
import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path.cwd()
sys.path[:0] = [str(ROOT / 'skills/guzhu-hao/scripts'), str(ROOT / 'engine')]
from official_materials import execute

os.environ['DSH_LYRA_ALLOW_NETWORK'] = '1'

TOPIC = json.loads((ROOT / 'work/guzhu-templates/topic-11878.json').read_text(encoding='utf-8'))
LIB = ROOT / 'work/guzhu-templates/library'
LIB.mkdir(parents=True, exist_ok=True)

CACHE = Path(os.environ['LOCALAPPDATA']) / 'JianyingPro/User Data/Cache'
ARTIST = CACHE / 'artistEffect'
LYRA = CACHE / 'lyra-cli' / 'material-cache' / 'lyric_animation'


def sync_to_lyra(rid):
    """套用时官方读 lyra-cli 目录，material download 却落到 artistEffect，需要同步。"""
    src = ARTIST / rid
    if not src.is_dir():
        return False
    shutil.copytree(src, LYRA / rid / rid, dirs_exist_ok=True)
    return True


def index_of(rid, title):
    style = next((LYRA / rid).rglob('LyricStyle.json'), None) if (LYRA / rid).is_dir() else None
    if style is None:
        style = next((ARTIST / rid).rglob('LyricStyle.json'), None)
    entry = {'id': rid, 'title': title, 'font_size': None, 'style_title': None,
             'dependencies': 0, 'has_style': bool(style)}
    if style is None:
        return entry
    try:
        data = json.loads(style.read_text(encoding='utf-8', errors='replace'))
    except Exception:  # noqa: BLE001
        return entry
    entry['font_size'] = (data.get('text_style') or {}).get('font_size')
    entry['style_title'] = data.get('title')
    deps = set()

    def walk(node):
        if isinstance(node, dict):
            for key, value in node.items():
                if key in ('font_id', 'resource_id', 'effect_id'):
                    vals = value if isinstance(value, list) else [value]
                    for v in vals:
                        if str(v).isdigit() and len(str(v)) >= 15:
                            deps.add(str(v))
                else:
                    walk(value)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(data)
    entry['dependencies'] = len(deps)
    entry['dep_ids'] = sorted(deps)
    return entry


index = {}
ok = fail = 0
for pos, (rid, info) in enumerate(sorted(TOPIC.items()), 1):
    title = info.get('title')
    r = execute(ROOT, ['material', 'download', '--type', 'lyric_animation', '--resource-id', rid])
    if 'envelope' not in r:
        fail += 1
        index[rid] = {'id': rid, 'title': title, 'download': 'failed',
                      'error': str(r.get('error'))[:150]}
        print('[%d/%d] %s %s 下载失败' % (pos, len(TOPIC), rid, title), flush=True)
        continue
    ok += 1
    sync_to_lyra(rid)
    entry = index_of(rid, title)
    entry['download'] = 'ok'
    index[rid] = entry
    print('[%d/%d] %s %-12s 字号=%-4s 风格=%-22s 依赖=%d'
          % (pos, len(TOPIC), rid, title, entry['font_size'],
             str(entry['style_title'])[:20], entry['dependencies']), flush=True)

(LIB / 'index.json').write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding='utf-8')
print()
print('下载完成：成功 %d，失败 %d，索引 %d 条' % (ok, fail, len(index)))
