"""校正官方模板重建后的歌词文本，保留模板字体及段动画。"""
import json
import sys
import re
from pathlib import Path
ROOT=Path.cwd()
sys.path.insert(0,str(ROOT/'skills/guzhu-hao/scripts'))
import guzhu_batch as gb
from guzhu_timeline import Editor,range_of,retitle
out=ROOT/'work/guzhu-mingyun'
loc=json.loads((out/'draft-location.json').read_text(encoding='utf-8'))
timeline,source=gb.read_draft_timeline(ROOT,loc['folder'])
editor=Editor(timeline)
rows=[]
for track,seg in editor.segments():
 node=editor.node(seg.get('material_id')) or {}
 if editor.bucket(seg.get('material_id'))=='texts' and node.get('type')!='subtitle':
  rows.append((range_of(seg)[0],seg,node))
rows.sort(key=lambda r:r[0])
# 官方模板的每个句子由多个重叠累积字块组成，上一句结束对应下一句起点。
starts=[6833333,10666666,14000000,17600000,21300000,24833333,28600000,30050000]
lines=['有一些瞬间我在命运之外','楼下站着一直在发呆','屏幕亮起来我没理睬','那几分钟我才算存在','你也试过吧不想上来','掏钥匙的手慢了半拍','呼一口气才']
changes=[]
for idx,line in enumerate(lines):
 group=[r for r in rows if starts[idx]<=r[0]<starts[idx+1]]
 if not group: raise RuntimeError('模板歌词组为空')
 weights=[]
 for _start,_seg,node in group:
  text=gb._recognized_text(node)
  weights.append(max(1,len(re.sub(r'[^\u4e00-\u9fffA-Za-z0-9]','',text))))
 cursor=0
 total=sum(weights)
 for j,(_start,seg,node) in enumerate(group):
  end=len(line) if j==len(group)-1 else round(len(line)*sum(weights[:j+1])/total)
  text=line[cursor:end]
  cursor=end
  if not text: raise RuntimeError('歌词字块校正产生空文本，停止')
  retitle(node,text)
  changes.append({'segment':seg['id'],'start_us':_start,'text':text})
 if ''.join(c['text'] for c in changes[-len(group):])!=line:raise RuntimeError('校正后文本不一致')
gb.write_draft_timeline(ROOT,loc['folder'],timeline,source)
(out/'lyric-final-correction.json').write_text(json.dumps(changes,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(changes,ensure_ascii=False,indent=2))
