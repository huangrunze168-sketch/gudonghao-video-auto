"""验证：顶层 filter/effect add 是否产生独立段，从而让 remove/update 可用。"""
import json
import sys

sys.path.insert(0, 'tools')
import functional_test as ft

cli = ft.OfficialCli(timeout=240)
ctx = ft.TestContext(cli, ft.WORK, ref_name='func-test-seg2')
ctx.prepare()
ctx._seed_resources()
filter_uri = 'vimo://' + (ctx.resources.get('filter') or [''])[0]
effect_uri = ctx.resource_id('effect')
print('filter', filter_uri, 'effect', effect_uri)


def run(name, args):
    outcome = cli(args, cwd=str(ctx.root), read_write=ctx.read_write_paths(),
                  read_only=[str(ctx.media_dir)])
    print(f'--- {name}: {outcome.state} exit={outcome.exit_code}')
    print('   ', (outcome.message or '')[:200])
    return outcome


run('filter add', ['draft', 'filter', 'add', '--ref', ctx.ref, '--resource', filter_uri])
run('effect add', ['draft', 'effect', 'add', '--ref', ctx.ref, '--resource', effect_uri,
                   '--type', 'video_effect'])
summary = run('extract summary', ['draft', 'extract', 'summary', '--ref', ctx.ref])
structure = ft.parse_json_result(summary)
kinds = {}
for node in (structure or []):
    if isinstance(node, dict):
        kinds.setdefault(node.get('type'), []).append(node.get('id'))
print('   段类型:', {k: len(v) for k, v in kinds.items()})
print('   全部类型:', sorted(kinds))

if kinds.get('filter'):
    seg = kinds['filter'][0]
    for flag in ('--seg-id', '--target'):
        run(f'filter remove({flag})', ['draft', 'filter', 'remove', '--ref', ctx.ref,
                                       flag, seg])
if kinds.get('effect') or kinds.get('video_effect'):
    seg = (kinds.get('effect') or kinds.get('video_effect'))[0]
    for flag in ('--seg-id', '--target'):
        run(f'effect remove({flag})', ['draft', 'effect', 'remove', '--ref', ctx.ref,
                                       flag, seg])
ctx.cleanup()
print('cleaned')
