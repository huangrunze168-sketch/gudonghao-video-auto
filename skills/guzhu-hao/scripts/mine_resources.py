#!/usr/bin/env python3
"""刷新剪映官方 CLI 的能力清单与本机资源池。

三条产物（都落在 ``references/``）：

- ``cli-commands.md``       官方命令行能力清单，按域分组
- ``effect-pool.json``      可用效果资源池（名称 -> id，均已确认本地有实体）
- ``resource-index.json``   全部素材缓存里能挖到名称的资源索引

为什么需要挖：素材缓存里的资源**没有可读名称**（名字在服务器上），但**凡是被用过的
资源**都会把 ``name`` + ``resource_id`` 写进草稿。所以「扫全部草稿拿名字 + 扫全部
缓存确认本地有实体」就能得到当下可用的资源清单，不必一个类型一个类型去试。

用法：

    python scripts/mine_resources.py --project "C:\\path\\to\\jianying-headless-windows"
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

NAME_KEYS = ("name", "title", "label", "display_name", "effect_name", "resource_name")
ID_KEYS = ("resource_id", "effect_id", "transition_id", "animation_id", "filter_id",
           "sticker_id", "text_effect_id", "audio_effect_id", "material_id")
MAX_JSON_BYTES = 600_000


def cache_root():
    return Path(os.environ.get("LOCALAPPDATA", "")) / "JianyingPro" / "User Data" / "Cache"


def draft_root():
    return (Path(os.environ.get("LOCALAPPDATA", "")) / "JianyingPro"
            / "User Data" / "Projects" / "com.lveditor.draft")


def resource_is_local(resource_id, root=None):
    """资源在本机缓存里有没有实体（必须扫全部子目录，不同资源类型放不同子目录）。"""
    root = root or cache_root()
    if not root.is_dir():
        return True
    return any((folder / str(resource_id)).is_dir()
               for folder in root.iterdir() if folder.is_dir())


def dump_commands(engine_dir, references):
    source = Path(engine_dir) / "lyra_commands.json"
    if not source.is_file():
        return None
    data = json.loads(source.read_text(encoding="utf-8"))
    groups = {}
    for item in data.get("commands") or []:
        path = [str(part) for part in (item.get("path") or [])]
        if not path:
            continue
        groups.setdefault(path[0] if len(path) > 1 else "(顶层)", []).append({
            "name": ".".join(path),
            "summary": str(item.get("summary") or "").strip(),
            "options": [str(opt) for opt in (item.get("options") or [])],
        })
    lines = ["# 剪映官方 CLI 能力清单", "",
             "由 `engine/lyra_commands.json` 生成。全部命令都经",
             "`engine/draftediting_runtime.py` 在官方 VMSDK 沙箱内执行；",
             "直接调 `lyra-cli.exe` 会报 `unauthorized host process`。", ""]
    for group in sorted(groups):
        rows = sorted(groups[group], key=lambda row: row["name"])
        lines += ["## %s（%d 条）" % (group, len(rows)), "",
                  "| 命令 | 用途 | 关键参数 |", "| --- | --- | --- |"]
        for row in rows:
            options = [opt for opt in row["options"] if opt not in ("--help", "--version", "--jq")]
            shown = ", ".join(options[:8]) + (" …" if len(options) > 8 else "")
            lines.append("| `%s` | %s | %s |" % (row["name"], row["summary"] or "-", shown or "-"))
        lines.append("")
    (Path(references) / "cli-commands.md").write_text("\n".join(lines), encoding="utf-8")
    return sum(len(value) for value in groups.values())


def dump_cache_index(references):
    """遍历全部缓存子目录，抽每个资源元数据里的 name。"""
    index = {}
    root = cache_root()
    if not root.is_dir():
        return index
    if str(Path(__file__).resolve().parents[2]) not in sys.path:
        pass
    for cache_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        found = {}
        try:
            resources = [d for d in cache_dir.iterdir() if d.is_dir()]
        except OSError:
            continue
        for resource in resources:
            entry = {"name": None, "files": []}
            try:
                files = [f for f in resource.rglob("*") if f.is_file()]
            except OSError:
                continue
            for path in files:
                entry["files"].append(path.name)
                if entry["name"] or path.suffix.lower() != ".json":
                    continue
                try:
                    if path.stat().st_size > MAX_JSON_BYTES:
                        continue
                    data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
                except (OSError, ValueError):
                    continue
                if isinstance(data, dict):
                    for key in NAME_KEYS:
                        value = data.get(key)
                        if isinstance(value, str) and value.strip():
                            entry["name"] = value.strip()
                            break
            if entry["name"]:
                found[resource.name] = {"name": entry["name"], "files": entry["files"][:6]}
        if found:
            index[cache_dir.name] = found
    (Path(references) / "resource-index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")
    return index


def dump_pool(project, references):
    """扫草稿收集 (bucket -> id -> name)，只保留本地有实体的。"""
    sys.path.insert(0, str(Path(project) / "engine"))
    import windows_runtime  # noqa: PLC0415

    names = {}
    root = draft_root()
    scanned = 0
    for folder in root.iterdir() if root.is_dir() else []:
        if not folder.is_dir():
            continue
        content = folder / "draft_content.json"
        if not content.is_file():
            continue
        try:
            timeline = windows_runtime._decrypt_metadata_in_memory(content)
        except Exception:  # noqa: BLE001
            continue
        scanned += 1
        for bucket, items in (timeline.get("materials") or {}).items():
            if not isinstance(items, list):
                continue
            for item in items:
                if not isinstance(item, dict):
                    continue
                name = item.get("name")
                rid = next((item.get(key) for key in ID_KEYS if item.get(key)), None)
                if name and rid and str(rid).isdigit():
                    names.setdefault(bucket, {})[str(rid)] = str(name)
    pool = {}
    for bucket, items in names.items():
        ready = {rid: name for rid, name in items.items() if resource_is_local(rid)}
        if ready:
            pool[bucket] = ready
    counts = {}
    local_root = cache_root()
    if local_root.is_dir():
        for folder in local_root.iterdir():
            if folder.is_dir():
                try:
                    counts[folder.name] = sum(1 for child in folder.iterdir() if child.is_dir())
                except OSError:
                    continue
    pool["_cache_counts"] = counts
    pool["_scanned_drafts"] = scanned
    (Path(references) / "effect-pool.json").write_text(
        json.dumps(pool, ensure_ascii=False, indent=2), encoding="utf-8")
    return pool


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True,
                        help="jianying-headless-windows 检出目录（含 engine/）")
    parser.add_argument("--references", default=None,
                        help="产物输出目录，默认本 skill 的 references/")
    args = parser.parse_args(argv)

    project = Path(args.project).resolve()
    references = Path(args.references) if args.references else (
        Path(__file__).resolve().parent.parent / "references")
    references.mkdir(parents=True, exist_ok=True)

    total = dump_commands(project / "engine", references)
    print("命令清单：%s 条 -> cli-commands.md" % total)

    pool = dump_pool(project, references)
    kinds = {key: len(value) for key, value in pool.items() if not key.startswith("_")}
    print("效果资源池 -> effect-pool.json：%s" % kinds)
    counts = pool.get("_cache_counts") or {}
    top = sorted(counts.items(), key=lambda pair: -pair[1])[:8]
    print("缓存资源数（前 8）：%s" % "、".join("%s=%d" % row for row in top))

    index = dump_cache_index(references)
    named = sum(len(value) for value in index.values())
    print("带名称资源索引 -> resource-index.json：%d 个（%d 个缓存目录）"
          % (named, len(index)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
