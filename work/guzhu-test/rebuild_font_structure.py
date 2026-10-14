"""按官方结构重建字体缓存目录，让剪映真正认到字体。

官方正常下载的字体结构（实测）：
    font/<id>/
      font.ttf
      .locks/<md5>.lock
      <md5>/
        <原文件名>.ttf        <- 真字体（保留包内原名）
        config.json           <- {"effect":{"Link":[{"type":"InfoSticker"}]},"version":"3.1.1"}

绕过 CLI 直接下载时缺了 <md5>/ 子目录，并且会残留一个 **0 字节的 font.lock**。
草稿里的 font.path 恰好指向那个 lock 文件，剪映读到空文件就回退默认字体
（实测：字体文件 9.6MB 就在同目录，画面却仍是默认发光体）。
"""
import json
import os
import shutil
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
CACHE = Path(os.environ['LOCALAPPDATA']) / 'JianyingPro/User Data/Cache/lyra-cli/material-cache'
FONTDIR = CACHE / 'font'
EFFECT = Path(os.environ['LOCALAPPDATA']) / 'JianyingPro/User Data/Cache/effect'
FONT_SUFFIX = ('.ttf', '.otf', '.ttc')
CONFIG = {"effect": {"Link": [{"type": "InfoSticker"}]}, "version": "3.1.1"}

audit = json.loads(Path('work/guzhu-templates/font-audit.json').read_text(encoding='utf-8'))
ids = sorted(audit['fonts'])

fixed = 0
report = []
for fid in ids:
    folder = FONTDIR / fid
    if not folder.is_dir():
        continue
    fonts = [f for f in folder.iterdir()
             if f.is_file() and f.suffix.lower() in FONT_SUFFIX and f.stat().st_size > 1024]
    if not fonts:
        continue
    primary = max(fonts, key=lambda f: f.stat().st_size)
    changed = []

    # 1. 删掉 0 字节的 font.lock（它会让草稿的 font.path 指向空文件）
    lock = folder / 'font.lock'
    if lock.is_file() and lock.stat().st_size == 0:
        lock.unlink()
        changed.append('删 font.lock')

    # 2. 建 <md5>/ 子目录，放真字体 + config.json
    md5name = None
    for item in folder.iterdir():
        if item.is_dir() and item.name != '.locks' and len(item.name) == 32:
            md5name = item.name
            break
    if md5name is None:
        # 从 .locks 里的 lock 文件名推断 md5
        locks_dir = folder / '.locks'
        if locks_dir.is_dir():
            for f in locks_dir.iterdir():
                if f.suffix == '.lock' and len(f.stem) == 32:
                    md5name = f.stem
                    break
    if md5name is None:
        md5name = 'local0000000000000000000000000000'
    sub = folder / md5name
    if not sub.is_dir():
        sub.mkdir(parents=True, exist_ok=True)
        changed.append('建 %s/' % md5name)
    inner = sub / primary.name
    if not inner.is_file() or inner.stat().st_size != primary.stat().st_size:
        shutil.copyfile(primary, inner)
        changed.append('放真字体')
    cfg = sub / 'config.json'
    if not cfg.is_file():
        cfg.write_text(json.dumps(CONFIG, ensure_ascii=False, indent=2), encoding='utf-8')
        changed.append('写 config.json')

    # 3. effect 目录也保证有字体（渲染读取）
    eff = EFFECT / fid
    if not eff.is_dir() or not any(f.is_file() and f.suffix.lower() in FONT_SUFFIX
                                   and f.stat().st_size > 1024 for f in eff.iterdir()):
        eff.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(primary, eff / primary.name)
        changed.append('补 effect')

    if changed:
        fixed += 1
        report.append({'font_id': fid, 'changed': changed, 'file': primary.name,
                       'bytes': primary.stat().st_size})
        print('%-20s %s' % (fid, '、'.join(changed)))

print()
print('整理 %d 个字体目录' % fixed)
Path('work/guzhu-templates/font-structure-fix.json').write_text(
    json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
