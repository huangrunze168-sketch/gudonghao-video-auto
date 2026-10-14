"""保存官方完整自检诊断及音频、字体、时间范围验证。"""
import json
import sys
import os
from pathlib import Path
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'skills/guzhu-hao/scripts'));sys.path.insert(0,str(ROOT/'engine'))
import guzhu_batch as gb
import lyra_cli
from guzhu_timeline import Editor,range_of,parse_text_content
out=ROOT/'work/guzhu-mingyun';loc=json.loads((out/'draft-location.json').read_text(encoding='utf-8'));folder=Path(loc['folder']);root=loc['root'];ref='local://'+folder.name
report=folder/'official-lint.json';error=None
try: lyra_cli.lint_draft(root,ref,output=str(report))
except Exception as e: error=str(e)
if not report.is_file():raise RuntimeError('官方自检没有产出诊断文件：'+str(error))
d=json.loads(report.read_text(encoding='utf-8'))
(out/'official-lint.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
timeline,_=gb.read_draft_timeline(ROOT,folder);ed=Editor(timeline)
fonts=set();audio=[]
for track,seg in ed.segments():
 node=ed.node(seg.get('material_id')) or {}
 if ed.bucket(seg.get('material_id'))=='texts' and node.get('type')!='subtitle':
  c=parse_text_content(node.get('content')) or {}
  for style in c.get('styles') or []:
   f=style.get('font') or {};p=Path(f.get('path') or '')
   if not p.is_file() or p.stat().st_size==0:raise RuntimeError('实际歌词字体没有实体')
   fonts.add((f.get('id'),p.stat().st_size))
 if ed.bucket(seg.get('material_id'))=='audios':audio.append({'id':seg['id'],'range':range_of(seg),'source':seg.get('source_timerange'),'speed':seg.get('speed'),'volume':seg.get('volume'),'fades':seg.get('extra_material_refs')})
summary={'duration_us':timeline.get('duration'),'fonts':sorted(fonts),'audio':audio,'lint_status':d.get('status'),'lint_issues':d.get('issues')}
(out/'final-draft-check.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print('字体实体',fonts,'草稿时长',timeline.get('duration'))
print('官方自检',d.get('status'),'问题数',len(d.get('issues') or []))
print([(i.get('severity'),i.get('rule_id'),i.get('message')) for i in d.get('issues') or []][:10])
