"""核对口播范围、原文件与帧对齐误差；只做检测，不加工生产音频。"""
import json, hashlib, sys, subprocess
from pathlib import Path
ROOT=Path.cwd();sys.path[:0]=[str(ROOT/'skills/guzhu-hao/scripts'),str(ROOT/'engine')]
import guzhu_batch as gb
from guzhu_timeline import Editor,range_of
folder=Path(gb.draft_root(ROOT))/'guzhu-01'
tl,_=gb.read_draft_timeline(ROOT,folder);ed=Editor(tl)
raw=json.loads((ROOT/'work/guzhu-mingyun-repair/tts/tts.json').read_text(encoding='utf-8'))
by_text={x['text']:x for x in raw['lines']};rows=[]
for _,seg in ed.segments():
 n=ed.node(seg.get('material_id')) or {}
 if ed.bucket(seg.get('material_id'))=='audios' and n.get('name') in by_text:
  item=by_text[n['name']];start,duration=range_of(seg);speed=seg.get('speed') or 1
  src=seg.get('source_timerange') or {}
  expected=item['source_duration_us']/speed
  rows.append({'text':n['name'],'start_us':start,'duration_us':duration,'source_duration_us':item['source_duration_us'],'source_start_us':src.get('start',0),'source_range_complete':src.get('duration')==item['source_duration_us'],'speed':speed,'volume':seg.get('volume'),'frame_rounding_error_us':duration-expected,'raw_file_identical':hashlib.sha256(Path(n['path']).read_bytes()).digest()==hashlib.sha256(Path(item['path']).read_bytes()).digest()})
rows.sort(key=lambda r:r['start_us'])
for index,row in enumerate(rows):row['gap_from_previous_us']=row['start_us']-(rows[index-1]['start_us']+rows[index-1]['duration_us']) if index else 0
if len(rows)!=5 or not all(r['raw_file_identical'] and r['source_range_complete'] and abs(r['frame_rounding_error_us'])<33334 and r['gap_from_previous_us']==0 for r in rows):raise RuntimeError('口播源文件或时间范围验收失败')
report={'segments':rows,'检查结论':'五段原始文件保持不变，源范围完整，目标无空洞或重叠，取整误差小于一帧','听感结论':'技术检查不替代真实试听，不宣称已完成主观听感验收'}
(ROOT/'work/guzhu-mingyun-repair/audio-continuity.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
