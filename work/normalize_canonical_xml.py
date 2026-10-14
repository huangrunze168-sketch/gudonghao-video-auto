"""按官方 XMLDRAFT 属性所有者模型规范化 canonical XML。

`font_ref` 属于 text|sub|slot|style|text_style，不属于 <subtitle> 宿主；并且它的
值必须是资源库引用，物理路径会被资源校验拒绝（blueprint resource 不支持字体导入）。
因此默认 `--mode drop` 移除 font_ref（文字回退到默认字体），`--mode move` 只把
宿主上的 font_ref 迁到 <sub>，保留给将来资源库支持字体时使用。

用法：python work/normalize_canonical_xml.py [--workspace ...] [--mode drop|move] [--dry-run]
"""
import argparse
import json
import os
from pathlib import Path
import re

DEFAULT_WORKSPACE = Path(os.environ["LOCALAPPDATA"]) / "Temp" / "jianying-draftediting" / "apply2"
FILES = ("target_draft.xml", "current_draft.xml")
BLOCK = re.compile(r"<subtitle\b(?P<attrs>[^>]*)>(?P<body>.*?)</subtitle>", re.S)
FONT = re.compile(r'\s+font_ref="[^"]*"')
ANY_FONT = re.compile(r'\s+font_ref="[^"]*"')


def normalize(text, mode):
    moved = []

    def fix(match):
        found = FONT.search(match.group("attrs"))
        attrs = FONT.sub("", match.group("attrs"))
        body = match.group("body")
        if found:
            moved.append(found.group(0).strip())
        if mode == "move" and found:
            path = found.group(0).split('"')[1]
            body = body.replace('<sub ', f'<sub font_ref="{path}" ')
        return f"<subtitle{attrs}>{body}</subtitle>"

    updated = BLOCK.sub(fix, text)
    if mode == "drop":
        updated = ANY_FONT.sub("", updated)
    return updated, moved


MAIN = re.compile(r"<main\b(?P<attrs>[^>]*)>(?P<body>.*?)</main>", re.S)
VIDEO = re.compile(r"(?P<open>[ \t]*<video\b(?P<attrs>[^>]*)>)(?P<body>.*?)(?P<close></video>)", re.S)
TIME = re.compile(r"<time\b[^>]*/>")
ATTR = re.compile(r'%s="([^"]*)"')


def time_attr(tag, name, default=None):
    found = re.search(ATTR.pattern % name, tag)
    return found.group(1) if found else default


def split_overflow(body, attrs, opener, closer, limit_ms, report, label):
    """把超出素材范围的主轨片段拆成多段（官方审计禁止 source_range 越界）。"""
    timing = TIME.search(body)
    if timing is None:
        return None
    tag = timing.group(0)
    speed = float(time_attr(tag, "speed", "1") or 1)
    start = int(time_attr(tag, "material_start", "0") or 0)
    duration = int(time_attr(tag, "duration", "0") or 0)
    if duration <= 0 or start + duration * speed <= limit_ms + 0.5:
        return None
    base_id = time_attr(attrs, "id", "main")
    cursor, remaining, pieces = start, duration, []
    suffix = 0
    while remaining > 0:
        available = int((limit_ms - cursor) / speed)
        take = min(remaining, available)
        if take <= 0:
            break
        suffix += 1
        segment_id = base_id if suffix == 1 else f"{base_id}_b{suffix}"
        new_attrs = re.sub(ATTR.pattern % "id", f'id="{segment_id}"', attrs)
        new_time = f'<time material_start="{cursor}" duration="{take}" speed="{speed:g}" />'
        pieces.append((opener.replace(attrs, new_attrs),
                       body.replace(tag, new_time), closer, segment_id))
        remaining -= take
        cursor = max(0, limit_ms - int(remaining * speed))
    if remaining > 0:
        report.append({"segment": base_id, "error": "无法在素材范围内容纳该片段"})
        return None
    report.append({"segment": base_id, "ref": time_attr(attrs, "ref"),
                   "original_duration_ms": duration, "limit_ms": limit_ms,
                   "pieces": [{"id": piece[3], "material_start_ms": int(time_attr(piece[1], "material_start")),
                               "duration_ms": int(time_attr(piece[1], "duration"))} for piece in pieces]})
    _ = label
    return "\n".join(piece[0] + piece[1] + piece[2] for piece in pieces)


def fix_main_range(text, durations, report):
    def fix_main(main_match):
        body = main_match.group("body")

        def fix_video(video_match):
            attrs = video_match.group("attrs")
            ref = time_attr(attrs, "ref")
            limit = durations.get(ref)
            if not limit:
                return video_match.group(0)
            fixed = split_overflow(video_match.group("body"), attrs, video_match.group("open"),
                                   video_match.group("close"), limit, report, ref)
            return fixed if fixed else video_match.group(0)

        return "<main" + main_match.group("attrs") + ">" + VIDEO.sub(fix_video, body) + "</main>"

    return MAIN.sub(fix_main, text)


def resource_durations(workspace):
    path = workspace / "resource_map.json"
    if not path.is_file():
        return {}
    result = {}
    for entry in json.loads(path.read_text(encoding="utf-8")):
        duration = (entry.get("metadata") or {}).get("duration_us") or entry.get("duration_us")
        if isinstance(duration, (int, float)) and duration > 0:
            result[entry.get("asset_id")] = int(duration / 1000)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", default=str(DEFAULT_WORKSPACE))
    parser.add_argument("--mode", choices=("drop", "move"), default="drop")
    parser.add_argument("--fix-main-range", action="store_true",
                        help="拆分超出素材范围的主轨片段（官方 apply 目标审计要求）")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    workspace = Path(args.workspace).resolve(strict=True)
    durations = resource_durations(workspace)
    report, splits = {}, []
    for name in FILES:
        path = workspace / name
        text = path.read_text(encoding="utf-8")
        updated, moved = normalize(text, args.mode)
        if args.fix_main_range:
            splits = []
            updated = fix_main_range(updated, durations, splits)
        report[name] = {"font_ref_moved": len(moved), "changed": updated != text, "main_splits": splits}
        if not args.dry_run and updated != text:
            path.write_text(updated, encoding="utf-8")
    print(json.dumps({"workspace": str(workspace), "mode": args.mode, "dry_run": args.dry_run,
                      "files": report}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
