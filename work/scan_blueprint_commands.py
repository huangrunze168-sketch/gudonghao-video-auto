"""从剪映官方 canvas_agent runtime 中提取 lyra-cli 命令契约（只读侦查）。"""
import re
from pathlib import Path

APP = Path(
    r"C:\Users\Administrator\AppData\Local\JianyingPro\Apps\11.5.0.14471"
    r"\Resources\canvas_agent\runtime\app-server.mjs"
)
text = APP.read_text(encoding="utf-8", errors="replace")
print("file bytes:", len(text))

PREFIXES = (
    '["draft","blueprint"',
    '["draft","project"',
    '["draft","canvas"',
    '["draft","render"',
    '["media"',
    '["material"',
)


def show(prefix, span=460, limit=14):
    print("=" * 24, prefix)
    seen = set()
    count = 0
    for match in re.finditer(re.escape(prefix), text):
        segment = text[match.start():match.start() + span].replace("\n", " ")
        if segment in seen:
            continue
        seen.add(segment)
        count += 1
        if count > limit:
            break
        print("-", segment)


for prefix in PREFIXES:
    show(prefix)

print("=" * 24, "flag context")
for flag in ("--current-only", "--selection-file", "--base-revision", "--allow-existing-subtitle-changes",
             "--source-draft", "--dir", "--ref"):
    hits = [m.start() for m in re.finditer(re.escape(flag), text)]
    print(f"{flag}: {len(hits)} hits")
