"""实测 C1/C3：套用一次动效后，草稿里到底有几段带 <template>。

C1: 一次 update 是作用于整组还是单段
C3: `--mode draft` 的重复识别在草稿侧是多段还是单段
"""
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "engine"))
import lyra_cli  # noqa: E402

DRAFT_ROOT = Path(r"C:\Users\Administrator\AppData\Local\JianyingPro\User Data\Projects\com.lveditor.draft")
CANDIDATES = ["headless-engine-20261010-005054", "headless-final-lyrics", "headless-official3"]


def inspect(name):
    folder = DRAFT_ROOT / name
    timeline = folder / "Timelines"
    files = list(timeline.glob("*/draft_content.json")) if timeline.is_dir() else []
    if not files:
        return None
    import subprocess
    install = Path(r"C:\Users\Administrator\AppData\Local\JianyingPro\Apps\11.5.0.14471")
    out = ROOT / "work" / f"cmp-{name}.json"
    subprocess.run([sys.executable, str(ROOT / "bridge" / "windows_crypto.py"), "decrypt",
                    "--install-dir", str(install), str(files[0]), str(out)],
                   capture_output=True, text=True, encoding="utf-8", errors="replace")
    if not out.is_file():
        return None
    data = json.loads(out.read_text(encoding="utf-8"))
    templates = data.get("materials", {}).get("text_templates", []) or []
    kinds = {}
    for node in templates:
        key = node.get("type") or "?"
        kinds[key] = kinds.get(key, 0) + 1
    texts = data.get("materials", {}).get("texts", []) or []
    return {"path": str(files[0]), "text_templates": len(templates), "kinds": kinds,
            "texts": len(texts),
            "lyric_effects": len(data.get("lyrics_effects", []) or [])}


for name in CANDIDATES:
    result = inspect(name)
    if result:
        print(f"== {name}")
        print(f"   text_templates={result['text_templates']} kinds={result['kinds']}")
        print(f"   texts={result['texts']} lyrics_effects={result['lyric_effects']}")
    else:
        print(f"== {name}: 无时间线")
