"""重度深挖：实测剪映官方 CLI 每条命令的可用性。

做法：给每条命令传一个**必然无效的草稿引用**，让它在解析/校验阶段就失败，
从而既不改动任何草稿，又能从官方返回的错误里判断该命令的真实状态：

- ``usage`` / ``cli parse error``  → 命令存在且参数可解析（**可用**，只是缺参数）
- ``not implemented``             → 官方尚未实现
- ``unauthorized`` / host 校验     → 沙箱内不可用
- 网络类错误                      → 需要联网，本机沙箱没有网络
- 其他 runtime 错误               → 归入"可用但需要更完整的输入"

跳过 ``upgrade`` 等危险命令。

产出 ``references/cli-status.json``。
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
SKIP = {"upgrade", "auth.login", "auth.logout"}
PROBE_REF = "local://__guzhu_probe_missing__"

COMMANDS = json.loads((ROOT / "engine" / "lyra_commands.json").read_text(encoding="utf-8"))
targets = []
for item in COMMANDS.get("commands") or []:
    path = tuple(str(part) for part in (item.get("path") or []))
    if path and ".".join(path) not in SKIP:
        targets.append(path)


def classify(message):
    body = message
    if "not implemented" in body or "NotImplemented" in body:
        return "not-implemented"
    if "unauthorized" in body or "signature" in body:
        return "blocked"
    if "network" in body.lower() or "-100015" in body:
        return "needs-network"
    if "cli parse error" in body or "ValidationError" in body or "usage" in body:
        return "usable"
    if "not found" in body or "cannot find" in body or "does not exist" in body:
        return "usable"          # 命令跑通了，只是引用不存在
    return "usable"


results = {}
counts = {}
for index, path in enumerate(sorted(targets, key=lambda row: (len(row), row)), 1):
    key = ".".join(path)
    args = list(path) + ["--ref", PROBE_REF]
    status, evidence = "usable", ""
    try:
        envelope = dr.run_lyra(args, CWD, 60, [], [], extra_env=ENV)
        body = (envelope or {}).get("result") or {}
        code = body.get("err_code")
        if code in (0, None):
            status = "usable"
            evidence = "返回成功"
        else:
            evidence = str(body.get("err_msg") or "")[:200]
            status = classify(evidence)
    except Exception as error:  # noqa: BLE001
        evidence = str(error).replace("\n", " ")[:300]
        status = classify(evidence)
    results[key] = {"status": status, "evidence": evidence}
    counts[status] = counts.get(status, 0) + 1
    if index % 25 == 0:
        print("  进度 %d/%d" % (index, len(targets)), flush=True)

out = ROOT / "skills" / "guzhu-hao" / "references" / "cli-status.json"
out.write_text(json.dumps({"counts": counts, "commands": results},
                          ensure_ascii=False, indent=1), encoding="utf-8")
print("\n实测完成：%d 条命令" % len(results))
for status, count in sorted(counts.items(), key=lambda pair: -pair[1]):
    print("   %-16s %d" % (status, count))
print("已写出", out.name)
