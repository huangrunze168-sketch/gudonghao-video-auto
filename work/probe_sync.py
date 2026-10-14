"""探测 blueprint sync 的 --ref 解析方式（local://<name> 相对哪个根）。"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "engine"))
import draftediting_runtime as dr  # noqa: E402

LOCAL = Path(os.environ["LOCALAPPDATA"])
WS = LOCAL / "Temp" / "jianying-draftediting" / "apply2"
COPY_ROOT = LOCAL / "Temp" / "jianying-draftediting-project-copy"
DRAFTS = LOCAL / "JianyingPro" / "User Data" / "Projects" / "com.lveditor.draft"

CASES = [
    (COPY_ROOT, "local://source-copy"),
    (WS, "local://source-copy"),
    (DRAFTS.parent, "local://com.lveditor.draft"),
    (COPY_ROOT / "source-copy", "local://source-copy"),
]

for cwd, ref in CASES:
    if not Path(cwd).is_dir():
        print("SKIP missing cwd", cwd)
        continue
    try:
        result = dr.run_lyra(["draft", "blueprint", "sync", "--workspace", str(WS), "--ref", ref],
                             cwd, 120, [WS, COPY_ROOT, cwd])
        print("OK  ", cwd, "|", ref, "|", result["result"].get("result"))
        break
    except Exception as error:  # noqa: BLE001 - 探测脚本需要看到每种失败
        print("FAIL", cwd, "|", ref, "|", str(error)[:300])
