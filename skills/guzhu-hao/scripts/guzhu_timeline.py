# -*- coding: utf-8 -*-
"""把股东号模板改造成目标视频的时间线：换歌、换话术、换歌词、重排时间轴。

模板骨架（由 inspect_template 动态识别，不依赖硬编码 id）：

    0 ──────────────── intro_end ────────────── 总时长
    │  片头 N 组引流     │  主歌段（歌曲高潮 + 歌词）
    │  TTS + 字幕 + 贴纸 │  音乐 + 歌词字幕
"""
from __future__ import annotations

import copy
from dataclasses import dataclass, field
import json
import uuid

from guzhu_anim import STICKER_OFFSET_Y, STICKER_SCALE, sticker_pixels
from guzhu_common import GuzhuError

PLACEHOLDER_MARK = "##_draftpath_placeholder_"
MIN_LYRIC_US = 120_000
PRUNABLE_BUCKETS = ("texts", "material_animations", "stickers", "text_templates",
                    "placeholder_infos", "sound_channel_mappings")


def new_id():
    return str(uuid.uuid4()).upper()


def timerange(start=0, duration=0):
    """剪映的写法：start 为 0 时省略。"""
    value = {"duration": int(duration)}
    if start:
        value["start"] = int(start)
    return value


def range_of(segment, key="target_timerange"):
    value = segment.get(key) or {}
    return int(value.get("start") or 0), int(value.get("duration") or 0)


def set_range(segment, key, start, duration):
    segment[key] = timerange(start, duration)


def placeholder_prefix(path):
    """取出草稿占位前缀，例如 `##_draftpath_placeholder_XXX_##`。"""
    if not isinstance(path, str):
        return None
    index = path.find(PLACEHOLDER_MARK)
    if index < 0:
        return None
    end = path.find("_##", index + len(PLACEHOLDER_MARK))
    if end < 0:
        return None
    return path[:end + 3]


def parse_text_content(raw):
    """解析文字素材 content 字符串；失败时返回 None。"""
    if not isinstance(raw, str):
        return None
    try:
        value = json.loads(raw)
    except ValueError:
        return None
    return value if isinstance(value, dict) else None


