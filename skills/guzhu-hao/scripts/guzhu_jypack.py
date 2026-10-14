# -*- coding: utf-8 -*-
"""JYPACK 容器读写：JY 魔数 ZIP（PK↔JY）与加密的 draft_content.json。

剪映导出包把 ZIP 的全部 `PK` 签名改写成 `JY`，并用 videoeditor.dll 加密
`draft_content.json` / `draft_meta_info.json`。本模块负责在内存中完成
解包、解密、改内容、重新加密、重新打包，全程不覆盖源包。

另外处理两个已知坑：
1. 剪映有四个必须一致的草稿镜像（根与 Timelines/<id>/ 下各一份
   `draft_content.json` 与 `template-2.tmp`），模板包里它们常常本身就是
   不同步的旧内容，写回必须全部对齐。
2. 换歌换配音后原素材会变成孤儿，需要按引用清理，否则包体积成倍增长。
"""
from __future__ import annotations

from dataclasses import dataclass, field
import io
import json
from pathlib import Path
import re
import shutil
import subprocess
import uuid
import zipfile

from guzhu_common import GuzhuError

JY_TO_PK = {
    b"JY\x03\x04": b"PK\x03\x04",
    b"JY\x01\x02": b"PK\x01\x02",
    b"JY\x05\x06": b"PK\x05\x06",
    b"JY\x06\x06": b"PK\x06\x06",
    b"JY\x06\x07": b"PK\x06\x07",
}
PK_TO_JY = {value: key for key, value in JY_TO_PK.items()}

TIMELINE_NAME = "draft_content.json"
METADATA_NAME = "draft_meta_info.json"
COVER_NAME = "draft_cover.jpg"
MIRROR_FILES = ("draft_content.json", "template-2.tmp", "draft_content.json.bak")
ACTIVE_MIRRORS = ("draft_content.json", "template-2.tmp")
PRUNABLE_PREFIXES = ("ImportedMaterials/", "textReading/", "Resources/audioAlg/",
                     "Resources/combination/")
PRUNE_WHITELIST = ("Resources/defaultPlaceholder.png",)
MIN_DATE = (1980, 1, 1, 0, 0, 0)
PLACEHOLDER_RE = re.compile(r"##_draftpath_placeholder_[^#]+_##[\\/]([^\"\\]+)")
BINARY_SUFFIXES = (".wav", ".mp3", ".mp4", ".aac", ".jpg", ".jpeg", ".png", ".gif",
                   ".ttf", ".otf", ".dat", ".db", ".bak", ".tmp", ".extra")


def decode_container(payload):
    """JY 魔数 → 标准 ZIP 字节。"""
    for jy, pk in JY_TO_PK.items():
        payload = payload.replace(jy, pk)
    if not payload.startswith(b"PK\x03\x04"):
        raise GuzhuError("文件不是受支持的 JY/ZIP 容器")
    return payload


def encode_container(payload):
    """标准 ZIP 字节 → JY 魔数（剪映可导出的形式）。"""
    for pk, jy in PK_TO_JY.items():
        payload = payload.replace(pk, jy)
    return payload


def normalize_name(value):
    """兼容剪映包中未设置 UTF-8 flag、但实际以 UTF-8 写入的文件名。"""
    try:
        return value.encode("cp437").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return value


def raw_name_of(info):
    """取回条目名的原始字节，保证重打包后编码与 flag 不变。"""
    if info.flag_bits & 0x800:
        return info.filename.encode("utf-8")
    try:
        return info.orig_filename.encode("cp437")
    except UnicodeEncodeError:
        return info.orig_filename.encode("utf-8")


def new_id():
    return str(uuid.uuid4()).upper()


class RawZipInfo(zipfile.ZipInfo):
    """覆盖 stdlib 的文件名编码钩子，按原始字节写回条目名。"""

    def __init__(self, raw_name, date_time=MIN_DATE):
        super().__init__(raw_name.decode("utf-8", "surrogateescape"), date_time)
        self._raw_name = raw_name

    def _encodeFilenameFlags(self):  # noqa: N802 - 覆写 stdlib 私有钩子
        return self._raw_name, self.flag_bits


@dataclass
class Entry:
    name: str
    raw_name: bytes
    data: bytes
    date_time: tuple = MIN_DATE
    compress_type: int = zipfile.ZIP_DEFLATED
    external_attr: int = 0


