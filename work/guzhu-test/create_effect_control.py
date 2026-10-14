"""仅为渲染对照创建副本并取消富士影片引用，不修改正式草稿。"""
import json, shutil, sys
from pathlib import Path
ROOT=Path.cwd()
sys.path[:0]=[str(ROOT/'skills/guzhu-hao/scripts'),str(ROOT/'engine')]
import guzhu_batch as gb
root=Path(gb.draft_root(ROOT))
source=root/'guzhu-01'
control=root/'guzhu-mingyun-effect-control'
if control.exists(): raise RuntimeError('验收副本已存在，停止覆盖')
shutil.copytree(source,control)
tl,path=gb.read_draft_timeline(ROOT,control)
ids={m['id'] for m in tl.get('materials',{}).get('video_effects',[]) if str(m.get('resource_id'))=='7631600978600480036'}
changed=[]
for track in tl.get('tracks',[]):
 for seg in track.get('segments',[]):
  refs=seg.get('extra_material_refs') or []
  if any(r in ids for r in refs):
   seg['extra_material_refs']=[r for r in refs if r not in ids]
   changed.append(seg['id'])
if len(changed)!=1: raise RuntimeError('富士影片目标数量不是1，停止对照')
gb.write_draft_timeline(ROOT,control,tl,path)
(ROOT/'work/guzhu-mingyun-repair/effect-control.json').write_text(json.dumps({'control':str(control),'原始草稿未修改':True,'removed_refs':list(ids),'segments':changed},ensure_ascii=False,indent=2),encoding='utf-8')
print('对照副本已创建，仅取消一个视频段的富士影片引用')
