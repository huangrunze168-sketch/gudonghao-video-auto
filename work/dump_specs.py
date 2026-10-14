"""打印指定命令的真实 help 参数规格。"""
import sys

sys.path.insert(0, 'tools')
import functional_test as ft

targets = [tuple(item.split('/')) for item in sys.argv[1:]]
for path in targets:
    text = ft.load_help_text(path)
    if not text:
        print(path, 'NO HELP')
        continue
    print('==', ' '.join(path))
    for spec in ft.parse_option_specs(text):
        if spec.flag in ('--help', '--version', '--jq'):
            continue
        mark = 'REQUIRED' if spec.required else ''
        print(f"   {spec.flag:24s} {spec.type_token:30s} {mark:9s} {spec.choices[:4]}")
