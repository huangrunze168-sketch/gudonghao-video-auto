"""新歌草稿官方处理阶段：原生变速、增益、渐弱、歌词识别与模板。"""
import json
import os
import sys
from pathlib import Path
ROOT=Path.cwd()
sys.path.insert(0,str(ROOT/'skills/guzhu-hao/scripts'))
sys.path.insert(0,str(ROOT/'engine'))
import guzhu_batch as gb
import lyra_cli
from guzhu_common import EngineCrypto
from guzhu_jypack import read_package
from guzhu_timeline import inspect_template
os.environ['DSH_LYRA_ALLOW_NETWORK']='1'
out=ROOT/'work/guzhu-mingyun'
state=json.loads((out/'native-build.json').read_text(encoding='utf-8'))
batch,entry=state['batch'],state['entry']
root=gb.draft_root(ROOT)
folder,_=gb.install_draft(entry['jypack'],root,'guzhu-mingyun-new')
ref='local://'+folder.name
crypto=EngineCrypto(ROOT)
tl,source=gb.read_draft_timeline(ROOT,folder)
sk=inspect_template(tl)
results=[]
def command(path,segment,options):
 opts={'--seg-id':segment['id'],**options}
 result=lyra_cli.draft(path,str(root),ref,opts,timeout=900)
 gb._mirror_draft(folder)
 results.append({'command':path,'options':opts,'result':result})
 (out/'official-edit-results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
 print('官方成功',path,segment['id'][:8],options,flush=True)
for group in sk.groups:
 if group.tts_segment:
  command(['audio','speed'],group.tts_segment,{'--speed':'1.3'})
for _t,segment,_mid in sk.intro_music:
 command(['audio','volume'],segment,{'--db':'-8'})
 command(['audio','fade'],segment,{'--out':'400ms'})
for _t,segment,_mid in sk.main_music:
 command(['audio','volume'],segment,{'--db':'3'})
 command(['audio','fade'],segment,{'--in':'250ms','--out':'1200ms'})
# 重新读取官方编辑后的时间线，歌词识别针对副歌原素材范围。
tl,_=gb.read_draft_timeline(ROOT,folder)
cues,ordered=gb.lyric_cues_for(batch,entry)
result=gb.install_lyrics_via_cli(ROOT,root,folder,tl,batch['lyrics'],cues=cues,ordered=ordered)
(out/'official-lyrics.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print('官方歌词套用完成',result['animation'],flush=True)
(out/'draft-location.json').write_text(json.dumps({'root':str(root),'folder':str(folder)},indent=2),encoding='utf-8')
