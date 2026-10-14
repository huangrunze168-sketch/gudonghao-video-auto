# -*- coding: utf-8 -*-
"""实测官方 TTS：在剪映草稿根下的草稿副本上直接生成配音。"""
import shutil
import sys
import traceback
from pathlib import Path

ROOT = Path(r"C:\Users\Administrator\Documents\剪映")
sys.path.insert(0, str(ROOT / "engine"))
sys.path.insert(0, str(ROOT / "skills" / "guzhu-hao" / "scripts"))

import lyra_cli  # noqa: E402
import windows_runtime  # noqa: E402
from guzhu_jypack import read_package  # noqa: E402

DRAFT_ROOT = Path(windows_runtime.DRAFT_ROOT).resolve()
REF = "guzhu-official-test"
SOURCE = ROOT / "work" / "guzhu-final" / "jypack" / "问春风.jypack"

folder = DRAFT_ROOT / REF
if folder.exists():
    shutil.rmtree(folder)
folder.mkdir(parents=True)
package = read_package(SOURCE, None, decrypt=False)
for name in package.names():
    if name.endswith("/"):
        continue
    target = folder / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(package.read(name))
print("已安装草稿副本:", folder)

TEXT = "家人们别划走，这条用剪映官方音色试一句。"
for speaker in ("ICL_zh_female_xinmanbo", "BV700_streaming"):
    print("\n===== 试 speaker = %s =====" % speaker)
    try:
        result = lyra_cli.draft(
            ["algo", "tts"], str(DRAFT_ROOT), "local://" + REF,
            {"--text": TEXT, "--speaker": speaker, "--write-to-draft": "true"},
            timeout=600)
        print("成功:", str(result)[:900])
    except Exception as error:  # noqa: BLE001 - 探测哪些参数可用
        print("失败:", type(error).__name__, str(error)[:400])
