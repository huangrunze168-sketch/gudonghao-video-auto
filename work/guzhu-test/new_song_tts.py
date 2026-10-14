"""新歌官方口播；原始音频不做本地变速，1.3倍速交给草稿原生段速率。"""
import json
import os
import sys
from pathlib import Path
ROOT = Path.cwd()
sys.path.insert(0, str(ROOT/'skills/guzhu-hao/scripts'))
sys.path.insert(0, str(ROOT/'engine'))
import guzhu_batch as gb
from guzhu_common import EngineCrypto
from guzhu_jypack import read_package
os.environ['DSH_LYRA_ALLOW_NETWORK']='1'
template = Path(r'C:\Users\Administrator\.dsh\attachments\v1\files\1b\1b4df543f999b6d91fd0b4e328a108a2c0bb320ea7474fc1bac469c9176a61f2\测试.jypack')
lines = ['有没有下班到家', '却在楼下多站几分钟', '不是不想回家', '只是想把自己还给自己', '懂这首歌的评论区留个句号']
crypto=EngineCrypto(ROOT)
package=read_package(template,crypto)
out=ROOT/'work/guzhu-mingyun/tts'
out.mkdir(parents=True,exist_ok=True)
result=gb.official_tts_lines(ROOT,package,template,gb.draft_root(ROOT),lines,out,speed=1.0)
result['native_playback_speed']=1.3
for item in result['lines']:
 item['source_duration_us']=gb.probe(item['path'])['duration_us']
 item['duration_us']=round(item['source_duration_us']/1.3)
(out/'tts-native.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
