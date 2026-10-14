"""查看模板报告的渲染就绪度与路径完整性。"""
import json
from pathlib import Path

data = json.loads(Path('work/测试-jypack-report.json').read_text(encoding='utf-8'))
for key in ('official_template_package', 'render_readiness', 'path_integrity'):
    print('=' * 20, key)
    print(json.dumps(data.get(key), ensure_ascii=False, indent=1)[:2200])
