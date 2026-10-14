"""继续定位崩溃：--wait、时间范围、以及客户端版本环境变量的影响。"""
import sys

sys.path.insert(0, 'tools')
sys.path.insert(0, 'engine')
import functional_test as ft
import draftediting_runtime as dr

cli = ft.OfficialCli(timeout=180)
ctx = ft.TestContext(cli, ft.WORK, ref_name='func-test-fix3')
ctx.prepare()
video = ctx.seg_id


def run(name, args):
    outcome = cli(args, cwd=str(ctx.root), read_write=ctx.read_write_paths(),
                  read_only=[str(ctx.media_dir)])
    print(f'--- {name}: {outcome.state} exit={outcome.exit_code}')
    print('   ', (outcome.message or '')[:220])
    return outcome


run('vt + wait false', ['draft', 'algo', 'video-tracking', '--ref', ctx.ref,
                        '--seg-id', video, '--source-seg-id', video,
                        '--tracker-type', '1', '--wait', 'false',
                        '--center-x', '0.5', '--center-y', '0.5'])
run('vt + time-range', ['draft', 'algo', 'video-tracking', '--ref', ctx.ref,
                        '--seg-id', video, '--source-seg-id', video,
                        '--tracker-type', '1', '--tracking-time-range', '0s,1s'])
run('vt 用 text 段做 source', ['draft', 'algo', 'video-tracking', '--ref', ctx.ref,
                              '--seg-id', video,
                              '--source-seg-id', ctx.ids_by_type.get('text', [video])[0],
                              '--tracker-type', '1'])

# 客户端版本环境变量是否影响服务端 invalid_client_source 判定
for env in ({"LYRA_CLI_APP_VERSION": "10.7.0"}, {"LYRA_CLI_APP_VERSION": "11.6.0"},
            {"LYRA_CLI_APP_VERSION": "11.5.0.14471"}):
    label = ", ".join(f"{k}={v}" for k, v in env.items())
    try:
        result = dr.run_lyra(['draft', 'algo', 'material-understand', '--ref', ctx.ref,
                              '--seg-id', video, '--prompt', '花', '--analysis-level', 'low'],
                             str(ctx.root), 120, ctx.read_write_paths(), extra_env=env)
        print(f'--- material-understand [{label}]: OK {str(result)[:160]}')
    except Exception as error:  # noqa: BLE001 - 记录官方原始失败信息
        text = str(error).replace('\n', ' ')
        stage = 'invalid_client_source' in text
        print(f'--- material-understand [{label}]: 失败 invalid_client_source={stage} {text[:170]}')
ctx.cleanup()
print('cleaned')
