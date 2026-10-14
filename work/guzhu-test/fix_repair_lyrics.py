"""纠正官方模板重建后的整句文本，保持原段时间和官方样式。"""
import json, sys
from pathlib import Path
ROOT=Path.cwd()
sys.path[:0]=[str(ROOT/'skills/guzhu-hao/scripts'),str(ROOT/'engine')]
import guzhu_batch as gb
from guzhu_timeline import Editor, range_of, retitle
folder=Path(gb.draft_root(ROOT))/'guzhu-01'
tl,src=gb.read_draft_timeline(ROOT,folder)
ed=Editor(tl)
rows=[]
for _,seg in ed.segments():
 node=ed.node(seg.get('material_id')) or {}
 if ed.bucket(seg.get('material_id'))=='texts' and node.get('type')!='subtitle':
  rows.append((range_of(seg)[0],seg,node))
rows.sort(key=lambda r:r[0])
lines=['有一些瞬间\n我在命运之外','楼下站着\n一直在发呆','屏幕亮起来\n我没理睬','那几分钟\n我才算存在','你也试过吧\n不想上来','掏钥匙的手\n慢了半拍','呼一口气\n才把锁打开']
if len(rows)!=len(lines): raise RuntimeError('歌词段数变化，停止自动修改')
changes=[]
for (_,seg,node),text in zip(rows,lines):
 old=gb._recognized_text(node)
 retitle(node,text)
 changes.append({'id':seg['id'],'before':old,'after':text,'range':range_of(seg)})
gb.write_draft_timeline(ROOT,folder,tl,src)
(ROOT/'work/guzhu-mingyun-repair/lyrics-correction.json').write_text(json.dumps(changes,ensure_ascii=False,indent=2),encoding='utf-8')
print('已校正七句歌词，保留官方模板样式和段时间')