def dump_text_content(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def even_words(text, template=None):
    """按字符均分逐字时间，供字幕的逐字字段使用。"""
    characters = list(text)
    total = 0
    if isinstance(template, dict):
        ends = template.get("end_time") or []
        if ends and isinstance(ends[-1], (int, float)):
            total = int(ends[-1])
    if total <= 0:
        total = max(300, 120 * max(1, len(characters)))
    if not characters:
        return {}
    step = total / len(characters)
    starts, ends, texts = [], [], []
    for index, character in enumerate(characters):
        starts.append(int(round(index * step)))
        ends.append(int(round((index + 1) * step)))
        texts.append(character)
    return {"start_time": starts, "end_time": ends, "text": texts}


def remap_words(text, skeleton=None, duration_ms=0):
    """把新文本套到原有的逐字时间骨架上，**保留演唱节奏**。

    官方识别的 ``words`` 是按演唱切好的词块（带停顿、有疏密）。换文本时如果
    只拿它的总时长再按字数均分，节奏就被抹平成机械节拍，字幕便会跟歌声错开——
    这正是"歌词跟音频不对齐"的根因。这里按原词块的时间边界，把新文本按字数
    比例填进去，骨架保留。
    """
    characters = list(str(text))
    if not characters:
        return {}
    starts = (skeleton or {}).get("start_time") or []
    ends = (skeleton or {}).get("end_time") or []
    tokens = (skeleton or {}).get("text") or []
    blocks = [(int(low), int(high))
              for low, high, token in zip(starts, ends, tokens)
              if str(token).strip()]
    # 以实际段时长为准：拆段后段时间会变短，骨架要跟着压缩，否则会超出段范围
    total = int(duration_ms) if int(duration_ms) > 0 else 0
    if total <= 0 and ends and isinstance(ends[-1], (int, float)):
        total = int(ends[-1])
    if total <= 0:
        total = max(300, 120 * len(characters))
    if not blocks:
        return even_words(text, {"end_time": [total]})
    if blocks[-1][1] < total:
        blocks[-1] = (blocks[-1][0], total)

    new_starts, new_ends, new_text = [], [], []
    cursor = 0
    for index, (low, high) in enumerate(blocks):
        left_blocks = len(blocks) - index
        left_chars = len(characters) - cursor
        if left_chars <= 0:
            break
        take = max(1, int(round(left_chars / left_blocks)))
        chunk = characters[cursor:cursor + take]
        cursor += len(chunk)
        if not chunk:
            continue
        step = max(1, high - low) / len(chunk)
        for order, character in enumerate(chunk):
            new_text.append(character)
            new_starts.append(int(round(low + order * step)))
            new_ends.append(int(round(low + (order + 1) * step)))
    while cursor < len(characters):
        new_text.append(characters[cursor])
        base = new_ends[-1] if new_ends else 0
        new_starts.append(base)
        new_ends.append(base + 100)
        cursor += 1
    return {"start_time": new_starts, "end_time": new_ends, "text": new_text}


def retitle(node, text):
    """改写一条文字素材的文本，并同步样式区间与逐字时间。"""
    for key in ("content", "base_content"):
        value = parse_text_content(node.get(key))
        if value is None:
            continue
        value["text"] = text
        styles = value.get("styles")
        if isinstance(styles, list):
            for style in styles:
                if isinstance(style, dict):
                    style["range"] = [0, len(text)]
        node[key] = dump_text_content(value)
    if "recognize_text" in node:
        node["recognize_text"] = text
    if "words" in node:
        # 用 remap 而不是均分：官方 words 里的词块边界就是演唱节奏
        node["words"] = remap_words(text, node.get("words"))


class Editor:
    """在解密后的时间线 dict 上做结构化改造，保持剪映原有字段风格。"""

    def __init__(self, timeline):
        if not isinstance(timeline, dict):
            raise GuzhuError("缺少可改造的时间线")
        self.t = timeline
        self.materials = timeline.setdefault("materials", {})
        self.tracks = timeline.setdefault("tracks", [])
        self.refresh()

    def refresh(self):
        self.by_id = {}
        for bucket, nodes in self.materials.items():
            if not isinstance(nodes, list):
                continue
            for node in nodes:
                if isinstance(node, dict) and node.get("id"):
                    self.by_id[node["id"]] = (bucket, node)

    def material(self, material_id):
        return self.by_id.get(material_id)

    def node(self, material_id):
        found = self.by_id.get(material_id)
        return found[1] if found else None

    def bucket(self, material_id):
        found = self.by_id.get(material_id)
        return found[0] if found else None

    def segments(self):
        for track in self.tracks:
            for segment in track.get("segments") or []:
                yield track, segment

    def track_of(self, segment):
        for track in self.tracks:
            if segment in (track.get("segments") or []):
                return track
        return None

    def clone_material(self, material_id):
        found = self.by_id.get(material_id)
        if not found:
            raise GuzhuError("找不到要克隆的素材：" + str(material_id))
        bucket, node = found
        clone = copy.deepcopy(node)
        clone["id"] = new_id()
        self.add_material(bucket, clone)
        return clone["id"]

    def add_material(self, bucket, node):
        self.materials.setdefault(bucket, []).append(node)
        self.by_id[node["id"]] = (bucket, node)
        return node["id"]

    def clone_refs(self, refs):
        return [self.clone_material(ref) for ref in (refs or []) if self.material(ref)]

    def remove_material(self, material_id):
        found = self.by_id.pop(material_id, None)
        if not found:
            return
        bucket, node = found
        self.materials[bucket] = [item for item in self.materials[bucket] if item is not node]

    def remove_segment(self, track, segment):
        track["segments"] = [item for item in (track.get("segments") or [])
                             if item is not segment]

    def add_segment(self, track, segment):
        track.setdefault("segments", []).append(segment)

    def used_materials(self):
        used = set()
        for _, segment in self.segments():
            if segment.get("material_id"):
                used.add(segment["material_id"])
            used.update(segment.get("extra_material_refs") or [])
        return used

    def sort_tracks(self):
        for track in self.tracks:
            segments = track.get("segments")
            if isinstance(segments, list):
                segments.sort(key=lambda item: range_of(item)[0])

    def shift_from(self, threshold, delta):
        """把起点不早于 threshold 的片段整体平移 delta 微秒。"""
        if not delta:
            return 0
        moved = 0
        for _, segment in self.segments():
            start, duration = range_of(segment)
            if start >= threshold:
                set_range(segment, "target_timerange", start + delta, duration)
                moved += 1
        return moved

    def shift_template_words(self, threshold_ms, delta_ms):
        """同步平移歌词卡内部的绝对毫秒时间。"""
        if not delta_ms:
            return
        for node in self.materials.get("text_templates") or []:
            for key in ("current_word_info", "origin_word_info"):
                info = node.get(key)
                if not isinstance(info, dict):
                    continue
                if info.get("start_time") is not None and info["start_time"] >= threshold_ms:
                    for name in ("start_time", "end_time"):
                        if info.get(name) is not None:
                            info[name] += delta_ms
                for word in info.get("words") or []:
                    if not isinstance(word, dict):
                        continue
                    if word.get("start_time") is not None and word["start_time"] >= threshold_ms:
                        for name in ("start_time", "end_time"):
                            if word.get(name) is not None:
                                word[name] += delta_ms

    def duration(self):
        return int(self.t.get("duration") or 0)

    def set_duration(self, value):
        self.t["duration"] = int(value)

    def max_segment_end(self):
        end = 0
        for _, segment in self.segments():
            start, duration = range_of(segment)
            end = max(end, start + duration)
        return end


@dataclass
class IntroGroup:
    """片头的一组引流：一条 TTS + 一条字幕 + 一个贴纸。"""

    tts_segment: dict = None
    tts_material: str = None
    subtitle_segment: dict = None
    subtitle_material: str = None
    sticker_segment: dict = None
    sticker_material: str = None
    start: int = 0
    duration: int = 0


@dataclass
class Skeleton:
    """模板结构识别结果。"""

    intro_end: int = 0
    groups: list = field(default_factory=list)
    main_music: list = field(default_factory=list)
    intro_music: list = field(default_factory=list)
    main_duration: int = 0
    lyric_track: dict = None
    lyric_materials: list = field(default_factory=list)
    lyric_segment_sample: dict = None
    subtitle_track: dict = None
    sticker_track: dict = None
    tts_track: dict = None
    video_track: dict = None
    subtitle_sample: str = None
    lyric_font: dict = None


def inspect_template(timeline):
    """识别股东号模板的骨架。"""
    editor = Editor(timeline)
    tts, music, subtitles, stickers = [], [], [], []
    subtitle_track = lyric_track = sticker_track = tts_track = video_track = None
    lyric_materials = []
    lyric_segment_sample = None

    for track, segment in editor.segments():
        material_id = segment.get("material_id")
        bucket = editor.bucket(material_id)
        node = editor.node(material_id) or {}
        kind = node.get("type")
        if bucket == "audios" and kind == "text_to_audio":
            tts.append((track, segment, material_id))
            tts_track = tts_track or track
        elif bucket == "audios":
            music.append((track, segment, material_id))
        elif bucket == "texts" and kind == "subtitle":
            subtitles.append((track, segment, material_id))
            subtitle_track = subtitle_track or track
        elif bucket == "text_templates":
            lyric_track = lyric_track or track
            lyric_materials.append(material_id)
            if lyric_segment_sample is None:
                lyric_segment_sample = copy.deepcopy(segment)
        elif bucket == "stickers":
            stickers.append((track, segment, material_id))
            sticker_track = sticker_track or track
        if track.get("type") == "video":
            video_track = video_track or track

    if not music:
        raise GuzhuError("模板里没有音乐轨道，无法换歌")
    if not tts:
        raise GuzhuError("模板里没有 TTS 引流话术，无法换话术")

    music.sort(key=lambda item: range_of(item[1])[0])
    main_music = [music[-1]]
    intro_music = music[:-1]
    intro_end = range_of(main_music[0][1])[0]
    if intro_end <= 0:
        raise GuzhuError("无法确定模板片头与主歌的分界点")

    tts.sort(key=lambda item: range_of(item[1])[0])
    subtitles.sort(key=lambda item: range_of(item[1])[0])
    stickers.sort(key=lambda item: range_of(item[1])[0])

    groups = []
    for index, (_, segment, material_id) in enumerate(tts):
        group = IntroGroup(tts_segment=segment, tts_material=material_id)
        group.start, group.duration = range_of(segment)
        if index < len(subtitles):
            group.subtitle_segment = subtitles[index][1]
            group.subtitle_material = subtitles[index][2]
        if index < len(stickers):
            group.sticker_segment = stickers[index][1]
            group.sticker_material = stickers[index][2]
        groups.append(group)

    lyric_font = None
    if lyric_materials:
        template = editor.node(lyric_materials[0]) or {}
        for resource in template.get("resources") or []:
            if isinstance(resource, dict) and resource.get("panel") == "fonts":
                lyric_font = {"path": resource.get("path"),
                              "resource_id": resource.get("resource_id")}
                break

    return Skeleton(intro_end=intro_end, groups=groups, main_music=main_music,
                    intro_music=intro_music,
                    main_duration=range_of(main_music[0][1])[1],
                    lyric_track=lyric_track, lyric_materials=lyric_materials,
                    lyric_segment_sample=lyric_segment_sample,
                    subtitle_track=subtitle_track,
                    sticker_track=sticker_track, tts_track=tts_track,
                    video_track=video_track,
                    subtitle_sample=(subtitles[0][2] if subtitles else None),
                    lyric_font=lyric_font)


def _grow_groups(editor, skeleton, count):
    """把片头引流组复制到指定数量。"""
    groups = list(skeleton.groups)
    if not groups:
        raise GuzhuError("模板片头没有可复制的引流组")
    while len(groups) < count:
        source = groups[-1]
        group = IntroGroup()
        for track, segment, material_id, segment_attr, material_attr in (
                (skeleton.tts_track, source.tts_segment, source.tts_material,
                 "tts_segment", "tts_material"),
                (skeleton.subtitle_track, source.subtitle_segment, source.subtitle_material,
                 "subtitle_segment", "subtitle_material"),
                (skeleton.sticker_track, source.sticker_segment, source.sticker_material,
                 "sticker_segment", "sticker_material")):
            if segment is None or track is None:
                continue
            clone = copy.deepcopy(segment)
            clone["id"] = new_id()
            clone["material_id"] = editor.clone_material(material_id)
            clone["extra_material_refs"] = editor.clone_refs(segment.get("extra_material_refs"))
            editor.add_segment(track, clone)
            setattr(group, segment_attr, clone)
            setattr(group, material_attr, clone["material_id"])
        groups.append(group)
    return groups


def _drop_group(editor, group):
    used = editor.used_materials()
    for segment, material_id in ((group.tts_segment, group.tts_material),
                                 (group.subtitle_segment, group.subtitle_material),
                                 (group.sticker_segment, group.sticker_material)):
        if segment is not None:
            track = editor.track_of(segment)
            if track is not None:
                editor.remove_segment(track, segment)
        if material_id and material_id not in used:
            editor.remove_material(material_id)


def _rescale_intro(editor, skeleton, old_length, new_length):
    """片头里的画面段随新片头长度等比缩放。

    source_timerange 必须与 target_timerange 一起改：模板里两者相等，
    只改 target 会让引擎认为素材不够长而整段丢弃（片头直接消失）。
    """
    if old_length == new_length or skeleton.video_track is None:
        return 0
    scaled = 0
    for segment in skeleton.video_track.get("segments") or []:
        start, duration = range_of(segment)
        if duration <= 0 or start + duration > old_length + 500:
            continue
        new_start = int(round(start * new_length / old_length))
        new_duration = int(round(duration * new_length / old_length))
        set_range(segment, "target_timerange", new_start, new_duration)
        if isinstance(segment.get("source_timerange"), dict):
            source_start, _ = range_of(segment, "source_timerange")
            set_range(segment, "source_timerange", source_start, new_duration)
        scaled += 1
    return scaled


def _resize_main_clip(editor, skeleton, intro_new, main_duration):
    """把主歌画面段伸缩到实际主歌时长。

    每首歌长度不同，主歌段不再沿用模板的固定时长；画面段必须跟着伸缩，
    否则会尾部留白（画面先结束）或被下一段盖住。source 区间同步改，
    只改 target 会被引擎判定素材不足而丢弃整段。
    """
    if skeleton.video_track is None:
        return 0
    resized = 0
    for segment in skeleton.video_track.get("segments") or []:
        start, _ = range_of(segment)
        if abs(start - int(intro_new)) > 2000:
            continue
        set_range(segment, "target_timerange", start, int(main_duration))
        if isinstance(segment.get("source_timerange"), dict):
            set_range(segment, "source_timerange", 0, int(main_duration))
        resized += 1
    return resized


def _replace_background(editor, skeleton, intro_new, image):
    """把主歌段的背景换成一张图片；片头的背景保持不动。

    主歌段是起点等于新片头长度的那个画面片段。素材做成 ``photo`` 类型并给足时长；
    区间长度由 :func:`_resize_main_clip` 统一负责。
    """
    if not image or skeleton.video_track is None:
        return 0
    replaced = 0
    for segment in skeleton.video_track.get("segments") or []:
        start, duration = range_of(segment)
        if abs(start - int(intro_new)) > 2000:
            continue
        node = copy.deepcopy(editor.node(segment.get("material_id")) or {})
        node["id"] = new_id()
        node["type"] = "photo"
        node["path"] = image["entry_path"]
        node["material_name"] = image.get("name") or "background.jpg"
        node["duration"] = 10_800_000_000
        node["width"] = int(image.get("width") or 1920)
        node["height"] = int(image.get("height") or 1080)
        node["has_audio"] = False
        editor.add_material("videos", node)
        segment["material_id"] = node["id"]
        set_range(segment, "source_timerange", 0, duration)
        set_range(segment, "target_timerange", start, duration)
        replaced += 1
    return replaced


def _replace_lyrics(editor, skeleton, lyrics, intro_new, mode="subtitle"):
    """用歌词行替换模板的歌词动效卡。

    ``mode="subtitle"`` 写成可被原生引擎直接渲染的普通字幕（离线可见、无动效）；
    ``mode="text"`` 写成**不带 template 的普通文本段**，留给官方
    ``lyrics animation update`` 套官方歌词动效——官方只接受这种目标段。
    """
    track = skeleton.lyric_track or skeleton.subtitle_track
    if track is None:
        raise GuzhuError("模板里没有可承载歌词的文字轨道")
    for segment in list(track.get("segments") or []):
        if editor.bucket(segment.get("material_id")) == "text_templates":
            editor.remove_segment(track, segment)
    for material_id in skeleton.lyric_materials:
        editor.remove_material(material_id)
    # 模板顶层的歌词动效分组已随歌词卡一起失效。
    if editor.t.get("lyrics_effects"):
        editor.t["lyrics_effects"] = []

    if mode == "text":
        # 官方歌词动效只接受"普通文本段"；借用模板歌词卡片段的版式，
        # 但剥掉 template 相关的附加素材，也不会继承任何 template 子节点。
        template_node = None
        template_segment = skeleton.lyric_segment_sample
        if template_segment is None:
            raise GuzhuError("模板里没有可克隆的歌词段结构")
        template_segment = copy.deepcopy(template_segment)
        template_segment["extra_material_refs"] = []
    else:
        sample_material = skeleton.subtitle_sample
        if sample_material is None:
            raise GuzhuError("模板里没有可克隆的字幕样式")
        template_node = copy.deepcopy(editor.node(sample_material))
        template_segment = None
        for _, segment in editor.segments():
            if segment.get("material_id") == sample_material:
                template_segment = copy.deepcopy(segment)
                break
        template_segment = template_segment or {"render_index": 14000}

    written = dropped = 0
    previous_end = int(intro_new)
    for lyric in lyrics:
        text = str(lyric.get("text") or "").strip()
        if not text:
            continue
        start = max(int(lyric["start_us"]), int(intro_new))
        duration = int(lyric["duration_us"])
        if start < previous_end:
            start = previous_end
        if duration < MIN_LYRIC_US:
            dropped += 1
            continue
        if template_node is not None:
            node = copy.deepcopy(template_node)
            node["id"] = new_id()
            retitle(node, text)
            node.pop("text_to_audio_ids", None)
        else:
            node = {
                "id": new_id(),
                "type": "none",
                "language": "zh-CN",
                "content": dump_text_content({
                    "text": text,
                    "styles": [{
                        "fill": {"content": {"render_type": "solid",
                                             "solid": {"color": [1, 1, 1]}}},
                        "size": 8, "range": [0, len(text)]}]}),
                "recognize_text": text,
                "words": even_words(text),
                "initial_scale": 1,
                "layer_weight": 1,
                "lyrics_template": {"path": "", "resource_id": ""},
                "caption_template_info": {"path": "", "resource_id": ""},
            }
        editor.add_material("texts", node)

        segment = copy.deepcopy(template_segment)
        segment["id"] = new_id()
        segment["material_id"] = node["id"]
        segment["extra_material_refs"] = editor.clone_refs(template_segment.get("extra_material_refs"))
        segment.pop("source_timerange", None)
        set_range(segment, "target_timerange", start, duration)
        editor.add_segment(track, segment)
        previous_end = start + duration
        written += 1
    return {"lyrics": written, "lyrics_dropped": dropped}


def prune_orphan_materials(editor):
    """删除不再被任何片段引用的文字/动画/贴纸素材。

    模板的歌词卡会带一批逐词文字素材（每个词一个素材，各自绑定歌词字体），
    歌词卡被替换后它们会变成孤儿并把大字体文件一起拖进包里，必须清掉。
    """
    used = editor.used_materials()
    removed = {}
    for bucket in PRUNABLE_BUCKETS:
        nodes = editor.materials.get(bucket)
        if not isinstance(nodes, list):
            continue
        for node in list(nodes):
            if not isinstance(node, dict):
                continue
            material_id = node.get("id")
            if not material_id or material_id in used:
                continue
            editor.remove_material(material_id)
            removed[bucket] = removed.get(bucket, 0) + 1
    return removed


def trim_to_chorus(timeline, chorus_us):
    """把"整首布局"的草稿裁到副歌起点。

    用在"先按整首让官方识别，再按识别出的副歌时间裁剪"的流程：
    主歌音乐段与画面段从副歌起点开始，起点之前的歌词段整段丢弃，
    其余歌词段整体前移，总时长同步缩短。这样裁剪点是官方识别给的真实
    句首时间，而不是靠能量或行数比例估出来的近似值。
    """
    editor = Editor(timeline)
    skeleton = inspect_template(timeline)
    if not skeleton.main_music:
        raise GuzhuError("没有主歌音乐段，无法按副歌裁剪")
    chorus_us = int(chorus_us)
    intro_us = range_of(skeleton.main_music[0][1])[0]
    delta = chorus_us - intro_us
    if delta <= 0:
        return {"delta_us": 0, "dropped_lyrics": 0, "shifted_lyrics": 0}

    report = {"delta_us": delta}
    for _, segment, _ in skeleton.main_music:
        start, duration = range_of(segment)
        source_start, _ = range_of(segment, "source_timerange")
        keep = max(1, duration - delta)
        set_range(segment, "source_timerange", source_start + delta, keep)
        set_range(segment, "target_timerange", start, keep)

    if skeleton.video_track is not None:
        for segment in skeleton.video_track.get("segments") or []:
            start, duration = range_of(segment)
            if abs(start - int(intro_us)) > 2000:
                continue
            keep = max(1, duration - delta)
            set_range(segment, "target_timerange", start, keep)
            if isinstance(segment.get("source_timerange"), dict):
                set_range(segment, "source_timerange", 0, keep)

    dropped = shifted = 0
    for track, segment in list(editor.segments()):
        material_id = segment.get("material_id")
        node = editor.node(material_id) if material_id else None
        if node is None or editor.bucket(material_id) != "texts":
            continue
        if str(node.get("type")) == "subtitle":
            continue
        start, duration = range_of(segment)
        if start + duration <= chorus_us:
            editor.remove_segment(track, segment)
            dropped += 1
            continue
        if start < chorus_us:
            # 跨着副歌起点的段：从副歌起点截断
            keep = duration - (chorus_us - start)
            set_range(segment, "source_timerange", 0, max(1, keep))
            set_range(segment, "target_timerange", chorus_us - delta, max(1, keep))
            shifted += 1
            continue
        set_range(segment, "target_timerange", start - delta, duration)
        shifted += 1

    total = int(editor.duration())
    new_total = max(intro_us + 1, int(intro_us + (total - intro_us) - delta))
    editor.set_duration(new_total)
    editor.sort_tracks()
    report.update({"dropped_lyrics": dropped, "shifted_lyrics": shifted,
                   "duration_us": new_total})
    return report


def _replace_stickers(editor, skeleton, stickers):
    """把片头每组的贴纸换成按话术情绪挑中的贴纸。

    贴纸素材引用的是剪映素材缓存目录（不在包内），所以只改 name/path/resource_id
    就能换图。关键点是**重算 clip.scale**：模板里不同贴纸的 scale 并不相同
    （开会 240x240 用 0.5755、熊猫头 84x78 用 2.0124），说明视觉尺寸 ≈ 素材像素 ×
    scale。换图后若沿用旧 scale，小图会被放大到铺满整屏。
    """
    if not stickers:
        return 0
    changed = 0
    for index, group in enumerate(skeleton.groups):
        if index >= len(stickers):
            break
        pick = stickers[index]
        if not pick:
            continue
        material_id = getattr(group, "sticker_material", None)
        if not material_id:
            continue
        node = editor.node(material_id)
        if node is None:
            continue
        # 统一尺寸与位置：贴纸素材都被处理成同一画布尺寸，scale 也就用同一个基准值，
        # 居中水平、略向上移，避免压住底部字幕。
        segment = getattr(group, "sticker_segment", None)
        if segment is not None:
            clip = segment.setdefault("clip", {})
            clip["scale"] = {"x": STICKER_SCALE, "y": STICKER_SCALE}
            clip["transform"] = {"x": 0, "y": STICKER_OFFSET_Y}
        node["name"] = pick["name"]
        node["path"] = pick["path"]
        if pick.get("id"):
            node["resource_id"] = pick["id"]
            node["sticker_id"] = pick["id"]
        changed += 1
    return changed


def apply_spec(timeline, spec):
    """按 spec 改造时间线，返回改造报告。"""
    editor = Editor(timeline)
    skeleton = inspect_template(timeline)
    lines = list(spec.get("intro_lines") or [])
    lyrics = list(spec.get("lyrics") or [])
    song = spec.get("song") or {}

    if not lines:
        raise GuzhuError("至少需要一条引流话术")
    for line in lines:
        if not isinstance(line.get("duration_us"), int) or line["duration_us"] <= 0:
            raise GuzhuError("引流话术缺少有效时长：" + str(line.get("text")))
        if not line.get("entry_path"):
            raise GuzhuError("引流话术缺少音频路径：" + str(line.get("text")))
    for key in ("entry_path", "duration_us", "start_us"):
        if key not in song:
            raise GuzhuError("歌曲参数缺少 " + key)

    intro_old = skeleton.intro_end
    intro_new = sum(int(line["duration_us"]) for line in lines)
    # 主歌段时长：默认按这首歌的实际情况给（见 build 阶段的 main_duration_us），
    # 只有没给时才回退到模板自带的主歌时长——不同歌曲长度不同，不能锁死模板值。
    main_duration = int(spec.get("main_duration_us") or skeleton.main_duration)
    if main_duration <= 0:
        raise GuzhuError("主歌段时长必须为正")

    grown = max(0, len(lines) - len(skeleton.groups))
    groups = _grow_groups(editor, skeleton, len(lines)) if grown else skeleton.groups
    report = {"intro_before_us": intro_old, "intro_after_us": intro_new,
              "delta_us": intro_new - intro_old, "intro_groups": len(lines),
              "intro_groups_grown": grown,
              "template_main_duration_us": skeleton.main_duration,
              "main_duration_us": main_duration}

    # 1) 先按模板原始时间轴平移主歌及其后的全部内容。
    #    必须早于片头重排：重排后的片头组可能越过原分界点，否则会被二次平移。
    delta = intro_new - intro_old
    report["shifted_segments"] = editor.shift_from(intro_old, delta)
    editor.shift_template_words(intro_old // 1000, int(round(delta / 1000)))
    report["rescaled_intro_clips"] = _rescale_intro(editor, skeleton, intro_old, intro_new)

    # 2) 重排片头各组，让字幕、贴纸与配音严格对齐。
    cursor = 0
    for index, line in enumerate(lines):
        group = groups[index]
        duration = int(line["duration_us"])
        tts = editor.node(group.tts_material)
        if tts is not None:
            tts["path"] = line["entry_path"]
            tts["name"] = line["text"]
            tts["duration"] = duration
        if group.tts_segment is not None:
            set_range(group.tts_segment, "target_timerange", cursor, duration)
            set_range(group.tts_segment, "source_timerange", 0, duration)
        subtitle = editor.node(group.subtitle_material)
        if subtitle is not None:
            retitle(subtitle, line["text"])
        if group.subtitle_segment is not None:
            set_range(group.subtitle_segment, "target_timerange", cursor, duration)
        if group.sticker_segment is not None:
            set_range(group.sticker_segment, "target_timerange", cursor, duration)
        cursor += duration

    # 3) 删除超出的引流组
    for group in groups[len(lines):]:
        _drop_group(editor, group)

    for _, segment, material_id in skeleton.intro_music + skeleton.main_music:
        node = editor.node(material_id)
        if node is not None:
            node["path"] = song["entry_path"]
            node["name"] = song.get("name") or node.get("name")
            node["duration"] = int(song["duration_us"])

    layout = str(spec.get("audio_layout") or "continue")
    if layout in ("full", "chorus") and skeleton.intro_music:
        # 片头单独一份垫乐素材（chorus=压低 8dB 的歌曲开头，full=静音）。
        # 必须另建素材——片头与主歌原本共用同一个音乐素材，直接改会把主歌也一起改掉。
        template = editor.node(skeleton.intro_music[0][2]) or {}
        pad = copy.deepcopy(template)
        pad["id"] = new_id()
        pad["path"] = spec.get("intro_audio_entry") or template.get("path")
        pad["name"] = "intro-bgm.wav"
        pad["duration"] = max(int(intro_new), 1)
        editor.add_material("audios", pad)
        for _, segment, _ in skeleton.intro_music:
            segment["material_id"] = pad["id"]

    music_offset = 0 if layout in ("full", "chorus") else intro_new
    for _, segment, _ in skeleton.intro_music:
        set_range(segment, "target_timerange", 0, intro_new)
        set_range(segment, "source_timerange", 0, intro_new)
    for _, segment, _ in skeleton.main_music:
        set_range(segment, "target_timerange", intro_new, main_duration)
        set_range(segment, "source_timerange", music_offset, main_duration)

    # 主歌画面段（背景图/视频）随主歌时长伸缩，否则会留出空白或盖住结尾。
    report["main_clip_resized"] = _resize_main_clip(editor, skeleton, intro_new, main_duration)

    if lyrics:
        report.update(_replace_lyrics(editor, skeleton, lyrics, intro_new,
                                      mode=spec.get("lyrics_mode", "subtitle")))

    report["background_replaced"] = _replace_background(
        editor, skeleton, intro_new, spec.get("background"))
    report["stickers_replaced"] = _replace_stickers(
        editor, skeleton, spec.get("stickers"))

    report["pruned_materials"] = prune_orphan_materials(editor)

    duration = intro_new + main_duration
    editor.set_duration(duration)
    editor.sort_tracks()
    report["duration_us"] = duration
    report["max_segment_end_us"] = editor.max_segment_end()
    return report
