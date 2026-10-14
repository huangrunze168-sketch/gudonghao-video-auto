# -*- coding: utf-8 -*-
"""检查：歌词为 text 模式时，官方 sync 出来的 canonical XML 里是不是普通 <text> 段。"""
import collections
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\Administrator\Documents\剪映")
sys.path.insert(0, str(ROOT / "engine"))
sys.path.insert(0, str(ROOT / "skills" / "guzhu-hao" / "scripts"))

import windows_runtime  # noqa: E402
from guzhu_jypack import read_package  # noqa: E402

DR = Path(windows_runtime.DRAFT_ROOT).resolve()
NAME = "guzhu-lyric-text"
FOLDER = DR / NAME
if FOLDER.exists():
    shutil.rmtree(FOLDER)
FOLDER.mkdir(parents=True)
package = read_package(ROOT / "work" / "guzhu-official" / "jypack" / "问春风.jypack",
                       None, decrypt=False)
for name in package.names():
    if name.endswith("/"):
        continue
    target = FOLDER / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(package.read(name))
print("已安装草稿:", NAME)

WS = Path(r"C:\Temp\lyric-ws")
if WS.exists():
    shutil.rmtree(WS)
for arguments in (["init", "--workspace", str(WS)],
                  ["sync", "--workspace", str(WS), "--ref", "local://" + NAME,
                   "--draft-root", str(DR)]):
    completed = subprocess.run([sys.executable, str(ROOT / "engine" / "draftediting_runtime.py"),
                                *arguments], capture_output=True, cwd=str(ROOT))
    print(arguments[0], "rc =", completed.returncode)
    if completed.returncode:
        print(completed.stderr.decode("utf-8", "replace")[-500:])

xml = (WS / "current_draft.xml").read_text(encoding="utf-8", errors="replace")
print("\n标签统计:", dict(collections.Counter(re.findall(r"<(\w+)", xml))))
print("\n== 所有 <text> 段 ==")
for match in re.finditer(r"<text\b[^>]*>.*?</text>", xml, re.S):
    body = match.group(0)
    has_template = "<template" in body
    text = re.search(r'<sub text="([^"]*)"', body)
    print("  template=%-5s  text=%s" % (has_template, (text.group(1) if text else "?")[:26]))
