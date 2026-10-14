"""诊断：整首歌的官方歌词识别为什么被判为失败。

绕开 lyra_cli._result 的 err_code 检查，直接读官方 envelope，
拿到完整的 err_code / err_msg / 返回体大小。
"""
import json
import sys
import tempfile
import uuid
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(r"C:\Users\Administrator\Documents\剪映")
sys.path.insert(0, str(ROOT / "skills" / "guzhu-hao" / "scripts"))
sys.path.insert(0, str(ROOT / "engine"))

import draftediting_runtime as dr  # noqa: E402
import guzhu_batch as gb  # noqa: E402
from guzhu_common import EngineCrypto  # noqa: E402
from guzhu_jypack import read_package  # noqa: E402

project = str(ROOT)
crypto = EngineCrypto(project)
jypack = next((ROOT / "work" / "guzhu-sz" / "jypack").glob("*.jypack"))
print("草稿包:", jypack.name)
package = read_package(jypack, crypto)
draft_root = gb.draft_root(project)
folder, _count = gb.install_draft(jypack, draft_root, "guzhu-diag-sz")
ref = "local://" + folder.name

workspace = Path(tempfile.gettempdir()) / ("guzhu-diag-%s" % uuid.uuid4().hex[:8])
gb._project_script(project, "draftediting_runtime.py", ["init", "--workspace", str(workspace)])
gb._project_script(project, "draftediting_runtime.py",
                   ["sync", "--workspace", str(workspace), "--ref", ref,
                    "--draft-root", str(draft_root)])
id_map = json.loads((workspace / "id_map.json").read_text(encoding="utf-8"))
skeleton = gb.inspect_template(package.timeline)
music_segment = skeleton.main_music[0][1].get("id")
print("主歌音乐段:", music_segment, " 工作区段数:", len(id_map))

envelope = dr.run_lyra(
    ["draft", "lyrics", "recognize", "--ref", ref, "--language", "zh",
     "--mode", "segment", "--seg-id", music_segment, "--clear-previous", "true"],
    Path(project) / "engine", 1800, [draft_root], [],
    extra_env={"LYRA_CLI_ALLOW_DEV_JIANYING_APP": "1"})

parsed = envelope.get("result") if isinstance(envelope, dict) else {}
print("\n== envelope 顶层键 ==", list(envelope.keys()) if isinstance(envelope, dict) else type(envelope))
if isinstance(parsed, dict):
    print("err_code =", parsed.get("err_code"))
    print("err_msg  =", str(parsed.get("err_msg"))[:1200])
    for key in ("output", "result", "affected_segments"):
        value = parsed.get(key)
        if value is None:
            continue
        size = len(json.dumps(value, ensure_ascii=False)) if not isinstance(value, str) else len(value)
        print("%s 长度 = %d" % (key, size))
    segments = parsed.get("affected_segments")
    if isinstance(segments, list):
        print("识别段数 =", len(segments))
        sentences = sum(len((item.get("asr") or {}).get("sentences") or []) for item in segments)
        print("句子数 =", sentences)
else:
    print(json.dumps(parsed, ensure_ascii=False)[:1500])
