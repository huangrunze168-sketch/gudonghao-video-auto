"""检查官方 preload 如何加载 native addon，判断能否从工作区运行。"""
import re
from pathlib import Path

PRELOAD = Path(r"C:\Users\Administrator\AppData\Local\JianyingPro\Apps\11.5.0.14471"
               r"\Resources\canvas_agent\runtime\agent-runtime-addon-preload.mjs")
text = PRELOAD.read_text(encoding="utf-8", errors="replace")
print("bytes:", len(text), "lines:", text.count("\n") + 1)

for key in ("AGENT_RUNTIME_ADDON_PATH", "CUSTOM_AGENT_NATIVE_ADDON_DIR", ".node", "dlopen",
            "import.meta", "runtime-sandbox-bridge", "Bun.plugin"):
    hits = list(re.finditer(re.escape(key), text))
    print(f"== {key}: {len(hits)}")
    for match in hits[:3]:
        print("  ...", text[max(0, match.start() - 150):match.start() + 190].replace("\n", " "))
