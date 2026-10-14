"""继续定位 blueprint patch 崩溃与 effect generate 的 Lumi 404。"""
import json
import sys

sys.path.insert(0, 'tools')
import functional_test as ft

cli = ft.OfficialCli(timeout=240)
ctx = ft.TestContext(cli, ft.WORK, ref_name='func-test-fix4')
ctx.prepare()
video = ctx.seg_id


def run(name, args):
    outcome = cli(args, cwd=str(ctx.root), read_write=ctx.read_write_paths(),
                  read_only=[str(ctx.media_dir)])
    print(f'--- {name}: {outcome.state} exit={outcome.exit_code}')
    print('   ', (outcome.message or '')[:220])
    return outcome


ws = ctx.fresh_workspace(clear=True)
run('blueprint init', ['draft', 'blueprint', 'init', '--workspace', str(ws)])
run('blueprint sync', ['draft', 'blueprint', 'sync', '--workspace', str(ws),
                       '--ref', ctx.ref])
print('workspace:', sorted(p.name for p in ws.iterdir()))

patches = {
    'insert 节点': '<patch><insert path="/draft"></insert></patch>',
    '空 patch 无 dry-run': '<patch></patch>',
    'replace 节点': '<patch><replace path="/draft"></replace></patch>',
}
for label, body in patches.items():
    patch = ctx.out_dir / ('patch-' + str(abs(hash(label))) + '.xml')
    patch.write_text(body, encoding='utf-8', newline='\n')
    run(f'patch({label})', ['draft', 'blueprint', 'patch', '--workspace', str(ws),
                            '--patch-file', str(patch), '--dry-run'])

# effect generate：cloud 与 local 两种执行方式
run('effect generate(cloud)', ['draft', 'effect', 'generate', '--ref', ctx.ref,
                               '--type', 'motiongraph', '--execution', 'cloud',
                               '--prompt', '花', '--start', '0s', '--duration', '1s',
                               '--name', 'func-test'])
run('effect generate(local)', ['draft', 'effect', 'generate', '--ref', ctx.ref,
                               '--type', 'motiongraph', '--execution', 'local',
                               '--prompt', '花', '--start', '0s', '--duration', '1s',
                               '--name', 'func-test'])
help_text = ft.load_help_text(('draft', 'effect', 'generate')) or ''
print('=== effect generate 关键选项 ===')
for line in help_text.replace('\r', '').split('\n'):
    if any(word in line for word in ('execution', 'cloud', 'local', 'lumi', 'Lumi', 'endpoint')):
        print('   ', line.strip()[:150])
ctx.cleanup()
print('cleaned')
