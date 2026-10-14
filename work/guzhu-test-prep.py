# -*- coding: utf-8 -*-
"""从模板包里导出原始 TTS 配音，供对照测试使用。"""
import sys
from pathlib import Path

SKILL = Path(r"C:\Users\Administrator\Documents\剪映\skills\guzhu-hao\scripts")
sys.path.insert(0, str(SKILL))

from guzhu_common import EngineCrypto, resolve_project  # noqa: E402
from guzhu_jypack import read_package  # noqa: E402
from guzhu_timeline import Editor, inspect_template, range_of  # noqa: E402

SRC = Path(r"C:\Users\Administrator\.dsh\attachments\v1\files\1b"
           r"\1b4df543f999b6d91fd0b4e328a108a2c0bb320ea7474fc1bac469c9176a61f2\测试.jypack")
OUT = Path(r"C:\Users\Administrator\Documents\剪映\work\guzhu-test")
(OUT / "voice").mkdir(parents=True, exist_ok=True)

crypto = EngineCrypto(resolve_project())
package = read_package(SRC, crypto)
skeleton = inspect_template(package.timeline)
editor = Editor(package.timeline)

for index, group in enumerate(skeleton.groups, 1):
    node = editor.node(group.tts_material)
    relative = node["path"].split("_##/")[-1]
    target = OUT / "voice" / ("line-%02d.wav" % index)
    target.write_bytes(package.read(relative))
    start, duration = range_of(group.tts_segment)
    print("%d  %-24s 素材 %8d us  片段 %8d us @%d  → %s"
          % (index, node.get("name"), node.get("duration"), duration, start, target.name))
print("片头总长:", skeleton.intro_end, "us; 主歌:", skeleton.main_duration, "us")
