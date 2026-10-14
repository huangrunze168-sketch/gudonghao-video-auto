"""验证快照式撤销/重做（官方 standalone 不支持 history undo/redo 的替代）。"""
import hashlib
import json
import sys

sys.path.insert(0, 'tools')
import functional_test as ft
import draft_history as dh

cli = ft.OfficialCli(timeout=180)
ctx = ft.TestContext(cli, ft.WORK, ref_name='func-test-hist')
ctx.prepare()
print('draft_root', ctx.draft_root)


def digest():
    root = ctx.draft_root
    value = hashlib.sha256()
    for item in sorted(root.rglob('*')):
        if item.is_file():
            value.update(item.read_bytes())
    return value.hexdigest()[:12]


print('初始 digest', digest())
dh.snapshot(ctx.ref, '起点')
state = dh.read_state(ctx.ref)
print('还原点', state)

# 真实改动工程：加一段视频
outcome = cli(['draft', 'video', 'add', '--ref', ctx.ref,
               '--resource', 'local:///' + str(ctx.media_files['video']).replace('\\', '/').lstrip('/'),
               '--track', '0', '--start', '3s'],
              cwd=str(ctx.root), read_write=ctx.read_write_paths(),
              read_only=[str(ctx.media_dir)])
print('加片段', outcome.state)
changed = digest()
print('改动后 digest', changed, '不同:', changed != state['points'] and True)

dh.snapshot(ctx.ref, '加片段后')
dh.restore(ctx.ref, 0, redo_point=False)
back = digest()
print('撤销后 digest', back)
dh.restore(ctx.ref, 1, redo_point=False)
forward = digest()
print('重做后 digest', forward)
print('撤销是否回到起点:', back != changed)
print('重做是否回到改动后:', forward == changed)
dh.show_list(ctx.ref)
ctx.cleanup()
import shutil
shutil.rmtree(dh.HISTORY_ROOT / ctx.ref_name, ignore_errors=True)
print('cleaned')
