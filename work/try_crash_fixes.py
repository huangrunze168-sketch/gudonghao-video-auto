"""实测 video-tracking 与 blueprint patch 的正确参数组合。"""
import json
import sys

sys.path.insert(0, 'tools')
import functional_test as ft

cli = ft.OfficialCli(timeout=180)
ctx = ft.TestContext(cli, ft.WORK, ref_name='func-test-fix')
ctx.prepare()
video = ctx.seg_id
text = ctx.ids_by_type.get('text', [None])[0]
print('video seg', video, 'text seg', text)


def run(name, args):
    outcome = cli(args, cwd=str(ctx.root), read_write=ctx.read_write_paths(),
                  read_only=[str(ctx.media_dir)])
    print(f'--- {name}: {outcome.state} exit={outcome.exit_code}')
    print('   ', (outcome.message or '')[:230])
    return outcome


base = ['draft', 'algo', 'video-tracking', '--ref', ctx.ref, '--source-seg-id', video]
run('tracker-type=1 + box', base + ['--tracker-type', '1',
                                   '--center-x', '0.5', '--center-y', '0.5',
                                   '--width', '0.2', '--height', '0.2'])
run('无 tracker-type + box', base + ['--center-x', '0.5', '--center-y', '0.5',
                                    '--width', '0.2', '--height', '0.2'])
run('tracker-type=motion + box', base + ['--tracker-type', 'motion',
                                        '--center-x', '0.5', '--center-y', '0.5',
                                        '--width', '0.2', '--height', '0.2'])
run('tracker-type=1 仅此', base + ['--tracker-type', '1'])

# blueprint：先 init 工作区，再 patch
ws = ctx.fresh_workspace(clear=True)
init = run('blueprint init', ['draft', 'blueprint', 'init', '--workspace', str(ws)])
if init.ok:
    selection = ctx.out_dir / 'edit.selection'
    selection.write_text('<selection><main/></selection>', encoding='utf-8', newline='\n')
    run('blueprint patch(带参数)',
        ['draft', 'blueprint', 'patch', '--workspace', str(ws),
         '--selection-file', str(selection), '--ref', ctx.ref])
    print('workspace 内容:', sorted(p.name for p in ws.iterdir()))
ctx.cleanup()
print('cleaned')
