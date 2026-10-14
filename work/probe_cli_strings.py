"""在 lyra-cli 二进制里搜索命令实现相关的字符串，对比 11.5 与 11.6 的能力差异。"""
import re
import sys
from pathlib import Path

PATTERNS = [
    b"not implemented yet",
    b"material recommend",
    b"material similar",
    b"recommend",
    b"similar",
    b"upgrade",
    b"invalid_client_source",
    b"Lumi",
    b"video_tracking",
    b"video-tracking",
    b"blueprint patch",
    b"is only available when lyra-cli is embedded",
    b"EffectABConfig",
    b"e06d7363",
]

for label in sys.argv[1:]:
    path = Path(label)
    data = path.read_bytes()
    print("=" * 30, path.parent.name, f"({len(data)} bytes)")
    text = data.decode("latin-1")
    for pattern in PATTERNS:
        needle = pattern.decode("latin-1")
        count = text.count(needle)
        if count:
            # 取第一处上下文，帮助判断是否是命令定义而不是错误文案
            index = text.find(needle)
            context = text[max(0, index - 70):index + 70]
            context = re.sub(r"[\x00-\x1f]+", " ", context)
            context = context.encode("ascii", "replace").decode("ascii")
            print(f"  {needle:52} x{count:<4} ...{context.strip()[:100]}...")
        else:
            print(f"  {needle:52} absent")
