"""真实发起官方分步登录，打印授权链接与完成登录所需参数。"""
import json
import sys

sys.path.insert(0, 'tools')
import functional_test as ft

cli = ft.OfficialCli(timeout=180)
workspace = ft.WORK
workspace.mkdir(parents=True, exist_ok=True)

status = cli(['auth', 'status'], cwd=str(workspace), read_write=[str(workspace)])
print('=== auth status ===')
print('state', status.state, 'exit', status.exit_code)
print(status.stdout[:600])

link = cli(['auth', 'login', '--link-url', '--no-wait'], cwd=str(workspace),
           read_write=[str(workspace)])
print('=== auth login --link-url --no-wait ===')
print('state', link.state, 'exit', link.exit_code, 'ms', link.duration_ms)
print('message', (link.message or '')[:200])
print('stdout', link.stdout[:2000])
if link.stdout.strip():
    try:
        body = json.loads(link.stdout)
    except json.JSONDecodeError:
        body = {}
    result = body.get('result') if isinstance(body, dict) else None
    if isinstance(result, dict):
        keep = {k: result.get(k) for k in
                ('login_url', 'device_code', 'user_code', 'session_handoff',
                 'expires_in', 'qr_image_markdown', 'qr_image_file', 'qr_token',
                 'device_id', 'interval')
                if result.get(k) is not None}
        print('=== 关键字段 ===')
        print(json.dumps(keep, ensure_ascii=False, indent=2)[:2000])