@dataclass
class Package:
    """一个 JYPACK 包在内存中的表示。"""

    source: Path
    entries: dict = field(default_factory=dict)
    timeline: dict = None
    timeline_encrypted: bool = False
    metadata: dict = None
    metadata_encrypted: bool = False

    def names(self):
        return sorted(self.entries)

    def has(self, name):
        return name in self.entries

    def read(self, name):
        entry = self.entries.get(name)
        if entry is None:
            raise GuzhuError("包内没有条目：" + name)
        return entry.data

    def replace(self, name, data):
        """替换或新增条目；总是换上新 Entry 对象，避免污染克隆出来的包。"""
        entry = self.entries.get(name)
        if entry is None:
            entry = Entry(name=name, raw_name=name.encode("utf-8"), data=data)
        else:
            entry = Entry(name=entry.name, raw_name=entry.raw_name, data=data,
                          date_time=entry.date_time, compress_type=entry.compress_type,
                          external_attr=entry.external_attr)
        self.entries[name] = entry
        return entry

    def drop(self, name):
        self.entries.pop(name, None)

    def rename_prefix(self, old_prefix, new_prefix):
        """改条目名前缀；raw_name 必须同步，否则写 ZIP 时仍用旧名字。"""
        for name in list(self.entries):
            if name.startswith(old_prefix):
                entry = self.entries.pop(name)
                new_name = new_prefix + name[len(old_prefix):]
                entry.name = new_name
                entry.raw_name = new_name.encode("utf-8")
                self.entries[new_name] = entry

    def text_entries(self):
        """可当作 UTF-8 文本读的条目（非素材二进制）。"""
        for name, entry in self.entries.items():
            if name.lower().endswith(BINARY_SUFFIXES):
                continue
            try:
                yield name, entry.data.decode("utf-8")
            except UnicodeDecodeError:
                continue

    def dump(self, dest):
        dest = Path(dest)
        if dest.exists():
            raise GuzhuError("拒绝覆盖已存在的输出：" + str(dest))
        dest.parent.mkdir(parents=True, exist_ok=True)
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
            for entry in self.entries.values():
                date_time = entry.date_time if entry.date_time >= MIN_DATE else MIN_DATE
                info = RawZipInfo(entry.raw_name, date_time)
                info.compress_type = (entry.compress_type
                                      if entry.compress_type in (zipfile.ZIP_STORED,
                                                                 zipfile.ZIP_DEFLATED)
                                      else zipfile.ZIP_DEFLATED)
                info.external_attr = entry.external_attr
                archive.writestr(info, entry.data)
        dest.write_bytes(encode_container(buffer.getvalue()))
        return dest


def _load_json(raw, label, strict=True):
    """解析 UTF-8 JSON；strict=False 时把"解析不出来"当作"内容已加密"。"""
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        if strict:
            raise GuzhuError(label + " 不是 UTF-8 文本：" + str(error)) from error
        return None
    try:
        return json.loads(text)
    except ValueError as error:
        if strict:
            raise GuzhuError(label + " 不是合法 JSON：" + str(error)) from error
        return None


def read_package(path, crypto=None, decrypt=True):
    """读取 JYPACK，可选地解密时间线与元信息。"""
    path = Path(path)
    try:
        path = path.resolve(strict=True)
    except OSError as error:
        raise GuzhuError("输入包不存在：" + str(path)) from error
    if not path.is_file() or path.suffix.lower() != ".jypack":
        raise GuzhuError("输入必须是 .jypack 普通文件：" + str(path))

    decoded = decode_container(path.read_bytes())
    entries = {}
    try:
        with zipfile.ZipFile(io.BytesIO(decoded)) as archive:
            bad = archive.testzip()
            if bad is not None:
                raise GuzhuError("包内 CRC 校验失败：" + str(bad))
            for info in archive.infolist():
                name = normalize_name(info.filename)
                data = b"" if info.is_dir() else archive.read(info)
                entries[name] = Entry(name=name, raw_name=raw_name_of(info), data=data,
                                      date_time=info.date_time,
                                      compress_type=info.compress_type,
                                      external_attr=info.external_attr)
    except zipfile.BadZipFile as error:
        raise GuzhuError("包不是合法 ZIP：" + str(error)) from error

    package = Package(source=path, entries=entries)
    if not decrypt:
        return package

    if TIMELINE_NAME not in entries:
        raise GuzhuError("包内缺少 " + TIMELINE_NAME)
    timeline = _load_json(entries[TIMELINE_NAME].data, TIMELINE_NAME, strict=False)
    if timeline is None:
        if crypto is None:
            raise GuzhuError("时间线已加密；需要剪映引擎才能读取")
        timeline = _load_json(crypto.decrypt(entries[TIMELINE_NAME].data),
                              "解密后的 " + TIMELINE_NAME)
        package.timeline_encrypted = True
    if not isinstance(timeline, dict):
        raise GuzhuError(TIMELINE_NAME + " 顶层必须是对象")
    package.timeline = timeline

    if METADATA_NAME in entries:
        metadata = _load_json(entries[METADATA_NAME].data, METADATA_NAME, strict=False)
        if metadata is None and crypto is not None:
            metadata = _load_json(crypto.decrypt(entries[METADATA_NAME].data),
                                  "解密后的 " + METADATA_NAME)
            package.metadata_encrypted = True
        if isinstance(metadata, dict):
            package.metadata = metadata
    return package


