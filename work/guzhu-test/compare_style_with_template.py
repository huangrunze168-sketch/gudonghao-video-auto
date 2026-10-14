"""核对草稿里的歌词文本样式是否与模板定义一致（颜色/字号/描边/字体）。

"与剪映官方一致"的可验证部分：
套模板走的是剪映官方 CLI（与 GUI 同一个模板引擎），因此只要
(1) 字体文件齐全（不回退）、(2) 模板定义的样式被写进草稿，
渲染结果就应当与 GUI 里套同一模板一致。这里逐项核对 (2)。
"""
import json
import os
import sys
from pathlib import Path

ROOT = Path.cwd()
sys.path[:0] = [str(ROOT / 'skills/guzhu-hao/scripts'), str(ROOT / 'engine')]
import guzhu_batch as gb
from guzhu_timeline import Editor, parse_text_content

CACHE = (Path(os.environ['LOCALAPPDATA']) / 'JianyingPro/User Data/Cache'
         / 'lyra-cli' / 'material-cache' / 'lyric_animation')

TARGETS = {
    '7413413547289464100': '雨雾氛围感',
    '7548651294404234505': 'KTV复古字幕',
    '7602473145622072595': '文艺复古',
    '7603235197269609791': '发光手写',
    '7642652941349883146': '星闪发光',
}


def template_style(tid):
    path = next((CACHE / tid).rglob('LyricStyle.json'), None)
    if path is None:
        return {}
    data = json.loads(path.read_text(encoding='utf-8', errors='replace'))
    return (data.get('text_style') or {})


def summarize(style):
    """把模板 text_style 压成可比对的关键项。"""
    if not isinstance(style, dict):
        return {}
    out = {}
    for key in ('font_id', 'font_size', 'size', 'color', 'text_color',
                'stroke_color', 'stroke_width', 'bold', 'italic',
                'shadow_color', 'shadow_alpha', 'alpha'):
        if key in style:
            out[key] = style[key]
    # 颜色常嵌在 fill / content 里
    fill = style.get('fill') or style.get('content')
    if isinstance(fill, dict):
        out['fill'] = json.dumps(fill, ensure_ascii=False)[:150]
    return out


def draft_style(folder):
    """读草稿里歌词段的实际样式。"""
    timeline, _ = gb.read_draft_timeline(ROOT, folder)
    editor = Editor(timeline)
    seen = []
    for _track, segment in editor.segments():
        node = editor.node(segment.get('material_id')) or {}
        if editor.bucket(segment.get('material_id')) != 'texts':
            continue
        if node.get('type') == 'subtitle':
            continue
        content = parse_text_content(node.get('content')) or {}
        for style in content.get('styles') or []:
            key = json.dumps({k: v for k, v in style.items() if k != 'range'},
                             ensure_ascii=False, sort_keys=True)
            if key not in [s['key'] for s in seen]:
                seen.append({'key': key, 'style': style})
        if len(seen) >= 3:
            break
    return seen


root = gb.draft_root(ROOT)
folder = sorted([d for d in Path(root).iterdir() if d.name.startswith('guzhu-')],
                key=lambda p: p.stat().st_mtime_ns, reverse=True)[0]
print('基准草稿: %s（当前套用的模板以草稿实际为准）' % folder.name)
print()
actual = draft_style(folder)
print('== 草稿里歌词段的实际样式 ==')
for index, item in enumerate(actual):
    s = item['style']
    print('  样式%d: font=%s size=%s' % (index, (s.get('font') or {}).get('id'),
                                        s.get('size')))
    for key in ('fill', 'strokes', 'stroke', 'shadows', 'shadow'):
        if key in s:
            print('        %s = %s' % (key, json.dumps(s[key], ensure_ascii=False)[:180]))
    if 'content' in s:
        print('        content = %s' % json.dumps(s['content'], ensure_ascii=False)[:180])
print()
print('== 各模板定义的 text_style 关键项 ==')
for tid, title in TARGETS.items():
    style = template_style(tid)
    info = summarize(style)
    print('  %-12s %s' % (title, json.dumps(info, ensure_ascii=False)[:220]))
