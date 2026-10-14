"""执行 blueprint apply 并只打印摘要，避免完整诊断刷屏。

用法：python work/run_apply.py <workspace> <draft-dir> <ref> <selection-file>
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "engine"))
import draftediting_runtime as dr  # noqa: E402

workspace, draft_dir, ref, selection = sys.argv[1:5]
response = dr.blueprint_apply(workspace, draft_dir, ref, selection)
result = response["result"]["result"]
print(json.dumps({
    "err_code": response["result"]["err_code"],
    "executed_count": result.get("executed_count"),
    "planned_count": result.get("planned_count"),
    "skipped_count": result.get("skipped_count"),
    "no_effect_count": result.get("no_effect_count"),
    "validation": (result.get("xmldraft_validation") or {}).get("summary"),
    "commands": result.get("cmd_list"),
}, ensure_ascii=False, indent=2))
