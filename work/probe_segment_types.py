"""实验：给工程加上滤镜/特效/调节/贴纸后，看官方结构里这些段的类型与 id。"""
import json
import sys

sys.path.insert(0, 'tools')
import functional_test as ft

cli = ft.OfficialCli(timeout=180)
ctx = ft.TestContext(cli, ft.WORK, ref_name='func-test-segtypes')
ctx.prepare()
ctx._seed_resources()
print('resources', json.dumps(ctx.resources, ensure_ascii=False))
print('ids before', {k: v[:1] for k, v in ctx.ids_by_type.items()})
video = ctx.seg_id
effect = ctx.resource_id('effect')
sticker = ctx.resource_id('sticker')
filter_uri = 'vimo://' + (ctx.resources.get('filter') or [''])[0]


def run(name, args):
    outcome = cli(args, cwd=str(ctx.root), read_write=ctx.read_write_paths(),
                  read_only=[str(ctx.media_dir)])
    print(f'--- {name}: {outcome.state} exit={outcome.exit_code} {(outcome.message or "")[:150]}')
    return outcome


run('filter add', ['draft', 'video', 'filter', 'add', '--ref', ctx.ref,
                   '--seg-id', video, '--resource', filter_uri])
run('effect add', ['draft', 'video', 'effect', 'add', '--ref', ctx.ref,
                   '--seg-id', video, '--resource', effect, '--type', 'video_effect'])
run('adjust add', ['draft', 'adjust', 'add', '--ref', ctx.ref, '--brightness', '0.1',
                   '--start', '0s', '--duration', '1s'])
run('sticker add', ['draft', 'sticker', 'add', '--ref', ctx.ref, '--resource', sticker,
                    '--start', '0s', '--duration', '1s'])
run('keyframe add', ['draft', 'keyframe', 'add', '--ref', ctx.ref, '--seg-id', video,
                     '--animated-property', 'opacity', '--points', '0s:0%,1s:100%'])
run('template publish', ['draft', 'template', 'publish', '--ref', ctx.ref,
                         '--dir', str(ctx.out_dir)])

summary = run('extract summary', ['draft', 'extract', 'summary', '--ref', ctx.ref])
structure = ft.parse_json_result(summary)
print('=== 结构类型统计 ===')
kinds = {}
for node in (structure or []):
    if isinstance(node, dict):
        kinds.setdefault(node.get('type'), []).append(node.get('id'))
for kind, ids in kinds.items():
    print(f'  {kind}: {len(ids)}  {ids[:2]}')
print(json.dumps(structure, ensure_ascii=False, indent=1)[:2000])
ctx.cleanup()
print('cleaned')
