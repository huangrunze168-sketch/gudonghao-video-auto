"""从 CLI 二进制挖掘剩余未成功项的真实约束（task id、段类型、下载、模板、本地生成）。"""
import re
import sys
from pathlib import Path

EXE = Path(sys.argv[1])
text = EXE.read_bytes().decode("latin-1")

GROUPS = {
    "task id 来源": ["task_id", "output-track-data", "output_track_data", "query",
                     "poll-interval", "commit-immediately", "track_data"],
    "滤镜/特效段": ["segment_filter", "segment_video_effect", "REMOVE_FILTER",
                    "filter add", "property=filter", "PROPERTY_FILTER"],
    "素材下载": ["material download", "--resource-id", "resource-dir", "download_urls",
                 "resource_pool", "unsupported material type"],
    "模板包": ["template add", "unzip failed", "--template-seg-id", "template://",
               "template publish", "template zip"],
    "本地生成": ["local_motiongraph", "motiongraph_export", "lumi_local",
                 "local runtime data manifest", "provider"],
    "lint 仓库": ["repo root does not look like lyra-cli", "lint command"],
}

for title, patterns in GROUPS.items():
    print("=" * 22, title)
    for pattern in patterns:
        count = text.count(pattern)
        if not count:
            continue
        samples = []
        start = 0
        while len(samples) < 2:
            index = text.find(pattern, start)
            if index < 0:
                break
            context = re.sub(r"[\x00-\x1f]+", " ", text[max(0, index - 70):index + 70])
            samples.append(context.encode("ascii", "replace").decode("ascii").strip()[:150])
            start = index + len(pattern)
        print(f"  {pattern:34} x{count:<3} {samples[0] if samples else ''}")
        if len(samples) > 1:
            print(f"  {'':34}      {samples[1]}")
