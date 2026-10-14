"""新歌原素材编排：不用 FFmpeg 裁切、增益、渐弱或变速。"""
import json
import sys
from pathlib import Path
ROOT=Path.cwd()
sys.path.insert(0,str(ROOT/'skills/guzhu-hao/scripts'))
import guzhu_batch as gb
from guzhu_common import EngineCrypto
from guzhu_jypack import read_package
out=ROOT/'work/guzhu-mingyun'
batch={
 'template':r'C:\Users\Administrator\.dsh\attachments\v1\files\1b\1b4df543f999b6d91fd0b4e328a108a2c0bb320ea7474fc1bac469c9176a61f2\测试.jypack',
 'out':str(out),'_base':str(ROOT),
 'media':{'native_audio':True,'background':str(out/'background.png'),'stickers':'off'},
 'lyrics':{'engine':'official','animation':'7513861835175546166'},
 'render':{'width':1280,'height':720,'fps':30,'bitrate':6000000,'timeout':1800},
 'songs':[{'name':'有一些瞬间 我在命运之外','audio_layout':'chorus','chorus_start_us':58280000,'target_seconds':30,
 'file':r'C:\Users\Administrator\.dsh\attachments\v1\files\28\28aa1248353b84819d4e7fd8c78bc47fe26a20b85a16ba9fbe596d4683fe05bc\有一些瞬间 我在命运之外（男）.wav',
 'lyrics':r'C:\Users\Administrator\.dsh\attachments\v1\files\7a\7a0e011d24e5ff22fcf13ad0222bdbd682902e54aa7eefe526a0e3846fcf76a1\新建 文本文档 (3).txt'}]}
tts=json.loads((out/'tts/tts-native.json').read_text(encoding='utf-8'))
crypto=EngineCrypto(ROOT)
package=read_package(batch['template'],crypto)
entry=gb.build_one(batch,package,tts,batch['songs'][0],out,ROOT,crypto)
(out/'native-build.json').write_text(json.dumps({'batch':batch,'entry':entry},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(entry,ensure_ascii=False,indent=2))
