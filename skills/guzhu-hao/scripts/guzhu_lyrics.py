# -*- coding: utf-8 -*-
"""歌词解析与时间换算：LRC 精确时间，或纯文本按行分配。"""
from __future__ import annotations

from pathlib import Path
import re

from guzhu_common import GuzhuError

TIME_TAG = re.compile(r"\[(\d{1,3}):(\d{1,2})(?:[.:](\d{1,3}))?\]")
META_TAG = re.compile(r"^\[[a-zA-Z]+:.*\]$")
MIN_CUE_US = 120_000
DEFAULT_GAP_US = 60_000


def parse_lrc(path):
    """解析 LRC，返回按时间升序排列的 [{time_ms, text}]。"""
    path = Path(path)
    if not path.is_file():
        raise GuzhuError("歌词文件不存在：" + str(path))
    entries = []
    for raw in path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        line = raw.strip()
        if not line or META_TAG.match(line):
            continue
        stamps = list(TIME_TAG.finditer(line))
        if not stamps:
            continue
        text = line[stamps[-1].end():].strip()
        if not text:
            continue
        for stamp in stamps:
            minutes = int(stamp.group(1))
            seconds = int(stamp.group(2))
            fraction = stamp.group(3) or "0"
            if len(fraction) == 1:
                milliseconds = int(fraction) * 100
            elif len(fraction) == 2:
                milliseconds = int(fraction) * 10
            else:
                milliseconds = int(fraction[:3])
            entries.append({"time_ms": (minutes * 60 + seconds) * 1000 + milliseconds,
                            "text": text})
    entries.sort(key=lambda item: item["time_ms"])
    if not entries:
        raise GuzhuError("没有从 LRC 解析出任何歌词：" + str(path))
    return entries


CHORUS_MARKERS = ("副歌", "chorus", "高潮", "chorus:", "refrain")


def is_chorus_marker(text, bracketed=False):
    """判断一行是不是"副歌从这里开始"的标记行。

    作者常在纯文本歌词里单独写一行「副歌」来标注段落。这行不是歌词，
    既不能拿它去对时间，也不能当歌词显示。

    ``bracketed=True`` 表示这行来自 ``[Chorus 1 - Open, Emotional]`` 这类方括号段落标记：
    标记里常带很长的英文情绪说明（实测 27 个字符），所以方括号内不再限制长度，只看是否
    以 chorus/副歌/高潮 开头；裸文本行仍然要求很短，避免把正常歌词判成标记。
    """
    cleaned = str(text).strip().strip("[]【】()（）<>《》-—=*·.　 \t:：")
    if not cleaned:
        return False
    if not bracketed and len(cleaned) > 8:
        return False
    lowered = cleaned.lower()
    # pre-chorus / post-chorus 不是副歌起点，但它们也包含 "chorus"，
    # 实测会把副歌定位到 Pre-Chorus 第一句（早整整 4 行），必须先排除。
    if "pre-chorus" in lowered or "pre chorus" in lowered or "post-chorus" in lowered:
        return False
    return any(marker in lowered for marker in CHORUS_MARKERS)


# 段落标记里的英文说明可能很长：[Chorus 1 - Open, Emotional] / [Pre-Chorus 2 - Rising Tension]
SECTION_RE = re.compile(r"^[\[【(（]\s*([^\]】)）]{1,80})\s*[\]】)）]\s*$")


def parse_lyric_lines(path):
    """读纯文本歌词，剔除段落标记，并找出副歌起点。

    歌词文件常带 ``[Hook]`` / ``[Verse 1]`` / ``[Chorus]`` 这类段落标记。它们不是
    歌词内容，却承载着"副歌从哪开始"的信息：标记里出现 chorus/副歌/高潮 的那一行，
    就是副歌起点。标记行必须全部剔除，否则会被当成歌词参与对齐而错位。

    返回 ``(歌词行, 副歌起始行号)``；没有副歌标记时行号为 ``None``。
    """
    lines, chorus_at = [], None
    for raw in read_plain_lines(path):
        text = str(raw).strip()
        if not text:
            continue
        section = SECTION_RE.match(text)
        if section:
            # 所有方括号段落标记一律剔除，不能留在歌词里污染对齐与显示。
            if chorus_at is None and is_chorus_marker(section.group(1), bracketed=True):
                chorus_at = len(lines)
            continue
        if is_chorus_marker(text):
            if chorus_at is None:
                chorus_at = len(lines)
            continue
        lines.append(text)
    return lines, chorus_at


def read_plain_lines(path):
    """读取纯文本歌词，一行一句。"""
    path = Path(path)
    if not path.is_file():
        raise GuzhuError("歌词文件不存在：" + str(path))
    lines = []
    for raw in path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        text = raw.strip()
        if text and not text.startswith("#"):
            lines.append(text)
    if not lines:
        raise GuzhuError("歌词文件是空的：" + str(path))
    return lines


def cues_from_lrc(path, song_start_us, intro_us, total_us, max_duration_us=None):
    """把 LRC 时间换算成草稿绝对时间，只保留主歌段内的歌词。

    换算关系：草稿时间 = 歌曲时间 - 选段起点。
    """
    entries = parse_lrc(path)
    tail_us = int(song_start_us) + int(total_us)
    cues = []
    for index, entry in enumerate(entries):
        absolute_us = entry["time_ms"] * 1000
        if absolute_us < song_start_us + intro_us:
            continue
        if absolute_us >= tail_us:
            continue
        end_us = tail_us
        if index + 1 < len(entries):
            end_us = min(tail_us, entries[index + 1]["time_ms"] * 1000)
        start_us = absolute_us - song_start_us
        duration_us = end_us - absolute_us - DEFAULT_GAP_US
        if duration_us < MIN_CUE_US:
            continue
        if max_duration_us:
            duration_us = min(duration_us, int(max_duration_us))
        cues.append({"text": entry["text"], "start_us": start_us,
                     "duration_us": duration_us})
    if not cues:
        raise GuzhuError("LRC 主歌段内没有任何可用歌词；请检查选段起点是否落在歌词区间")
    return cues


def cues_from_lines(path, intro_us, total_us):
    """纯文本歌词：在主歌段内按行均匀分配时间。"""
    lines = read_plain_lines(path)
    span = int(total_us) - int(intro_us)
    if span <= 0:
        raise GuzhuError("主歌段时长为零，无法分配歌词")
    each = span // len(lines)
    if each < MIN_CUE_US:
        raise GuzhuError("主歌段太短，装不下 %d 行歌词" % len(lines))
    cues = []
    for index, text in enumerate(lines):
        start = int(intro_us) + index * each
        duration = each if index + 1 < len(lines) else span - index * each
        cues.append({"text": text, "start_us": start,
                     "duration_us": max(MIN_CUE_US, duration - DEFAULT_GAP_US)})
    return cues


def read_cue_times(path):
    """只读取歌词行的绝对毫秒时间，供选段使用；纯文本歌词返回 None。"""
    suffix = Path(path).suffix.lower()
    if suffix in (".lrc", ".srt"):
        return [entry["time_ms"] for entry in parse_lrc(path)]
    return None


def build_cues(path, song_start_us, intro_us, total_us):
    """按扩展名自动选择 LRC 或纯文本处理。"""
    suffix = Path(path).suffix.lower()
    if suffix in (".lrc", ".srt"):
        return cues_from_lrc(path, song_start_us, intro_us, total_us)
    return cues_from_lines(path, intro_us, total_us)
