"""诊断 Toolhelp32 枚举结果，确认剪映进程是否可见。"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "engine"))
import draftediting_runtime as dr  # noqa: E402

rows = dr._win32_process_list()
print("enumerated:", len(rows))
print("distinct names:", len({row["name"] for row in rows}))
print("sample:", sorted({row["name"] for row in rows})[:30])
print("jianying matches:", [row for row in rows if "jianying" in row["name"].lower()])
print("bun matches:", [row for row in rows if "bun" in row["name"].lower()])
