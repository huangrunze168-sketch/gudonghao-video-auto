"""回归：选歌词模板不访问本地字体清单，官方失败不默默回退。"""
import sys
from pathlib import Path
from unittest.mock import patch
sys.path[:0]=[str(Path.cwd()/'skills/guzhu-hao/scripts'),str(Path.cwd()/'engine')]
import guzhu_anim as ga
import official_materials as om
items=[{'id':'111','title':'国风大字','vip':False},{'id':'222','title':'雨雾氛围感','vip':False}]
with patch.object(ga,'animation_catalog',side_effect=AssertionError('不得访问本地缓存')),patch.object(ga,'animation_dependencies_ready',side_effect=AssertionError('不得筛本地字体')),patch.object(ga,'search_online_templates',return_value=items),patch.object(ga,'score_lyric_styles',return_value={'rainy':3}),patch.object(om,'execute',return_value={'envelope':{},'status':'官方返回成功'}) as download:
 chosen,why=ga.pick_animation('夜晚独处',project='.')
 assert chosen=='222',(chosen,why)
 assert download.call_args.args[1][-1]=='222'
with patch.object(ga,'search_online_templates',return_value=[]):
 try:ga.pick_animation('夜晚',project='.')
 except RuntimeError:pass
 else:raise AssertionError('搜索为空不应回退本地')
with patch.object(om,'execute',return_value={'error':'模拟官方授权错误'}):
 try:ga.search_online_templates('抒情',project='.')
 except RuntimeError as e:assert '授权错误' in str(e)
 else:raise AssertionError('真实错误不得吞掉')
print('三项回归通过：不筛本地字体、先官方下载、失败停止不自动替代')
