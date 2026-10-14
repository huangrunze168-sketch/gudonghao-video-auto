"""验证 base-revision 算法：FNV-1a 64 对 target_draft.xml 的内容哈希。"""
import os
from pathlib import Path

WS = Path(os.environ["LOCALAPPDATA"]) / "Temp" / "jianying-draftediting" / "apply2"
EXPECTED = "145c3c70bb7f2c66"


def fnv1a64(text):
    value = 0xCBF29CE484222325
    for byte in text.encode("utf-8"):
        value ^= byte
        value = (value * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF
    return format(value, "016x")


for name in ("target_draft.xml", "current_draft.xml"):
    path = WS / name
    if not path.is_file():
        print(name, "missing")
        continue
    text = path.read_text(encoding="utf-8")
    print(name, "fnv1a64=", fnv1a64(text), "expected=", EXPECTED,
          "match=", fnv1a64(text) == EXPECTED)
