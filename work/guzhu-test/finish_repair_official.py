"""用官方命令添加独立画面效果、运镜和逐组在线贴纸。"""
import json, os, sys
from pathlib import Path
ROOT=Path.cwd()
sys.path[:0]=[str(ROOT/'skills/guzhu-hao/scripts'),str(ROOT/'engine')]
import guzhu_batch as gb
import lyra_cli
from official_materials import execute
from guzhu_timeline import Editor, range_of
os.environ['DSH_LYRA_ALLOW_NETWORK']='1'
root=gb.draft_root(ROOT);folder=Path(root)/'guzhu-01';ref='local://guzhu-01'
report={'draft':str(folder),'commands':[]}
def command(action,options):
 result=lyra_cli.draft(action,str(root),ref,options)
 gb._mirror_draft(folder)
 report['commands'].append({'action':action,'options':options,'result':result})
 return result
def download(kind,rid):
 result=execute(ROOT,['material','download','--type',kind,'--resource-id',rid])
 if 'envelope' not in result:raise RuntimeError(str(result))
 report.setdefault('downloads',[]).append(result)
 return result
# 漏光是独立画面效果，与歌词模板和富士影片调色分开。
rid='7399494094050970920';download('effect',rid)
tl,_=gb.read_draft_timeline(ROOT,folder);ed=Editor(tl)
video=next(s for _,s in ed.segments() if ed.bucket(s.get('material_id'))=='videos' and range_of(s)[0]>0)
command(['video','effect','add'],{'--seg-id':video['id'],'--resource':'vimo://'+rid})
command(['video','effect','update'],{'--seg-id':video['id'],'--resource-id':rid,'--params-json':json.dumps({'effects_adjust_background_animation':0.18,'effects_adjust_speed':0.25})})
duration=range_of(video)[1]/1e6
command(['keyframe','add'],{'--seg-id':video['id'],'--animated-property':'scale','--points':'0s:1x,%.6fs:1.035x'%duration})
# 每组使用官方在线素材实体，不再读取本地搞笑贴纸池。
pairs=[('7567593135224786200','下班啦'),('7436961804237933836','享受独处'),('7215840456385629451','叹气'),('7436961764689988883','独处时光'),('7410221196421172480','静享慢时光')]
for rid,_ in pairs:download('sticker',rid)
tl,_=gb.read_draft_timeline(ROOT,folder);ed=Editor(tl)
old=[s for _,s in ed.segments() if ed.bucket(s.get('material_id'))=='stickers']
groups=sorted([g for g in gb.inspect_template(tl).groups if g.tts_segment],key=lambda g:range_of(g.tts_segment)[0])
if len(groups)!=len(pairs):raise RuntimeError('口播组数变化，停止贴纸替换')
for s in old:command(['sticker','remove'],{'--seg-id':s['id']})
for group,(rid,name) in zip(groups,pairs):
 start,duration=range_of(group.tts_segment)
 tl,_=gb.read_draft_timeline(ROOT,folder);ed=Editor(tl)
 before={s['id'] for _,s in ed.segments() if ed.bucket(s.get('material_id'))=='stickers'}
 command(['sticker','add'],{'--resource':'vimo://'+rid,'--start':'%.6fs'%(start/1e6),'--duration':'%.6fs'%(duration/1e6)})
 tl,_=gb.read_draft_timeline(ROOT,folder);ed=Editor(tl)
 added=[s for _,s in ed.segments() if ed.bucket(s.get('material_id'))=='stickers' and s['id'] not in before]
 if len(added)!=1:raise RuntimeError('新增贴纸段数量异常')
 sid=added[0]['id']
 command(['sticker','translate'],{'--seg-id':sid,'--x':'0','--y':'0.42'})
 command(['keyframe','add'],{'--seg-id':sid,'--animated-property':'scale','--points':'0s:0.22x,%.6fs:0.22x'%(duration/1e6)})
 report.setdefault('stickers',[]).append({'name':name,'resource_id':rid,'segment':sid,'range':(start,duration)})
(ROOT/'work/guzhu-mingyun-repair/official-finish.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('官方漏光、轻推运镜、五组在线贴纸已应用')
