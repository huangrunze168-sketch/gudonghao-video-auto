"""轮询官方分步登录的收尾命令，直到用户完成浏览器授权。"""
import json
import sys
import time

sys.path.insert(0, 'tools')
import functional_test as ft

pending = json.load(open('work/auth-pending.json', encoding='utf-8'))
cli = ft.OfficialCli(timeout=120)
workspace = ft.WORK
workspace.mkdir(parents=True, exist_ok=True)
args = ['auth', 'login',
        '--device-code', pending['device_code'],
        '--user-code', pending['user_code'],
        '--session-handoff', pending['session_handoff']]

deadline = time.monotonic() + 330
attempt = 0
while time.monotonic() < deadline:
    attempt += 1
    outcome = cli(args, cwd=str(workspace), read_write=[str(workspace)])
    if outcome.ok:
        print(f'[attempt {attempt}] 登录成功')
        print('stdout:', outcome.stdout[:600])
        break
    message = outcome.message or ''
    print(f'[attempt {attempt}] state={outcome.state} exit={outcome.exit_code} '
          f'{(message or outcome.stderr)[:160]}', flush=True)
    if 'not ready' not in message and 'pending' not in message and outcome.exit_code != 1:
        print('非 pending 错误，停止轮询（可能设备码已过期，需要重新发起登录）')
        break
    time.sleep(3)
else:
    print('等待超时（设备码有效期约 300 秒），需要重新发起登录')

for extra in (['auth', 'status'], ['auth', 'me']):
    outcome = cli(extra, cwd=str(workspace), read_write=[str(workspace)])
    print('===', ' '.join(extra), '->', outcome.state, outcome.exit_code)
    print(outcome.stdout[:800])
