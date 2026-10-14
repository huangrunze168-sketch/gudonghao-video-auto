"""探测：官方 CLI 的 help 能否在沙箱里取到（决定能否批量抓全部命令的语义）。"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(r"C:\Users\Administrator\Documents\剪映")
sys.path.insert(0, str(ROOT / "engine"))
import draftediting_runtime as dr  # noqa: E402

ENV = {"LYRA_CLI_ALLOW_DEV_JIANYING_APP": "1"}
CWD = ROOT / "engine"

for label, args in [
    ("顶层 --help", ["--help"]),
    ("顶层 help", ["help"]),
    ("一条子命令 --help", ["draft", "video", "effect", "add", "--help"]),
    ("分组 --help", ["draft", "video", "--help"]),
]:
    try:
        envelope = dr.run_lyra(args, CWD, 60, [], [], extra_env=ENV)
        body = (envelope or {}).get("result") or {}
        text = str(body.get("output") or "")
        print("== %s ==  err_code=%s  output=%d 字符" % (label, body.get("err_code"), len(text)))
        print(text[:1200].replace("\r", ""))
    except Exception as error:  # noqa: BLE001
        print("== %s == 异常：%s" % (label, str(error).replace("\n", " ")[:300]))
    print()
