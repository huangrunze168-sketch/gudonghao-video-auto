"""探测 material search 支持哪些类型，为模板类命令找线上资源 id。"""
import sys

sys.path.insert(0, 'tools')
import functional_test as ft

cli = ft.OfficialCli(timeout=180)
ws = ft.WORK
ws.mkdir(parents=True, exist_ok=True)
for kind in ('sticker', 'effect', 'filter', 'transition', 'text_template',
             'subtitle_template', 'template', 'image', 'music'):
    outcome = cli(['material', 'search', '--type', kind, '--prompt', '花', '--limit', '1'],
                  cwd=str(ws), read_write=[str(ws)])
    body = ft.extract_json(outcome.stdout)
    result = body.get('result') if isinstance(body, dict) else None
    items = (result or {}).get('items') if isinstance(result, dict) else None
    first = (items or [{}])[0] if items else {}
    found = first.get('resource_id') or first.get('effect_id')
    print(f"{kind:20s} {outcome.state:16s} items={len(items or []):<3} "
          f"id={str(found):22s} {(outcome.message or '')[:60]}")