def collect_references(package):
    """收集包内所有被引用的草稿占位资源路径。"""
    references = set()

    def scan(text):
        for match in PLACEHOLDER_RE.finditer(text):
            references.add(match.group(1).replace("\\", "/").strip())

    if package.timeline is not None:
        scan(json.dumps(package.timeline, ensure_ascii=False))
    if package.metadata is not None:
        scan(json.dumps(package.metadata, ensure_ascii=False))
    for _, text in package.text_entries():
        scan(text)
    return references


def prune_unreferenced(package):
    """删除素材目录里不再被引用的孤儿文件。"""
    references = collect_references(package)
    removed = []
    for name in list(package.entries):
        if not name.startswith(PRUNABLE_PREFIXES):
            continue
        if name.endswith("/") or name in PRUNE_WHITELIST or name in references:
            continue
        package.drop(name)
        removed.append(name)
    return removed


def retarget_timeline(package, new_timeline_id):
    """把时间线 id 换成新值，并同步目录名与所有明文字段。"""
    timeline = package.timeline
    old_id = timeline.get("id")
    if not new_timeline_id or old_id == new_timeline_id:
        return old_id
    timeline["id"] = new_timeline_id
    if isinstance(old_id, str) and old_id:
        package.rename_prefix("Timelines/%s/" % old_id, "Timelines/%s/" % new_timeline_id)
        for name, text in list(package.text_entries()):
            if name in (TIMELINE_NAME, METADATA_NAME):
                continue
            if old_id in text:
                package.replace(name, text.replace(old_id, new_timeline_id).encode("utf-8"))
        if package.metadata is not None:
            for key, value in list(package.metadata.items()):
                if isinstance(value, str) and old_id in value:
                    package.metadata[key] = value.replace(old_id, new_timeline_id)
    return old_id


def update_metadata(package, draft_name=None, song=None):
    """同步草稿元信息：草稿名、素材库里的音乐条目。"""
    metadata = package.metadata
    if metadata is None:
        return {}
    changes = {}
    if draft_name:
        metadata["draft_name"] = draft_name
        metadata["draft_id"] = new_id()
        folder = metadata.get("draft_fold_path")
        if isinstance(folder, str) and folder:
            parent = folder.replace("\\", "/").rsplit("/", 1)[0]
            metadata["draft_fold_path"] = parent + "/" + draft_name
        changes["draft_name"] = draft_name
    if song:
        for group in metadata.get("draft_materials") or []:
            for item in group.get("value") or []:
                if not isinstance(item, dict) or item.get("metetype") != "music":
                    continue
                item["file_Path"] = song["entry_path"]
                item["extra_info"] = song.get("file_name") or song.get("name")
                item["duration"] = int(song["source_duration_us"])
                changes["music_items"] = changes.get("music_items", 0) + 1
    return changes


def mirror_names(timeline_id):
    names = []
    for name in MIRROR_FILES:
        names.append(name)
        names.append("Timelines/%s/%s" % (timeline_id, name))
    return names


def active_mirror_names(timeline_id):
    names = []
    for name in ACTIVE_MIRRORS:
        names.append(name)
        names.append("Timelines/%s/%s" % (timeline_id, name))
    return names


def relative_entry(path):
    """从草稿占位路径里取出包内相对路径。"""
    if not isinstance(path, str) or not path:
        return None
    index = path.find("_##/")
    if index >= 0:
        return path[index + 4:].replace("\\", "/")
    if path.startswith("##") or path.startswith("/") or ":" in path[:3]:
        return None
    return path.replace("\\", "/")


def sniff_media(data):
    """按文件头识别素材真实格式；识别不了就返回 None。"""
    if not data:
        return None
    if data[:3] == b"\xff\xd8\xff":
        return "jpeg"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "gif"
    if data[:2] == b"BM":
        return "bmp"
    if data[:4] in (b"II*\x00", b"MM\x00*"):
        return "tiff"
    if data[:4] == b"RIFF":
        return "webp" if data[8:12] == b"WEBP" else "riff"
    if len(data) > 12 and data[4:8] == b"ftyp":
        return "isobmff"
    if data[:4] == b"\x1aE\xdf\xa3":
        return "matroska"
    if data[:3] == b"ID3" or data[:2] in (b"\xff\xfb", b"\xff\xf3", b"\xff\xf2"):
        return "mp3"
    if data[:4] == b"fLaC":
        return "flac"
    if data[:4] == b"OggS":
        return "ogg"
    if data[:5] == b"%PDF-":
        return "pdf"
    if data[:4] in (b"\x00\x01\x00\x00", b"OTTO", b"true", b"ttcf"):
        return "font"
    return None


