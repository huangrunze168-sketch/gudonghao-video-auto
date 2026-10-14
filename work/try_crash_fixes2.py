"""确认 video-tracking 与 blueprint patch 在给出必填参数后的真实行为。"""
import sys

sys.path.insert(0, 'tools')
import functional_test as ft

cli = ft.OfficialCli(timeout=180)
ctx = ft.TestContext(cli, ft.WORK, ref_name='func-test-fix2')
ctx.prepare()
video = ctx.seg_id
print('video seg', video)


def run(name, args):
    outcome = cli(args, cwd=str(ctx.root), read_write=ctx.read_write_paths(),
                  read_only=[str(ctx.media_dir)])
    print(f'--- {name}: {outcome.state} exit={outcome.exit_code}')
    print('   ', (outcome.message or '')[:240])
    return outcome


run('video-tracking(seg-id+source+type1)',
    ['draft', 'algo', 'video-tracking', '--ref', ctx.ref,
     '--seg-id', video, '--source-seg-id', video, '--tracker-type', '1',
     '--center-x', '0.5', '--center-y', '0.5', '--width', '0.2', '--height', '0.2'])
run('video-tracking(仅 tracker-type1)',
    ['draft', 'algo', 'video-tracking', '--ref', ctx.ref,
     '--seg-id', video, '--source-seg-id', video, '--tracker-type', '1'])

ws = ctx.fresh_workspace(clear=True)
if run('blueprint init', ['draft', 'blueprint', 'init', '--workspace', str(ws)]).ok:
    for label, body in (('空 patch', '<patch></patch>'),
                        ('update 节点', '<patch><update target="none"><x/></update></patch>')):
        patch = ctx.out_dir / f'patch-{len(label)}.xml'
        patch.write_text(body, encoding='utf-8', newline='\n')
        run(f'blueprint patch({label})',
            ['draft', 'blueprint', 'patch', '--workspace', str(ws),
             '--patch-file', str(patch), '--dry-run'])
ctx.cleanup()
print('cleaned')
