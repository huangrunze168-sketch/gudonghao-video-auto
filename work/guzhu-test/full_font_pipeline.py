"""完整链路：重建草稿 → 逐个歌词段套模板字体 → 导出验证。

关键补丁：官方 `draft text style --font` 才是设置字体的通道，
但它要求**逐个段**传 `--seg-id`（逗号分隔会报 "expects raw segment ids"）。
模板的 font_id 从模板的 LyricStyle.json 读取。
"""
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd()
sys.path[:0] = [str(ROOT / 'skills/guzhu-hao/scripts'), str(ROOT / 'engine')]
import guzhu_batch as gb
import lyra_cli
from guzhu_timeline import Editor, range_of, parse_text_content

os.environ['DSH_LYRA_ALLOW_NETWORK'] = '1'

TEMPLATE_ID = '7413413547289464100'   # 雨雾氛围感
CACHE = Path(os.environ['LOCALAPPDATA']) / 'JianyingPro/User Data/Cache/lyra-cli/material-cache'
JYPACK = ROOT / 'work/guzhu-buneng-v3/jypack/不再需要答案.jypack'
OUT_DIR = ROOT / 'work/guzhu-buneng-v3/font-final'


def template_font_id(template_id):
    """从模板的 LyricStyle.json 读出它要求的字体 id。"""
    style = next((CACHE / 'lyric_animation' / template_id).rglob('LyricStyle.json'), None)
    if style is None:
        raise RuntimeError('找不到模板定义: ' + template_id)
    data = json.loads(style.read_text(encoding='utf-8', errors='replace'))
    font = (data.get('text_style') or {}).get('font_id')
    if isinstance(font, list):
        font = font[0] if font else None
    if not font:
        raise RuntimeError('模板没有声明 font_id')
    return str(font)


# 1. 用批次流程重建草稿（会重新识别 + 套模板）
print('== 重跑批次流程 ==')
completed = subprocess.run(
    [sys.executable, str(ROOT / 'skills/guzhu-hao/scripts/guzhu_batch.py'),
     'run', '--batch', str(ROOT / 'work/guzhu-test/batch-buneng-v3.json')],
    capture_output=True, timeout=3600, env={**os.environ, 'PYTHONUTF8': '1'})
tail = completed.stdout.decode('utf-8', 'replace').splitlines()
for line in tail:
    if any(k in line for k in ('官方歌词', '完成', '失败', '错误')):
        print('  ' + line.strip())
if completed.returncode != 0:
    raise SystemExit('批次流程失败: ' + completed.stderr.decode('utf-8', 'replace')[-300:])

root = gb.draft_root(ROOT)
folder = sorted([d for d in Path(root).iterdir() if d.name.startswith('guzhu-')],
                key=lambda p: p.stat().st_mtime_ns, reverse=True)[0]
ref = 'local://' + folder.name
print('草稿: %s' % folder.name)

# 2. 读出模板要求的字体，并逐个段设置
font_id = template_font_id(TEMPLATE_ID)
print('模板要求字体: %s' % font_id)

timeline, _ = gb.read_draft_timeline(ROOT, folder)
editor = Editor(timeline)
segments = sorted([s for _t, s in editor.segments()
                   if editor.bucket(s.get('material_id')) == 'texts'
                   and (editor.node(s.get('material_id')) or {}).get('type') != 'subtitle'],
                  key=lambda s: range_of(s)[0])
print('歌词段: %d 个' % len(segments))
if not segments:
    raise SystemExit('草稿里没有歌词段，无法设置字体')

applied = 0
for segment in segments:
    try:
        lyra_cli.draft(['text', 'style'], str(root), ref,
                       {'--seg-id': segment['id'], '--font': font_id})
        gb._mirror_draft(folder)
        applied += 1
    except Exception as error:  # noqa: BLE001
        print('  段 %s 设字体失败: %s' % (segment['id'][:8], str(error)[:100]))
print('设置字体成功 %d / %d 段' % (applied, len(segments)))

# 3. 回读确认
timeline2, _ = gb.read_draft_timeline(ROOT, folder)
editor2 = Editor(timeline2)
fonts = set()
for _t, s in editor2.segments():
    node = editor2.node(s.get('material_id')) or {}
    if editor2.bucket(s.get('material_id')) != 'texts':
        continue
    content = parse_text_content(node.get('content')) or {}
    for style in content.get('styles') or []:
        f = (style.get('font') or {}).get('id')
        if f:
            fonts.add(str(f))
print('回读草稿字体: %s' % fonts)
ok = font_id in fonts
print('模板字体是否已写入: %s' % ok)

(ROOT / 'work/guzhu-buneng-v3' / 'font-apply-report.json').write_text(
    json.dumps({'template': TEMPLATE_ID, 'font_id': font_id,
                'segments': len(segments), 'applied': applied,
                'draft_fonts': sorted(fonts), 'verified': ok},
               ensure_ascii=False, indent=2), encoding='utf-8')
print('完成')