IMAGE_KINDS = ("jpeg", "png", "gif", "bmp", "tiff", "webp")
AUDIO_KINDS = ("riff", "mp3", "flac", "ogg", "isobmff", "matroska")
VIDEO_KINDS = ("isobmff", "matroska")


def _solid_image(path, width, height, color):
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise GuzhuError("PATH 中找不到 ffmpeg，无法修复不可读的图片素材")
    completed = subprocess.run(
        [ffmpeg, "-v", "error", "-y", "-f", "lavfi",
         "-i", "color=c=%s:s=%dx%d" % (color, max(16, int(width)), max(16, int(height))),
         "-frames:v", "1", "-q:v", "3", str(path)],
        capture_output=True, timeout=180)
    if completed.returncode != 0 or not Path(path).is_file():
        raise GuzhuError("生成纯色图片失败：" +
                         completed.stderr.decode("utf-8", "replace").strip()[:200])


def repair_media(package, work_dir, color="black"):
    """检查被引用的素材是否真的可读。

    剪映导出的 JYPACK 会把部分素材（实测是图片）保持打包加密状态，只有经过
    剪映导入才会被解密重绑。原生渲染直接读草稿文件，遇到这种加密素材会
    **静默丢弃整个片段**（片头直接消失、成片变短）。图片可以用纯色图顶替，
    其它类型无法自动修复，必须明确失败而不是交出残缺成片。
    """
    timeline = package.timeline
    if timeline is None:
        raise GuzhuError("没有可检查的时间线")
    work_dir = Path(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    canvas = timeline.get("canvas_config") or {}
    repaired, blocked = [], []
    index = 0
    for bucket, allowed in (("videos", None), ("audios", AUDIO_KINDS)):
        for node in timeline.get("materials", {}).get(bucket) or []:
            if not isinstance(node, dict):
                continue
            relative = relative_entry(node.get("path"))
            if not relative or not package.has(relative):
                continue
            kinds = allowed
            if bucket == "videos":
                kinds = IMAGE_KINDS if node.get("type") == "photo" else VIDEO_KINDS
            kind = sniff_media(package.read(relative))
            if kind in kinds:
                continue
            if bucket == "videos" and node.get("type") == "photo":
                index += 1
                width = node.get("width") or canvas.get("width") or 1920
                height = node.get("height") or canvas.get("height") or 1080
                target = work_dir / ("solid-%02d.jpg" % index)
                if target.exists():
                    target.unlink()
                _solid_image(target, width, height, color)
                package.replace(relative, target.read_bytes())
                repaired.append({"entry": relative, "detected": kind,
                                 "action": "替换为纯色图片", "size": [int(width), int(height)]})
            else:
                blocked.append({"entry": relative, "detected": kind,
                                "material_type": node.get("type"), "bucket": bucket})
    return {"repaired": repaired, "blocked": blocked}


def seal(package, crypto, dest, cover=None, timeline_id=None, prune=True):
    """写回磁盘：对齐四个草稿镜像，重新加密，再打包成 JY/ZIP。"""
    if package.timeline is None:
        raise GuzhuError("没有可写回的时间线")

    if timeline_id:
        retarget_timeline(package, timeline_id)
    current_id = package.timeline.get("id")
    if not isinstance(current_id, str) or not current_id:
        raise GuzhuError("时间线缺少 id")

    payload = json.dumps(package.timeline, ensure_ascii=False,
                         separators=(",", ":")).encode("utf-8")
    if package.timeline_encrypted:
        payload = crypto.encrypt(payload)
    for name in active_mirror_names(current_id):
        package.replace(name, payload)
    for name in mirror_names(current_id):
        if name in package.entries and name not in active_mirror_names(current_id):
            package.replace(name, payload)

    if package.metadata is not None:
        meta_payload = json.dumps(package.metadata, ensure_ascii=False,
                                  separators=(",", ":")).encode("utf-8")
        if package.metadata_encrypted:
            meta_payload = crypto.encrypt(meta_payload)
        package.replace(METADATA_NAME, meta_payload)

    if cover is not None:
        package.replace(COVER_NAME, Path(cover).read_bytes())

    removed = prune_unreferenced(package) if prune else []
    result = package.dump(dest)
    return {"path": str(result), "pruned": removed}
