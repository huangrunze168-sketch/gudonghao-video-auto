"""官方画面缓推与叠化；不烘焙背景动画。"""
import json
import os
import sys
from pathlib import Path
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'skills/guzhu-hao/scripts'));sys.path.insert(0,str(ROOT/'engine'))
import guzhu_batch as gb
import lyra_cli
from official_materials import execute
from guzhu_timeline import Editor,range_of
os.environ['DSH_LYRA_ALLOW_NETWORK']='1'
out=ROOT/'work/guzhu-mingyun';loc=json.loads((out/'draft-location.json').read_text(encoding='utf-8'));folder=loc['folder'];root=loc['root'];ref='local://'+Path(folder).name
tl,_=gb.read_draft_timeline(ROOT,folder);ed=Editor(tl)
videos=sorted([s for t,s in ed.segments() if ed.bucket(s.get('material_id'))=='videos'],key=lambda s:range_of(s)[0])
intro,main=videos[0],videos[-1]
result=lyra_cli.draft(['keyframe','add'],root,ref,{'--seg-id':main['id'],'--animated-property':'scale','--points':'0s:1x,23s:1.04x','--curve':'linear'})
gb._mirror_draft(folder)
download=execute(ROOT,['material','download','--type','transition','--resource-id','6724845717472416269'])
if 'envelope' not in download:raise RuntimeError(download['error'])
transition=lyra_cli.draft(['video','transition','add'],root,ref,{'--seg-id':intro['id'],'--resource':'vimo://6724845717472416269','--duration':'500ms'})
gb._mirror_draft(folder)
(out/'official-finish.json').write_text(json.dumps({'camera':result,'transition':transition,'download':download},ensure_ascii=False,indent=2),encoding='utf-8')
print('官方背景缓推及叠化成功')
