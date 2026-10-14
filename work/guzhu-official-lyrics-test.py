# -*- coding: utf-8 -*-
"""验证官方歌词链路：lyrics recognize 是否生成可套动效的 <text> 段。"""
import collections
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\Administrator\Documents\剪映")
sys.path.insert(0, str(ROOT / "engine"))

import lyra_cli  # noqa: E402
import windows_runtime  # noqa: E402

DR = Path(windows_runtime.DRAFT_ROOT).resolve()
NAME = "guzhu-lyric-text"
WS = Path(r"C:\Temp\lyric-ws")

id_map = json.loads((WS / "id_map.json").read_text(encoding="utf-8"))
segs = {item["xml_id"]: item["seg_id"] for item in id_map}
print("audio 段:", {k: v for k, v in segs.items() if k.startswith("a")})

# a6/a7 是音乐轨；主歌段通常排在最后
target = segs.get("a7") or segs.get("a6")
print("识别目标 seg-id:", target)
try:
    result = lyra_cli.lyrics_recognize(str(DR), "local://" + NAME, language="zh",
                                       mode="segment", seg_id=target, timeout=1800)
    sentences = lyra_cli.lyrics_recognized_sentences(result)
    print("识别句数:", len(sentences))
    print("前 6 句:", sentences[:6])
    cues = lyra_cli.recognized_cues(result)
    print("cues 前 3 条:", json.dumps(cues[:3], ensure_ascii=False))
except Exception as error:  # noqa: BLE001 - 探测官方识别是否可用
    print("识别失败:", str(error)[:500])

# 官方只写 Timelines/<id>/，先同步镜像再 sync，否则读到的还是旧内容
folder = DR / NAME
timelines = sorted((folder / "Timelines").glob("*/draft_content.json"))
if timelines:
    source = max(timelines, key=lambda path: path.stat().st_mtime_ns)
    payload = source.read_bytes()
    for mirror in (folder / "draft_content.json", folder / "template-2.tmp",
                   source.parent / "template-2.tmp"):
        shutil.copyfile(source, mirror)
    print("已同步镜像:", source.parent.name)

WS2 = Path(r"C:\Temp\lyric-ws2")
if WS2.exists():
    shutil.rmtree(WS2)
for arguments in (["init", "--workspace", str(WS2)],
                  ["sync", "--workspace", str(WS2), "--ref", "local://" + NAME,
                   "--draft-root", str(DR)]):
    completed = subprocess.run([sys.executable, str(ROOT / "engine" / "draftediting_runtime.py"),
                                *arguments], capture_output=True, cwd=str(ROOT))
    print(arguments[0], "rc =", completed.returncode)
    if completed.returncode:
        print(completed.stderr.decode("utf-8", "replace")[-400:])

xml = (WS2 / "current_draft.xml").read_text(encoding="utf-8", errors="replace")
print("\n标签统计:", dict(collections.Counter(re.findall(r"<(\w+)", xml))))
print("\n== <text> 段 ==")
for match in re.finditer(r"<text\b[^>]*>.*?</text>", xml, re.S):
    body = match.group(0)
    text = re.search(r'<sub text="([^"]*)"', body)
    ident = re.search(r'<text id="([^"]*)"', body)
    print("  id=%-6s template=%-5s text=%s" % (ident.group(1) if ident else "?",
                                               "<template" in body,
                                               (text.group(1) if text else "?")[:30]))
print("\n== 新 id_map 的 t* 段数量 ==", sum(1 for k in
      (item["xml_id"] for item in json.loads((WS2 / "id_map.json").read_text(encoding="utf-8")))
      if k.startswith("t")))
