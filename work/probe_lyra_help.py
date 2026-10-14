"""让 lyra-cli 的完整 help 落盘，再直接读取（结果包装会截断长输出）。"""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "engine"))
import draftediting_runtime as dr  # noqa: E402

WS = Path(os.environ["LOCALAPPDATA"]) / "Temp" / "jianying-draftediting" / "help-probe"
TRACES = ROOT / "work" / "draftediting-traces"


def run_and_dump(args):
    before = {p.name for p in TRACES.glob("*.json")}
    try:
        dr.run_lyra(args, WS, 120, [WS])
    except Exception:  # noqa: BLE001 - help 以非零退出，我们只要它的输出
        pass
    fresh = [p for p in TRACES.glob("*.json") if p.name not in before]
    if not fresh:
        print("没有新的 trace")
        return
    latest = max(fresh, key=lambda p: p.stat().st_mtime)
    text = latest.read_text(encoding="utf-8", errors="replace")
    print(f"--- {latest.name} ({len(text)} 字符) ---")
    print(text[:7000])
    print("--- 结束 ---")


run_and_dump(["draft", "--help"])
