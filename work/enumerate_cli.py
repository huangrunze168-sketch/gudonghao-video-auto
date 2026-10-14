"""枚举官方 lyra-cli 的命令树，用于评估无头能力覆盖范围。"""
import base64
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "engine"))
import draftediting_runtime as dr  # noqa: E402
import windows_runtime  # noqa: E402

DOMAINS = [
    ["draft", "algo"],
    ["draft", "video"],
    ["draft", "text"],
    ["draft", "subtitle"],
    ["draft", "template"],
    ["draft", "effect"],
    ["draft", "audio"],
    ["draft", "keyframe"],
    ["material"],
    ["media"],
    ["lint"],
]

runtime = windows_runtime.validate_runtime()
install = Path(runtime["install_dir"])
dr.find_official_parent(install)
dr.ensure_packaged_bun(install)
ws = Path(os.environ["LOCALAPPDATA"]) / "Temp" / "jianying-draftediting" / "help-probe"
ws.mkdir(parents=True, exist_ok=True)


def run_help(args):
    out_dir = ROOT / "work" / "lyra-help"
    out_dir.mkdir(parents=True, exist_ok=True)
    result_path = out_dir / f"help-{'_'.join(args)}.json"
    result_path.unlink(missing_ok=True)
    request = {
        "installDir": str(install), "args": list(args) + ["--help"], "cwd": str(ws),
        "env": {"LYRA_CLI_ROOT_WORKSPACE": str(ws),
                "CUSTOM_AGENT_LYRA_CLI_ROOT_WORKSPACE": str(ws)},
        "timeoutMs": 120000, "readOnlyPaths": [str(ws)], "readWritePaths": [str(ws)],
    }
    scratch = Path(tempfile.mkdtemp(prefix="enum-"))
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
    try:
        subprocess.run([str(install / "bun.exe"), "--preload",
                        str(install / "Resources/canvas_agent/runtime/agent-runtime-addon-preload.mjs"),
                        str(dr.WORKER)],
                       env=env, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=90)
    except subprocess.TimeoutExpired:
        return "__TIMEOUT__"
    if not result_path.is_file():
        return ""
    payload = json.loads(result_path.read_text(encoding="utf-8", errors="replace"))

    def dig(node, key):
        if isinstance(node, dict):
            if key in node:
                yield node[key]
            for value in node.values():
                yield from dig(value, key)
        elif isinstance(node, list):
            for item in node:
                yield from dig(item, key)

    for text in dig(payload, "stdout"):
        if isinstance(text, str) and "SUBCOMMANDS" in text:
            return text
    return ""


for domain in DOMAINS:
    text = run_help(domain)
    name = " ".join(domain)
    if text == "__TIMEOUT__":
        print(f"== {name}: help 超时（该域可能需要在草稿上下文中调用）")
        continue
    if not text:
        print(f"== {name}: 无子命令列表")
        continue
    block = text.split("SUBCOMMANDS:", 1)[-1].split("EXAMPLES", 1)[0]
    names = re.findall(r"^\s{2}([a-z][a-z0-9-]+)\s{2,}", block, re.MULTILINE)
    print(f"== {name} ({len(names)}): {', '.join(names)}")
