# -*- coding: utf-8 -*-
"""股东号 skill 公共支撑：定位核心项目、借用剪映引擎加解密、统一报错。"""
from __future__ import annotations

import os
from pathlib import Path
import sys

ENV_ROOT = "JIANYING_HEADLESS_ROOT"


class GuzhuError(RuntimeError):
    """可预期的业务错误；CLI 只打印消息，不打印堆栈。"""


def resolve_project(explicit=None):
    """定位 jianying-headless-windows 检出目录。

    顺序：显式参数 → 环境变量 → 当前工作目录及其上级 → 本文件所在目录及其上级。
    """
    candidates = []
    if explicit:
        candidates.append(Path(explicit))
    env = os.environ.get(ENV_ROOT)
    if env:
        candidates.append(Path(env))
    here = Path(__file__).resolve()
    cwd = Path.cwd()
    candidates.extend([cwd, *cwd.parents, *here.parents])
    seen = set()
    for candidate in candidates:
        try:
            root = Path(candidate).resolve(strict=True)
        except OSError:
            continue
        if root in seen:
            continue
        seen.add(root)
        if (root / "project.json").is_file() and (root / "engine" / "windows_runtime.py").is_file():
            return root
    raise GuzhuError(
        "未找到 jianying-headless-windows 检出目录；"
        "请设置环境变量 " + ENV_ROOT + " 或用 --project 显式指定"
    )


class EngineCrypto:
    """借用核心项目已固定指纹的 videoeditor.dll 桥接加解密草稿。

    核心项目的 `_crypto` 每次调用都会体检一次剪映安装并新起一个隔离子进程，
    因此这里做进程内缓存；批量场景由调用方一次性传入本对象复用。
    """

    def __init__(self, project):
        self.project = Path(project)
        engine = str(self.project / "engine")
        if engine not in sys.path:
            sys.path.insert(0, engine)
        import windows_runtime  # noqa: PLC0415 - 延迟导入以复用核心项目

        self._runtime = windows_runtime
        self._cache = {}

    def _round(self, mode, payload):
        key = (mode, len(payload), hash(payload))
        if key in self._cache:
            return self._cache[key]
        result = self._runtime._crypto(mode, payload)
        if len(self._cache) > 8:
            self._cache.clear()
        self._cache[key] = result
        return result

    def decrypt(self, payload):
        return self._round("decrypt", payload)

    def encrypt(self, payload):
        return self._round("encrypt", payload)


def js(value):
    """紧凑 JSON 序列化，与剪映草稿的书写风格保持一致。"""
    import json

    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
