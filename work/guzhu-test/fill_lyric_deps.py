"""递归补齐歌词模板的官方依赖（字体 / effect / 动画），并同步到套用时的缓存位置。

官方 `lyrics animation update` 会现拉模板缺的依赖，而沙箱里这一步常常失败：
- 有的资源下载后在 `Cache/artistEffect`，而套用要读 `Cache/lyra-cli/material-cache/...`；
- 有的依赖（字体、effect）根本没下载过。

这里按模板的 LyricStyle.json 递归找出依赖 id，逐个用官方 `material download` 取，
再把结果同步进官方读取路径，最后用 `animation_dependencies_ready` 复核。
"""
import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT / 'skills/guzhu-hao/scripts'))
sys.path.insert(0, str(ROOT / 'engine'))
from official_materials import execute

os.environ['DSH_LYRA_ALLOW_NETWORK'] = '1'

base = Path(os.environ['LOCALAPPDATA']) / 'JianyingPro/User Data/Cache'
ARTIST = base / 'artistEffect'
LYRA = base / 'lyra-cli' / 'material-cache'

# 依赖类型 -> 官方 material 的 type 关键字
TYPE_BY_BUCKET = {'font': 'font', 'effect': 'effect', 'transition': 'transition',
                  'lyric_animation': 'lyric_animation', 'text_template': 'text_template',
                  'sticker': 'sticker', 'music': 'music'}


def deps_of(style_path):
    """从 LyricStyle.json 里递归收集资源 id 与它声明的类型。"""
    try:
        data = json.loads(Path(style_path).read_text(encoding='utf-8', errors='replace'))
    except Exception:
        return []
    found = {}

    def walk(node):
        if isinstance(node, dict):
            for key, value in node.items():
                if key in ('font_id', 'resource_id', 'effect_id') :
                    values = value if isinstance(value, list) else [value]
                    for v in values:
                        if str(v).isdigit() and len(str(v)) >= 15:
                            found.setdefault(str(v), None)
                elif key in ('meta_type', 'type') and isinstance(value, str):
                    pass
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(data)
    return sorted(found)


def sync_into_lyra(resource_id, bucket):
    """把 artistEffect 里的资源拷进官方套用会读取的目录。"""
    src = ARTIST / resource_id
    if not src.is_dir():
        return False
    dst = LYRA / bucket / resource_id / resource_id
    shutil.copytree(src, dst, dirs_exist_ok=True)
    return True


def main(targets):
    summary = {}
    for rid in targets:
        style = next((ARTIST / rid).rglob('LyricStyle.json'), None)
        if style is None:
            print('  %s 没有本地定义，跳过' % rid)
            continue
        print('== 模板 %s' % rid)
        sync_into_lyra(rid, 'lyric_animation')
        for dep in deps_of(style):
            if any((LYRA / bucket / dep).is_dir() for bucket in TYPE_BY_BUCKET.values()):
                print('   依赖 %s 已就位' % dep)
                continue
            ok_any = False
            for kind in ('font', 'effect', 'transition', 'lyric_animation', 'sticker'):
                r = execute('.', ['material', 'download', '--type', kind,
                                  '--resource-id', dep])
                if 'envelope' in r:
                    ok_any = True
                    print('   依赖 %s 以 %s 下载成功' % (dep, kind))
                    for bucket in TYPE_BY_BUCKET.values():
                        sync_into_lyra(dep, bucket)
                    break
            if not ok_any:
                print('   依赖 %s 下载失败' % dep)
        summary[rid] = True

    # 复核：官方读取路径下是否都有定义
    print()
    for rid in targets:
        style = next((LYRA / 'lyric_animation' / rid).rglob('LyricStyle.json'), None)
        print('  %s %s' % (rid, '可套用' if style else '仍缺定义'))
    (ROOT / 'work/guzhu-mingyun-v2/dep-fill.json').write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main(sys.argv[1:] or ['7548651294404234505', '7438521957072538934',
                          '7413395931036437796', '7431852704038784275'])
