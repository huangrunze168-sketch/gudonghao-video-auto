"""核验实际视频效果引用和官方原始口播，不从素材数量推断成片质量。"""
import hashlib
import json
import sys
from pathlib import Path
ROOT = Path.cwd()
sys.path[:0] = [str(ROOT/'skills/guzhu-hao/scripts'), str(ROOT/'engine')]
import guzhu_batch as gb
from guzhu_timeline import Editor, range_of
folder = Path(gb.draft_root(ROOT))/'guzhu-01'
timeline, source = gb.read_draft_timeline(ROOT, folder)
editor = Editor(timeline)
effects = {m['id']: m for m in timeline.get('materials', {}).get('video_effects', [])}
raw = json.loads((ROOT/'work/guzhu-mingyun-repair/tts/tts.json').read_text(encoding='utf-8'))
originals = {item['text']: item for item in raw['lines']}
report = {'draft': str(folder), 'source': str(source), 'effects': [], 'tts': [], 'lyrics': []}
for track, segment in editor.segments():
    material = editor.node(segment.get('material_id')) or {}
    bucket = editor.bucket(segment.get('material_id'))
    refs = segment.get('extra_material_refs') or []
    if bucket == 'videos':
        for ref in refs:
            if ref in effects:
                report['effects'].append({'video_segment': segment['id'], 'range': range_of(segment), 'effect': effects[ref]})
    if bucket == 'audios' and material.get('name') in originals:
        item = originals[material['name']]
        installed = Path(material['path'])
        original = Path(item['path'])
        report['tts'].append({'text': material['name'], 'range': range_of(segment), 'source_range': segment.get('source_timerange'), 'speed': segment.get('speed'), 'volume': segment.get('volume'), '原始文件逐字节一致': hashlib.sha256(installed.read_bytes()).digest() == hashlib.sha256(original.read_bytes()).digest(), 'source_duration_us': item['source_duration_us']})
    if bucket == 'texts' and material.get('type') != 'subtitle':
        report['lyrics'].append({'range': range_of(segment), 'text': gb._recognized_text(material)})
output = ROOT/'work/guzhu-mingyun-repair/draft-audit.json'
output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(report, ensure_ascii=False, indent=2))
