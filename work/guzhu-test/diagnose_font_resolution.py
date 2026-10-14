"""诊断：草稿到底引用了哪个字体文件，以及字体文件内部真实名称。"""
import os
import struct
import sys
from pathlib import Path

ROOT = Path.cwd()
sys.path[:0] = [str(ROOT / 'skills/guzhu-hao/scripts'), str(ROOT / 'engine')]
import guzhu_batch as gb
from guzhu_timeline import Editor, range_of, parse_text_content

CACHE = Path(os.environ['LOCALAPPDATA']) / 'JianyingPro/User Data/Cache'


def ttf_names(path):
    """读 TTF/OTF 的 name 表，返回 {nameID: 文本}。"""
    try:
        data = Path(path).read_bytes()
    except Exception as error:  # noqa: BLE001
        return '读取失败 %s' % error
    tag = data[:4]
    if tag not in (b'\x00\x01\x00\x00', b'OTTO', b'true', b'ttcf'):
        return '非字体魔数 %r' % tag
    if tag == b'ttcf':
        return {'note': 'TrueType Collection'}
    num = struct.unpack('>H', data[4:6])[0]
    off = None
    for i in range(num):
        base = 12 + i * 16
        if data[base:base + 4] == b'name':
            off = struct.unpack('>I', data[base + 8:base + 12])[0]
            break
    if off is None:
        return '无 name 表'
    count = struct.unpack('>H', data[off + 2:off + 4])[0]
    str_off = struct.unpack('>H', data[off + 4:off + 6])[0]
    names = {}
    for i in range(count):
        b = off + 6 + i * 12
        pid, _eid, _lid, nid, length, so = struct.unpack('>HHHHHH', data[b:b + 12])
        raw = data[off + str_off + so: off + str_off + so + length]
        try:
            txt = raw.decode('utf-16-be') if pid == 3 else raw.decode('latin-1')
        except Exception:  # noqa: BLE001
            continue
        if nid in (1, 4, 6):
            names.setdefault(nid, txt)
    return names


def label(names):
    if isinstance(names, dict):
        return 'family=%s subfamily=%s ps=%s' % (names.get(1), names.get(2), names.get(6))
    return str(names)


root = gb.draft_root(ROOT)
folder = sorted([d for d in Path(root).iterdir() if d.name.startswith('guzhu-')],
                key=lambda p: p.stat().st_mtime_ns, reverse=True)[0]
print('草稿:', folder.name)
timeline, _ = gb.read_draft_timeline(ROOT, folder)
editor = Editor(timeline)
rows = []
for _track, segment in editor.segments():
    node = editor.node(segment.get('material_id')) or {}
    if editor.bucket(segment.get('material_id')) != 'texts':
        continue
    content = parse_text_content(node.get('content')) or {}
    for style in content.get('styles') or []:
        f = style.get('font') or {}
        rows.append((range_of(segment)[0], f.get('id'), f.get('path'),
                     str(content.get('text'))[:8]))
rows.sort()

print()
print('== 草稿字体引用（去重）==')
seen = set()
for start, fid, fpath, text in rows:
    key = (fid, fpath)
    if key in seen:
        continue
    seen.add(key)
    p = Path(str(fpath)) if fpath else None
    print('  %7.3f id=%-20s exists=%s  text=%s' % (start / 1e6, fid,
                                                   p.is_file() if p else None, text))
    print('      path=%s' % str(fpath)[:120])
    if p and p.is_file():
        print('      内部名: %s' % label(ttf_names(p)))

print()
print('== 我下载的默陌专辑手写体 ==')
for cand in [CACHE / 'lyra-cli/material-cache/font/7340606325656654345/font.ttf',
             CACHE / 'effect/7340606325656654345/font.ttf']:
    print('  %-58s exists=%s' % (str(cand)[-58:], cand.is_file()))
    if cand.is_file():
        print('      内部名: %s' % label(ttf_names(cand)))

print()
print('== 官方正常下载的对照组（默陌追风手写体）==')
for cand in [CACHE / 'lyra-cli/material-cache/font/7315024815268565541/font.ttf',
             CACHE / 'effect/7315024815268565541/默陌追风手写体.ttf']:
    print('  %-58s exists=%s' % (str(cand)[-58:], cand.is_file()))
    if cand.is_file():
        print('      内部名: %s' % label(ttf_names(cand)))

print()
print('== effect 目录里 7340606325656654345 的实际内容 ==')
d = CACHE / 'effect/7340606325656654345'
if d.is_dir():
    for f in d.iterdir():
        print('  %-40s %9d bytes' % (f.name, f.stat().st_size if f.is_file() else -1))
else:
    print('  目录不存在')
