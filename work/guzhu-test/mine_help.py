"""重度深挖：批量抓取剪映官方 CLI 全部命令（含各级分组）的 help 原文。

官方命令 195 条，另外各级分组（draft / draft.video / draft.algo …）本身也有
help，能说明该域下面有哪些动作。全部走 draftediting_runtime 的官方沙箱。

产出 ``references/cli-help.json``：``{"draft.video.effect.add": "<help 原文>"}``
"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(r"C:\Users\Administrator\Documents\剪映")
sys.path.insert(0, str(ROOT / "engine"))
import draftediting_runtime as dr  # noqa: E402

ENV = {"LYRA_CLI_ALLOW_DEV_JIANYING_APP": "1"}
CWD = ROOT / "engine"
COMMANDS = json.loads((ROOT / "engine" / "lyra_commands.json").read_text(encoding="utf-8"))

targets = set()
for item in COMMANDS.get("commands") or []:
    path = tuple(str(part) for part in (item.get("path") or []))
    if not path:
        continue
    targets.add(path)
    for cut in range(1, len(path)):          # 各级分组
        targets.add(path[:cut])

results = {}
errors = {}
ordered = sorted(targets, key=lambda row: (len(row), row))
for index, path in enumerate(ordered, 1):
    args = list(path) + ["--help"]
    key = ".".join(path)
    try:
        envelope = dr.run_lyra(args, CWD, 60, [], [], extra_env=ENV)
        body = (envelope or {}).get("result") or {}
        text = str(body.get("output") or "")
        if not text:
            text = "ERR_CODE=%s MSG=%s" % (body.get("err_code"), body.get("err_msg"))
        results[key] = text[:6000]
    except Exception as error:  # noqa: BLE001
        errors[key] = str(error).replace("\n", " ")[:200]
    if index % 25 == 0:
        print("  进度 %d/%d" % (index, len(ordered)), flush=True)

out = ROOT / "skills" / "guzhu-hao" / "references" / "cli-help.json"
out.write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
print("抓到 %d 个目标的 help（失败 %d）-> %s (%.0f KB)"
      % (len(results), len(errors), out.name, out.stat().st_size / 1024))
if errors:
    print("失败的：")
    for key, message in list(errors.items())[:10]:
        print("   %-40s %s" % (key, message))
