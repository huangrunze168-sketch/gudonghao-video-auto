"""把本地识别歌词按官方歌词模板卡生成 Selection Expression。

对齐由 work/lyrics-template-map.json 显式给出（卡 id → 歌词句索引）；本脚本只做
校验与切分，不猜测时间。切分沿用模板原有的槽位字符比例，因此不改变模板设计。

用法：
    python work/build_lyrics_template_selection.py [--map ...] [--workspace ...]
输出：工作区内的 edit.selection 与对账报告。
"""
import argparse
import json
import os
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MAP = ROOT / "work" / "lyrics-template-map.json"
DEFAULT_WORKSPACE = Path(os.environ["LOCALAPPDATA"]) / "Temp" / "jianying-draftediting" / "apply2"
MIN_OVERLAP = 0.5


def xml_escape(value):
    return (value.replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def split_by_weights(words, weights):
    """按槽位权重切分词序列；槽位数无法容纳（词数不足）时返回 None。"""
    texts = [word["text"] for word in words]
    slots = len(weights)
    if slots < 1 or len(texts) < slots:
        return None
    total = sum(weights) or slots
    raw = [weight / total * len(texts) for weight in weights]
    quota = [max(1, int(value)) for value in raw]
    while sum(quota) < len(texts):
        quota[max(range(slots), key=lambda index: raw[index] - quota[index])] += 1
    while sum(quota) > len(texts):
        candidates = [index for index in range(slots) if quota[index] > 1]
        if not candidates:
            return None
        quota[min(candidates, key=lambda index: raw[index] - quota[index])] -= 1
    segments, cursor = [], 0
    for take in quota:
        segments.append("".join(texts[cursor:cursor + take]))
        cursor += take
    return segments


def overlap_ratio(card_start, card_end, cues):
    span = card_end - card_start
    if span <= 0:
        return 0.0
    covered = sum(max(0, min(card_end, cue["end_ms"]) - max(card_start, cue["start_ms"])) for cue in cues)
    return min(1.0, covered / span)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--map", default=str(DEFAULT_MAP))
    parser.add_argument("--workspace", default=str(DEFAULT_WORKSPACE))
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    workspace = Path(args.workspace).resolve(strict=True)
    mapping = json.loads(Path(args.map).read_text(encoding="utf-8"))
    require_schema = mapping.get("schema") == "jianying-lyrics-template-map/v1"
    if not require_schema:
        raise SystemExit("不支持的映射配置 schema")
    lyrics = json.loads((ROOT / mapping["lyrics"]).read_text(encoding="utf-8"))
    cues = lyrics["cues"]
    root = ET.fromstring((workspace / "current_draft.xml").read_text(encoding="utf-8"))
    multi = root.find("multi")
    if multi is None:
        raise SystemExit("canonical XML 缺少 <multi>")
    cards = {node.get("id"): node for node in multi if node.tag == "text" and node.find("template") is not None}

    used, lines, report = set(), [], []
    for entry in mapping["cards"]:
        node = cards.get(entry["id"])
        if node is None:
            raise SystemExit("映射引用了不存在的模板卡: " + str(entry["id"]))
        indices = entry["cues"]
        if len(set(indices)) != len(indices) or used.intersection(indices):
            raise SystemExit("歌词句被重复使用: " + str(indices))
        picked = [cues[index] for index in indices]
        subs = node.find("content").findall("sub")
        timing = node.find("time")
        start = int(timing.get("start"))
        end = start + int(timing.get("duration"))
        ratio = overlap_ratio(start, end, picked)
        words = [word for cue in picked for word in cue["words"]]
        segments = split_by_weights(words, [len(sub.get("text") or "") for sub in subs])
        record = {"id": entry["id"], "cues": indices, "start_ms": start, "end_ms": end,
                  "overlap_ratio": round(ratio, 3), "slots": len(subs), "words": len(words),
                  "old": [sub.get("text") for sub in subs]}
        if ratio < MIN_OVERLAP:
            raise SystemExit(f"卡片 {entry['id']} 与所映射歌词的交叠仅 {ratio:.0%}，低于 {MIN_OVERLAP:.0%}")
        if segments is None:
            raise SystemExit(f"卡片 {entry['id']} 的 {len(subs)} 个槽位无法用 {len(words)} 个词填充")
        record["new"] = segments
        report.append(record)
        used.update(indices)
        # 官方规范：模板多输入框只表达目标结果 —— 按输入框顺序给出多个 <sub>。
        # 逐 sub 改 attr("text") 会被转换器合并成一条 text=1;target=A|B|C，
        # 实测会把整串写进每个槽，因此必须整段替换 content 的子节点。
        fragment = "".join(f'<sub text="{xml_escape(value)}"></sub>' for value in segments)
        lines.append(f'draft.select("#{entry["id"]} content").replaceChildrenXml('
                     f'{json.dumps(fragment, ensure_ascii=False)});')

    output = Path(args.output) if args.output else workspace / "edit.selection"
    # lyra-cli 直连模式要求表达式以 draft.apply() 收尾（Agent 工具会自动补）。
    lines.append("draft.apply();")
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    (workspace / "lyrics-template-report.json").write_text(
        json.dumps({"schema": "jianying-lyrics-template-apply/v1", "selection": str(output),
                    "expressions": len(lines), "cards": report}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    changed = [row for row in report if row["old"] != row["new"]]
    print(json.dumps({"selection": str(output), "expressions": len(lines),
                      "cards": len(report), "changed_cards": len(changed), "report": report},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
