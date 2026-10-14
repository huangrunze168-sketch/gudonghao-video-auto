"""在 CLI 二进制里查找客户端来源标识、MotionGraph/Lumi 端点等可配置线索。"""
import re
import sys
from pathlib import Path

PATTERNS = [
    "client_source", "clientSource", "client-source", "invalid_client_source",
    "app_id", "appId", "app-id", "device_id", "register", "x-app",
    "lumi", "Lumi", "motiongraph", "MotionGraph", "submit stage",
    "http", "endpoint", "api_base", "apiBase", "base_url", "baseUrl",
    "VIDEO_TRACKING", "video_tracking", "tracker_type", "tracker-type",
]

for label in sys.argv[1:]:
    path = Path(label)
    text = path.read_bytes().decode("latin-1")
    print("=" * 26, path.parent.name)
    for pattern in PATTERNS:
        count = text.count(pattern)
        if not count:
            continue
        samples = []
        start = 0
        for _ in range(3):
            index = text.find(pattern, start)
            if index < 0:
                break
            context = re.sub(r"[\x00-\x1f]+", " ", text[max(0, index - 55):index + 55])
            samples.append(context.encode("ascii", "replace").decode("ascii").strip()[:105])
            start = index + len(pattern)
        print(f"  {pattern:22} x{count:<3} | " + " || ".join(samples))
