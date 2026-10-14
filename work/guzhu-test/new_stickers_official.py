"""用在线贴纸替换旧模板贴纸，调用官方定位和缩放，不处理贴纸图片。"""
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
out=ROOT/'work/guzhu-mingyun';loc=json.loads((out/'draft-location.json').read_text(encoding='utf-8'));root=loc['root'];folder=loc['folder'];ref='local://'+Path(folder).name
rid='7567593135224786200'
download=execute(ROOT,['material','download','--type','sticker','--resource-id',rid])
if 'envelope' not in download:raise RuntimeError(download['error'])
tl,_=gb.read_draft_timeline(ROOT,folder);editor=Editor(tl)
old=[s for t,s in editor.segments() if editor.bucket(s.get('material_id'))=='stickers']
for segment in old:
 lyra_cli.draft(['sticker','remove'],root,ref,{'--seg-id':segment['id']});gb._mirror_draft(folder)
result=lyra_cli.draft(['sticker','add'],root,ref,{'--resource':'vimo://'+rid,'--start':'0s','--duration':'2500ms'})
gb._mirror_draft(folder)
tl,_=gb.read_draft_timeline(ROOT,folder);ed=Editor(tl);new=[s for t,s in ed.segments() if ed.bucket(s.get('material_id'))=='stickers']
for seg in new:
 lyra_cli.draft(['sticker','translate'],root,ref,{'--seg-id':seg['id'],'--x':'0','--y':'0.42'});gb._mirror_draft(folder)
 lyra_cli.draft(['keyframe','add'],root,ref,{'--seg-id':seg['id'],'--animated-property':'scale','--points':'0s:0.22x,2.5s:0.22x'});gb._mirror_draft(folder)
(out/'official-stickers.json').write_text(json.dumps({'resource_id':rid,'download':download,'add':result},ensure_ascii=False,indent=2),encoding='utf-8')
print('官方贴纸添加定位缩放完成',flush=True)
