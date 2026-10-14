#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""歌词模板字体：审计、下载、双位置落盘。

官方 CLI 的字体下载有两个实测坑，本模块把它们封装成可复用能力：

1. **字体是"假下载"**：`material download --type font` 报
   ``upstream -100202 / resource_pool -7002 / download -1008 / cannot unzip file``，
   即服务端返回的字体包在 CLI 侧解压失败（包内中文文件名编码问题）。
   目录里只剩 ``font.lock``，**没有真正的字体文件**，渲染时静默回退默认字体。
   绕过方式（仍走官方接口）：``material query`` 拿官方签名 CDN 地址 →
   下载 → Python ``zipfile`` 解压 → **校验官方 md5**。

2. **字体必须放两个位置，只放一个不生效**：
   ``Cache/lyra-cli/material-cache/font/<id>/font.<ext>``（资源缓存）
   ``Cache/effect/<id>/<name>.<ext>``（草稿 ``font.path`` 指向这里，渲染读这个）
   官方正常下载会同时写两处；只写前者时，即使草稿里的 font_id 正确，
   画面依然是默认字体。

用法：
    python guzhu_fonts.py audit                     # 审计所有模板的字体依赖
    python guzhu_fonts.py fetch --font-id <id>      # 补一个字体（含双位置落盘）
    python guzhu_fonts.py ensure --all              # 补齐所有缺失字体
    python guzhu_fonts.py ensure --template <id>    # 只补某个模板需要的字体
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import sys
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(ROOT / "engine"))

FONT_SUFFIX = (".ttf", ".otf", ".ttc")
MIN_FONT_BYTES = 1024


def cache_root() -> Path:
    base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData/Local")
    return Path(base) / "JianyingPro/User Data/Cache"


def font_dir() -> Path:
    return cache_root() / "lyra-cli" / "material-cache" / "font"


def effect_dir() -> Path:
    return cache_root() / "effect"


def lyric_dir() -> Path:
    return cache_root() / "lyra-cli" / "material-cache" / "lyric_animation"


def real_fonts(folder: Path):
    """目录里真正可用的字体文件（>1KB 才算，排除 0 字节的 lock 残骸）。"""
    if not folder.is_dir():
        return []
    return [f for f in folder.rglob("*")
            if f.is_file() and f.suffix.lower() in FONT_SUFFIX
            and f.stat().st_size > MIN_FONT_BYTES]


def font_state(font_id: str):
    """返回 (状态, 字节数)。

    判定要点：**草稿的 font.path 指向 font/<id>/font.lock，渲染器直接读这个文件**。
    所以 font.lock 必须是真实字体内容；它是 0 字节时渲染会静默回退默认字体
    （删掉它则直接报"草稿引用的本地资源不存在"）。
    """
    folder = font_dir() / font_id
    lock = folder / "font.lock"
    lock_ok = lock.is_file() and lock.stat().st_size > MIN_FONT_BYTES
    cached = real_fonts(folder)
    in_effect = real_fonts(effect_dir() / font_id)
    if lock_ok and cached and in_effect:
        return "ok", lock.stat().st_size
    missing = []
    if not cached:
        missing.append("font/")
    if not in_effect:
        missing.append("effect/")
    if not lock_ok:
        missing.append("font.lock(空)")
    if not missing:
        return "ok", lock.stat().st_size if lock.is_file() else 0
    if cached or in_effect or lock_ok:
        return "half(缺 %s)" % "、".join(missing), 0
    if folder.is_dir():
        return ("lock-only" if any(folder.iterdir()) else "empty-dir"), 0
    return "missing-dir", 0


def font_ids_of_style(style_path: Path):
    try:
        data = json.loads(Path(style_path).read_text(encoding="utf-8", errors="replace"))
    except Exception:  # noqa: BLE001
        return []
    found = set()

    def walk(node):
        if isinstance(node, dict):
            for key, value in node.items():
                if key in ("font_id", "font_resource_id"):
                    values = value if isinstance(value, list) else [value]
                    for v in values:
                        if str(v).isdigit() and len(str(v)) >= 15:
                            found.add(str(v))
                else:
                    walk(value)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(data)
    return sorted(found)


def template_fonts(template_id: str):
    style = next((lyric_dir() / template_id).rglob("LyricStyle.json"), None) \
        if (lyric_dir() / template_id).is_dir() else None
    return font_ids_of_style(style) if style else []


def all_templates():
    base = lyric_dir()
    if not base.is_dir():
        return []
    return sorted(d.name for d in base.iterdir()
                  if d.is_dir() and next(d.rglob("LyricStyle.json"), None))


