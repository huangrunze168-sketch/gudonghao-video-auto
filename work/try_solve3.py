"""实测三条可解路径：query 的真实 task id、filter/effect 段、material download 类型匹配。"""
import json
import sys

sys.path.insert(0, 'tools')
import functional_test as ft

cli = ft.OfficialCli(timeout=240)
ctx = ft.TestContext(cli, ft.WORK, ref_name='func-test-solve')
ctx.prepare()
ctx._seed_resources()
video = ctx.seg_id
print('video', video, 'resources', json.dumps(ctx.resources, ensure_ascii=False))


def run(name, args, show=260):
    outcome = cli(args, cwd=str(ctx.root), read_write=ctx.read_write_paths(),
                  read_only=[str(ctx.media_dir)])
    print(f'--- {name}: {outcome.state} exit={outcome.exit_code}')
    print('   ', (outcome.stdout or outcome.message or '')[:show].replace('\n', ' '))
    return outcome


# A. video-tracking --wait false 是否返回可查询的 task id
vt = run('video-tracking --wait false',
         ['draft', 'algo', 'video-tracking', '--ref', ctx.ref, '--seg-id', video,
          '--source-seg-id', video, '--tracker-type', '1', '--wait', 'false',
          '--center-x', '0.5', '--center-y', '0.5', '--width', '0.2', '--height', '0.2'],
         show=700)
task_id = None
if vt.ok:
    body = ft.extract_json(vt.stdout)
    result = body.get('result') if isinstance(body, dict) else None
    if isinstance(result, dict):
        task_id = result.get('task_id') or result.get('taskId')
        print('   task_id =', task_id, '| 字段:', list(result)[:12])
if task_id:
    run('algo query(真实 task id)', ['draft', 'algo', 'query', '--task-id', str(task_id)])
    run('algo wait(真实 task id)', ['draft', 'algo', 'wait', '--task-id', str(task_id),
                                    '--timeout', '20s'])

# B. 顶层 filter/effect add 是否创建独立段
filter_uri = 'vimo://' + (ctx.resources.get('filter') or [''])[0]
effect_uri = ctx.resource_id('effect')
run('draft filter add', ['draft', 'filter', 'add', '--ref', ctx.ref,
                         '--target', f'seg_id={video}', '--resource', filter_uri])
run('draft effect add', ['draft', 'effect', 'add', '--ref', ctx.ref,
                         '--target', f'seg_id={video}', '--resource', effect_uri,
                         '--type', 'video_effect'])
summary = run('extract summary', ['draft', 'extract', 'summary', '--ref', ctx.ref])
structure = ft.parse_json_result(summary)
kinds = {}
for node in (structure or []):
    if isinstance(node, dict):
        kinds.setdefault(node.get('type'), []).append(node.get('id'))
print('   段类型:', {k: len(v) for k, v in kinds.items()})
for kind in ('filter', 'effect', 'video_effect'):
    if kinds.get(kind):
        seg = kinds[kind][0]
        run(f'filter/effect remove({kind})',
            ['draft', 'filter', 'remove', '--ref', ctx.ref, '--target', f'seg_id={seg}']
            if kind == 'filter' else
            ['draft', 'effect', 'remove', '--ref', ctx.ref, '--target', f'seg_id={seg}'])

# C. material download 的 --type 与 resource-id 类型匹配
sticker_id = (ctx.resources.get('sticker') or [None])[0]
if sticker_id:
    run('material download(type sticker)', ['material', 'download', '--type', 'sticker',
                                            '--resource-id', sticker_id,
                                            '--resource-dir', str(ctx.out_dir)],
        show=320)
ctx.cleanup()
print('cleaned')
