# -*- coding: utf-8 -*-
"""验证绕过剪映导入的路径：直接把生成的包安装成草稿根下的草稿，再原生渲染。"""
import subprocess
import sys
from pathlib import Path

SKILL = Path(r"C:\Users\Administrator\Documents\剪映\skills\guzhu-hao\scripts")
sys.path.insert(0, str(SKILL))
sys.path.insert(0, str(SKILL.parent.parent.parent / "engine"))

from guzhu_common import EngineCrypto, resolve_project  # noqa: E402
from guzhu_jypack import read_package  # noqa: E402

PROJECT = resolve_project()
JYPACK = Path(r"C:\Users\Administrator\Documents\剪映\work\guzhu-run-01\jypack\问春风.jypack")
OUT = Path(r"C:\Users\Administrator\Documents\剪映\work\guzhu-install-render")

sys.path.insert(0, str(PROJECT / "engine"))
import windows_runtime  # noqa: E402

DRAFT_ROOT = Path(windows_runtime.DRAFT_ROOT).resolve()
folder = DRAFT_ROOT / "guzhu-问春风-test"
print("草稿根:", DRAFT_ROOT)
print("目标草稿:", folder)

package = read_package(JYPACK, None, decrypt=False)
if folder.exists():
    import shutil

    shutil.rmtree(folder)
folder.mkdir(parents=True)
count = 0
for name in package.names():
    if name.endswith("/"):
        continue
    target = folder / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(package.read(name))
    count += 1
print("解包条目:", count)

if OUT.exists():
    import shutil

    shutil.rmtree(OUT)
command = [sys.executable, str(PROJECT / "engine" / "jypack_render.py"),
           "--input", str(JYPACK), "--out", str(OUT), "--draft-dir", str(folder),
           "--width", "1280", "--height", "720", "--timeout", "900"]
print("渲染:", " ".join(command[1:]))
completed = subprocess.run(command, capture_output=True, cwd=str(PROJECT))
print("returncode:", completed.returncode)
print(completed.stdout.decode("utf-8", "replace")[-2500:])
print("--- stderr ---")
print(completed.stderr.decode("utf-8", "replace")[-2500:])
