import copy
import json
from pathlib import Path


ROOT = Path(r"C:\Users\Administrator\Documents\剪映")
timeline_path = ROOT / "work/测试-jypack-render-final/timeline.json"
lyrics_path = ROOT / "work/测试-auto-lyrics-large-v3/lyrics.json"
output_path = ROOT / "work/测试-auto-lyrics-official-render-v2/timeline.json"

timeline = json.loads(timeline_path.read_text(encoding="utf-8"))
lyrics = json.loads(lyrics_path.read_text(encoding="utf-8"))
cues = lyrics["cues"]

# 样本前 6.4 秒已有口播字幕，官方歌词模板从音乐段第二句开始。
groups = [[cues[1]], [cues[2]], cues[3:5], cues[5:7], cues[7:9], cues[9:12]]
template_track = next(
    track for track in timeline["tracks"]
    if track.get("type") == "text" and len(track.get("segments", [])) == 6
)
templates = {item["id"]: item for item in timeline["materials"]["text_templates"]}
texts = {item["id"]: item for item in timeline["materials"]["texts"]}


def utf16_length(value):
    return len(value.encode("utf-16-le")) // 2


def combined(group):
    start = group[0]["start_ms"]
    end = group[-1]["end_ms"]
    words = []
    for cue_index, cue in enumerate(group):
        for word_index, word in enumerate(cue["words"]):
            value = word["text"]
            if cue_index and word_index == 0:
                value = "\n" + value
            words.append({
                "text": value,
                "start_time": max(0, word["start_ms"] - start),
                "end_time": max(1, word["end_ms"] - start),
            })
    return start, end, "".join(word["text"] for word in words), words


def update_text_material(material, value, words):
    content = json.loads(material.get("content") or "{}")
    content["text"] = value
    length = utf16_length(value)
    styles = content.get("styles") or []
    for style in styles:
        style["range"] = [0, length]
    material["content"] = json.dumps(content, ensure_ascii=False, separators=(",", ":"))
    material["recognize_text"] = value
    material["words"] = {
        "text": [word["text"] for word in words],
        "start_time": [word["start_time"] for word in words],
        "end_time": [word["end_time"] for word in words],
    }


audit = []
for segment, group in zip(template_track["segments"], groups):
    template = templates[segment["material_id"]]
    start, end, value, words = combined(group)
    old_count = max(1, len(template["origin_word_info"].get("words", [])))
    new_count = len(words)
    info = {"start_time": start, "end_time": end, "text": value,
            "words": copy.deepcopy(words)}
    template["origin_word_info"] = copy.deepcopy(info)
    template["current_word_info"] = copy.deepcopy(info)
    for resource in template.get("text_info_resources", []):
        old_start, old_end = resource.get("word_index", [0, old_count])
        new_start = min(new_count, round(old_start * new_count / old_count))
        new_end = min(new_count, max(new_start + 1, round(old_end * new_count / old_count)))
        resource["word_index"] = [new_start, new_end]
        text_material = texts.get(resource.get("text_material_id"))
        if text_material:
            subset = words[new_start:new_end]
            update_text_material(text_material, "".join(word["text"] for word in subset), subset)
    duration = end - start
    segment["target_timerange"] = {"start": start * 1000, "duration": duration * 1000}
    segment["render_timerange"] = {"start": start * 1000, "duration": duration * 1000}
    audit.append({"segment_id": segment["id"], "start_ms": start, "end_ms": end,
                  "text": value, "template_name": template.get("name"),
                  "effect_id": template.get("effect_id")})

output_path.parent.mkdir(parents=True, exist_ok=False)
output_path.write_text(json.dumps(timeline, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
(output_path.parent / "lyrics-template-audit.json").write_text(
    json.dumps({"source": str(lyrics_path), "recognized_by": lyrics["recognizer"],
                "template_segments": audit}, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8")
print(json.dumps({"timeline": str(output_path), "segments": len(audit)}, ensure_ascii=False))
