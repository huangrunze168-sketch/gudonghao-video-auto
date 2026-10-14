"""把新构建的包安装成草稿，供换贴纸与渲染使用。"""
import json
import os
import sys
from pathlib import Path

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT / 'skills/guzhu-hao/scripts'))
sys.path.insert(0, str(ROOT / 'engine'))
import guzhu_batch as gb

os.environ['DSH_LYRA_ALLOW_NETWORK'] = '1'

root = gb.draft_root('.')
jypack = ROOT / 'work/guzhu-mingyun-v2/jypack/有一些瞬间_我在命运之外.jypack'
folder, unpacked = gb.install_draft(jypack, root, 'guzhu-mingyun-v3')
print('已安装草稿 %s（%d 个文件）' % (folder.name, unpacked))

Path('work/guzhu-mingyun-v2/draft-location.json').write_text(
    json.dumps({'root': str(root), 'folder': str(folder)}, ensure_ascii=False, indent=2),
    encoding='utf-8')
