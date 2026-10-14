"""提取 blueprint apply 失败的完整诊断信息。"""
import json
import re
import sys
from pathlib import Path

path = Path(sys.argv[1])
env = json.loads(path.read_text(encoding="utf-8"))
out = json.loads(env["responseMessage"]["result"]["stdout"])
message = out.get("err_msg") or ""
print("err_code:", out.get("err_code"))
print("message length:", len(message))
for key in ("failure_reason", "failure_type", "issues", "error_code", "repair_instructions",
            "failed_command", "stderr", "stdout", "message"):
    pattern = '"' + key + r'"\s*:\s*(.{0,600})'
    for match in re.finditer(pattern, message):
        print("==", key, "=>", match.group(1).replace("\\n", " ")[:600])
print()
print("---- tail ----")
print(message[-1500:].replace("\\n", "\n"))
