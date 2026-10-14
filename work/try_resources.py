"""用 vimo://<线上资源 id> 实测资源类 draft 命令。"""
import json
import sys

sys.path.insert(0, 'tools')
import functional_test as ft

text = ft.load_help_text(('draft', 'adjust', 'add'))
print('=== draft adjust add help 片段 ===')
for line in (text or '').replace('\r', '').split('\n'):
    if any(word in line for word in ('EXAMPLES', 'picture_adjust', 'brightness', 'lyra-cli draft adjust')):
        print('   ', line.strip()[:140])

cli = ft.OfficialCli(timeout=180)
ctx = ft.TestContext(cli, ft.WORK, ref_name='func-test-res2')
ctx.prepare()
ctx._seed_resources()
print('resources', json.dumps(ctx.resources, ensure_ascii=False))
print('ids', {k: v[:1] for k, v in ctx.ids_by_type.items()})
video_seg = ctx.seg_id
text_seg = ctx.ids_by_type.get('text', [None])[0]


def run(name, args):
    outcome = cli(args, cwd=str(ctx.root), read_write=ctx.read_write_paths(),
                  read_only=[str(ctx.media_dir)])
    print(f'--- {name}: {outcome.state} exit={outcome.exit_code}')
    print('   ', (outcome.message or '')[:200])
    return outcome


def vimo(kind):
    ids = ctx.resources.get(kind) or []
    return 'vimo://' + ids[0] if ids else None


effect = vimo('effect')
sticker = vimo('sticker')
print('effect uri', effect, 'sticker uri', sticker)

if effect:
    run('video effect add', ['draft', 'video', 'effect', 'add', '--ref', ctx.ref,
                             '--seg-id', video_seg, '--resource', effect,
                             '--type', 'video_effect'])
    run('video filter add', ['draft', 'video', 'filter', 'add', '--ref', ctx.ref,
                             '--seg-id', video_seg, '--resource', effect])
    run('video mask add', ['draft', 'video', 'mask', 'add', '--ref', ctx.ref,
                           '--seg-id', video_seg, '--resource', effect,
                           '--resource-type', 'rectangle'])
    run('audio-effect add', ['draft', 'video', 'audio-effect', 'add', '--ref', ctx.ref,
                             '--seg-id', video_seg, '--resource', effect])
    run('text effect add', ['draft', 'text', 'effect', 'add', '--ref', ctx.ref,
                            '--content', '功能测试特效字', '--resource', effect])
if sticker:
    run('sticker add', ['draft', 'sticker', 'add', '--ref', ctx.ref,
                        '--resource', sticker, '--start', '0s', '--duration', '1s'])
run('adjust add(仅字段)', ['draft', 'adjust', 'add', '--ref', ctx.ref,
                          '--brightness', '0.1', '--start', '0s', '--duration', '1s'])
run('measure-box', ['media', 'measure-box', '--input', str(ctx.media_files['video']),
                    '--type', 'sticker', '--resource-dir', str(ctx.out_dir),
                    '--canvas-width', '1920', '--canvas-height', '1080',
                    '--allow-video-decode'])
ctx.cleanup()
print('cleaned')
