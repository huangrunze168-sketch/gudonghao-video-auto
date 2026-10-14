"""真实建工程并查看 extract summary 的结构，用于确认 segment id 的正确来源。"""
import json
import os
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, 'tools')
import functional_test as ft

cli = ft.OfficialCli(timeout=120)
root = ft.WORK
root.mkdir(parents=True, exist_ok=True)
ctx = ft.TestContext(cli, root, ref_name='func-test-struct')
ctx.prepare()
print('draft_root', ctx.draft_root, 'exists', bool(ctx.draft_root and ctx.draft_root.is_dir()))
print('seed steps', json.dumps(ctx.seed_steps, ensure_ascii=False)[:800])
outcome = cli(['draft', 'extract', 'summary', '--ref', ctx.ref],
              cwd=str(root), read_write=ctx.read_write_paths())
structure = ft.parse_json_result(outcome)
print('--- structure ---')
print(json.dumps(structure, ensure_ascii=False, indent=1)[:2500])
print('--- ids by type ---', json.dumps(ctx.ids_by_type, ensure_ascii=False)[:400])
print('--- seg_id ---', ctx.seg_id)
ctx.cleanup()
print('cleaned')
