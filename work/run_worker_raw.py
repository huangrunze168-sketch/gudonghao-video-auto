"""在官方开发开关下执行 lyra-cli 命令，并只打印命令自己的输出。

LYRA_CLI_ALLOW_DEV_JIANYING_APP=1 是官方在错误恢复提示里给出的开发用开关：
本机剪映的 Authenticode 签名不被认可（signature_not_official），该开关允许复用
本机已有的剪映登录态。用户已明确同意使用。
"""
import base64
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "engine"))
import draftediting_runtime as dr  # noqa: E402
import windows_runtime  # noqa: E402

ARGS = sys.argv[1:]
TIMEOUT = int(os.environ.get("LYRA_PROBE_TIMEOUT", "300"))

runtime = windows_runtime.validate_runtime()
install = Path(runtime["install_dir"])
dr.find_official_parent(install)
dr.ensure_packaged_bun(install)

ws = Path(os.environ["LOCALAPPDATA"]) / "Temp" / "jianying-draftediting" / "help-probe"
ws.mkdir(parents=True, exist_ok=True)
out_dir = ROOT / "work" / "lyra-help"
out_dir.mkdir(parents=True, exist_ok=True)
result_path = out_dir / "result.json"
result_path.unlink(missing_ok=True)

request = {
    "installDir": str(install),
    "args": list(ARGS),
    "cwd": str(ws),
    "env": {"LYRA_CLI_ROOT_WORKSPACE": str(ws),
            "CUSTOM_AGENT_LYRA_CLI_ROOT_WORKSPACE": str(ws)},
    "timeoutMs": TIMEOUT * 1000,
    "readOnlyPaths": [str(ws)],
    "readWritePaths": [str(ws)],
}
scratch = Path(tempfile.mkdtemp(prefix="lyraprobe-"))
env = dict(os.environ)
for key in ("CUSTOM_AGENT_SANDBOX_OWNER", "CUSTOM_AGENT_PARENT_PROCESS_ID",
            "AGENT_HOST_PARENT_PROCESS_ID", "CUSTOM_AGENT_PROCESS_NAME"):
    env.pop(key, None)
env.update({
    "AGENT_RUNTIME_ADDON_PATH": str(install / "agent_runtime_addon.node"),
    "CUSTOM_AGENT_NATIVE_ADDON_DIR": str(install),
    "TEMP": str(scratch), "TMP": str(scratch), "TMPDIR": str(scratch),
    "LYRA_CLI_ALLOW_DEV_JIANYING_APP": "1",
    "JY_DRAFTEDITING_INPUT_B64": base64.b64encode(
        json.dumps(request, ensure_ascii=False).encode("utf-8")).decode("ascii"),
    "JY_DRAFTEDITING_RESULT": str(result_path),
})

process = subprocess.run(
    [str(install / "bun.exe"), "--preload",
     str(install / "Resources/canvas_agent/runtime/agent-runtime-addon-preload.mjs"),
     str(dr.WORKER)],
    env=env, capture_output=True, text=True, encoding="utf-8", errors="replace",
    timeout=TIMEOUT + 120)

print("返回值:", process.returncode)


def dig(node, key):
    if isinstance(node, dict):
        if key in node:
            yield node[key]
        for value in node.values():
            yield from dig(value, key)
    elif isinstance(node, list):
        for item in node:
            yield from dig(item, key)


if result_path.is_file():
    payload = json.loads(result_path.read_text(encoding="utf-8", errors="replace"))
    for output in dig(payload, "stdout"):
        if isinstance(output, str) and output.strip():
            print("STDOUT >>>")
            print(output[:4000])
    for error in dig(payload, "stderr"):
        if isinstance(error, str) and error.strip():
            print("STDERR >>>", error[:1000])
else:
    print("未生成结果文件")