def download_font(font_id: str, dry_run: bool = False):
    """下载一个字体并落到两个位置。返回结果字典。"""
    state, _size = font_state(font_id)
    if state == "ok":
        return {"font_id": font_id, "status": "already-ok"}
    from official_materials import execute  # 官方调用器

    query = execute(ROOT, ["material", "query", "--type", "font",
                           "--resource-id", font_id])
    body = (((query.get("envelope") or {}).get("result") or {}).get("result") or {})
    items = body.get("items") or []
    if not items:
        return {"font_id": font_id, "status": "query-empty",
                "cli": query.get("status")}
    item = items[0]
    urls = item.get("download_urls") or []
    expect = str(item.get("md5") or "").lower()
    if not urls:
        return {"font_id": font_id, "status": "no-url"}
    if dry_run:
        return {"font_id": font_id, "status": "would-download",
                "title": item.get("title"), "md5": expect}
    blob = urllib.request.urlopen(urls[0], timeout=180).read()
    got = hashlib.md5(blob).hexdigest().lower()
    if expect and got != expect:
        return {"font_id": font_id, "status": "md5-mismatch",
                "expected": expect, "got": got}
    archive = zipfile.ZipFile(io.BytesIO(blob))
    names = [n for n in archive.namelist() if n.lower().endswith(FONT_SUFFIX)]
    if not names:
        return {"font_id": font_id, "status": "no-font-in-zip",
                "entries": archive.namelist()[:6]}
    written = []
    # 位置一：资源缓存（剪映期望固定名 font.<ext>）
    primary_name = None
    for name in names:
        content = archive.read(name)
        if len(content) <= MIN_FONT_BYTES:
            continue
        ext = Path(name.replace("\\", "/")).name
        ext = Path(ext).suffix.lower() or ".ttf"
        cached = font_dir() / font_id
        cached.mkdir(parents=True, exist_ok=True)
        target = cached / ("font" + ext)
        target.write_bytes(content)
        if primary_name is None or len(content) > written[-1]["bytes"]:
            primary_name = target.name
        written.append({"name": target.name, "bytes": len(content)})
    if not written:
        return {"font_id": font_id, "status": "empty-font"}
    # 位置二：effect 目录（草稿 font.path 指向这里，渲染实际读取）
    source = font_dir() / font_id / primary_name
    placed = effect_dir() / font_id
    placed.mkdir(parents=True, exist_ok=True)
    dest = placed / primary_name
    dest.write_bytes(source.read_bytes())
    # 位置三（最关键）：font.lock —— 草稿的 font.path 就是它，渲染器直接读
    lock = font_dir() / font_id / "font.lock"
    lock.write_bytes(source.read_bytes())
    # 官方结构里还有 <font_id>/<font_id>/<原文件名> + 紧凑 config.json
    inner_dir = font_dir() / font_id / font_id
    inner_dir.mkdir(parents=True, exist_ok=True)
    (inner_dir / primary_name).write_bytes(source.read_bytes())
    (inner_dir / "config.json").write_text(
        '{"effect":{"Link":[{"type":"InfoSticker"}]},"version":"3.1.1"}', encoding="utf-8")
    state_after, size = font_state(font_id)
    return {"font_id": font_id, "status": "ok" if state_after == "ok" else state_after,
            "file": primary_name, "bytes": size, "md5": expect,
            "places": [str(source), str(dest), str(lock), str(inner_dir / primary_name)]}


def audit(verbose=True):
    templates = all_templates()
    rows = {}
    fonts = {}
    for tid in templates:
        ids = template_fonts(tid)
        states = []
        for fid in ids:
            state, size = font_state(fid)
            states.append(state)
            fonts.setdefault(fid, {"state": state, "size": size, "templates": []})
            fonts[fid]["templates"].append(tid)
        if not ids:
            overall = "no-font-dep"
        elif all(s == "ok" for s in states):
            overall = "ok"
        elif any(s == "ok" for s in states):
            overall = "partial"
        else:
            overall = "missing"
        rows[tid] = {"fonts": ids, "states": states, "state": overall}
    if verbose:
        counts = {}
        for row in rows.values():
            counts[row["state"]] = counts.get(row["state"], 0) + 1
        bad = {k: v for k, v in fonts.items() if v["state"] != "ok"}
        print("模板 %d 个，字体 %d 个" % (len(rows), len(fonts)))
        print("模板状态: %s" % counts)
        print("不可用字体: %d 个" % len(bad))
        for fid, info in sorted(bad.items(), key=lambda kv: -len(kv[1]["templates"]))[:15]:
            print("  %-20s %-16s 影响 %d 个模板" % (fid, info["state"],
                                                 len(info["templates"])))
    return {"templates": rows, "fonts": fonts}


def ensure(font_ids, dry_run=False):
    results = []
    for fid in font_ids:
        row = download_font(fid, dry_run=dry_run)
        results.append(row)
        print("  %-20s %s %s" % (fid, row["status"],
                                 row.get("file") or row.get("title") or ""), flush=True)
    ok = sum(1 for r in results if r["status"] in ("ok", "already-ok"))
    print("完成：可用 %d / %d" % (ok, len(results)))
    return results


def main(argv=None):
    parser = argparse.ArgumentParser(description="歌词模板字体审计与补齐")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_audit = sub.add_parser("audit", help="审计所有模板的字体依赖")
    p_audit.add_argument("--output", default=None)

    p_fetch = sub.add_parser("fetch", help="补一个字体")
    p_fetch.add_argument("--font-id", required=True)
    p_fetch.add_argument("--dry-run", action="store_true")

    p_ensure = sub.add_parser("ensure", help="批量补齐缺失字体")
    p_ensure.add_argument("--all", action="store_true")
    p_ensure.add_argument("--template", default=None)
    p_ensure.add_argument("--dry-run", action="store_true")

    args = parser.parse_args(argv)

    if args.cmd == "audit":
        report = audit()
        if args.output:
            Path(args.output).write_text(json.dumps(report, ensure_ascii=False, indent=2),
                                         encoding="utf-8")
            print("已写入 %s" % args.output)
        return 0

    if args.cmd == "fetch":
        row = download_font(args.font_id, dry_run=args.dry_run)
        print(json.dumps(row, ensure_ascii=False, indent=2))
        return 0 if row["status"] in ("ok", "already-ok", "would-download") else 1

    if args.cmd == "ensure":
        if args.template:
            ids = template_fonts(args.template)
        else:
            report = audit(verbose=False)
            ids = sorted(report["fonts"])
        missing = [fid for fid in ids if font_state(fid)[0] != "ok"]
        print("待处理字体 %d 个" % len(missing))
        ensure(missing, dry_run=args.dry_run)
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
