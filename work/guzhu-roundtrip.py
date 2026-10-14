# -*- coding: utf-8 -*-
"""回环验证：读取 测试.jypack，原样重新加密打包，比对结构是否完全保真。"""
import sys
import time
from pathlib import Path

SKILL = Path(r"C:\Users\Administrator\Documents\剪映\skills\guzhu-hao\scripts")
sys.path.insert(0, str(SKILL))

from guzhu_common import EngineCrypto, resolve_project  # noqa: E402
from guzhu_jypack import read_package, seal  # noqa: E402

SRC = Path(r"C:\Users\Administrator\.dsh\attachments\v1\files\1b"
           r"\1b4df543f999b6d91fd0b4e328a108a2c0bb320ea7474fc1bac469c9176a61f2\测试.jypack")
OUT = Path(r"C:\Users\Administrator\Documents\剪映\work\guzhu-roundtrip\roundtrip.jypack")

project = resolve_project()
print("project:", project)
crypto = EngineCrypto(project)

started = time.monotonic()
package = read_package(SRC, crypto)
print("读取+解密 %.2fs，条目 %d，时间线加密=%s，元信息加密=%s"
      % (time.monotonic() - started, len(package.names()),
         package.timeline_encrypted, package.metadata_encrypted))
print("时间线 id:", package.timeline.get("id"), "duration:", package.timeline.get("duration"))

started = time.monotonic()
seal(package, crypto, OUT)
print("重新加密打包 %.2fs，输出 %.1f MB" % (time.monotonic() - started, OUT.stat().st_size / 1e6))

again = read_package(OUT, crypto)
print("条目集合一致:", set(package.names()) == set(again.names()))
differing = [name for name in package.names()
             if name not in ("draft_content.json", "draft_meta_info.json")
             and package.entries[name].data != again.entries[name].data]
print("素材字节不同的条目:", differing)
print("时间线内容一致:", package.timeline == again.timeline)
print("元信息内容一致:", package.metadata == again.metadata)
