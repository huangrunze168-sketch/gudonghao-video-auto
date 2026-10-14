"""读取最近一次流水线报告的关键字段。"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
target = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "work" / "run-verify"

report_path = target / "pipeline-report.json"
if not report_path.is_file():
    print("找不到报告:", report_path)
    raise SystemExit(1)

report = json.loads(report_path.read_text(encoding="utf-8"))
print("status:", report.get("status"))
print("source_draft:", report.get("source_draft"))
print("working_draft:", report.get("working_draft"))
for name, value in report.get("steps", {}).items():
    if name == "recognize":
        print(f"[{name}] engine={value.get('engine')} cue_count={value.get('cue_count')} "
              f"status={value.get('status')}")
        for line in (value.get("sentences") or [])[:12]:
            print("     ", line)
    elif name == "apply":
        print(f"[{name}] status={value.get('status')} executed={value.get('executed_count')} "
              f"applied={value.get('applied_count')} failed={value.get('failed_count')} "
              f"leftover={value.get('leftover_count')} rounds={value.get('rounds')}")
        for item in (value.get("failed") or [])[:3]:
            print("      failed:", item)
    elif name == "render":
        print(f"[{name}] status={value.get('status')} size={value.get('output_size')} "
              f"duration={value.get('video_duration')}")
    else:
        print(f"[{name}] status={value.get('status')}")
