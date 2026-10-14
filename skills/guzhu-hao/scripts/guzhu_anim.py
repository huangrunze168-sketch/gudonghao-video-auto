"""通过官方在线素材搜索及下载选择剪映歌词模板。

候选按歌词意境推荐，不读取本地字体库存筛选。视觉质量在官方套用及原生导出后
验收；在线失败时停止，不自动回退本地模板。保留的缓存分析及旧贴纸辅助函数
仅用于历史诊断，不作为官方歌词模板自动选择路径。
"""

import json
import os
import subprocess
import sys
from pathlib import Path

# 已验证观感良好、作为兜底的通用动效
DEFAULT_ANIMATION = "7591420714515844395"

# 风格 -> 资源标题里出现的关键词（小写比较）
STYLE_TITLE_HINTS = {
    "guofeng": ("chinesecalligraphy", "guofengdazi", "gangfeng", "国风", "书法"),
    "handwrite": ("文艺手写", "shouxiedazi", "多彩手写", "手写"),
    "rock": ("节奏摇滚", "stomp", "broken", "摇滚"),
    "sweet": ("lovely_pink", "sweet", "可爱", "甜"),
    "rainy": ("雨雾渐显", "raindrop", "emotion", "雨"),
    "retro": ("fugu", "复古", "港风"),
    "simple": ("clear", "simpleirregular", "jianyue", "简约", "mohu", "gecishaizi",
               "colorbold"),
    "mv": ("mv", "ktv", "moji"),
}

# 歌词里出现这些词，就认为该走对应气质
LYRIC_STYLE_WORDS = {
    "guofeng": ("金戈", "铁马", "战鼓", "边塞", "将军", "琵琶", "胭脂", "红袖", "孤烟",
                "大漠", "金甲", "漠北", "麒麟", "白发", "长枪", "策马", "关山", "沙场",
                "江山", "侠", "剑", "刀", "烽火", "塞外", "青史", "故人", "长安", "胭脂扣"),
    "rainy": ("雨", "泪", "潮湿", "窗前", "思念", "想你", "离开", "错过", "遗憾",
              "哭", "痛", "伤", "认输", "名分", "委屈", "心酸", "难堪", "留不住",
              "不算数", "贪心", "红过眼", "哽咽",
              "孤独", "深夜", "月亮", "回忆"),
    "sweet": ("甜", "喜欢你", "开心", "微笑", "阳光", "心动", "拥抱", "温柔", "暖"),
    "rock": ("燃烧", "爆发", "嘶吼", "fight", "fire", "撞", "疯狂", "炸"),
    "handwrite": ("写信", "手写", "纸", "日记", "字迹", "信封"),
    "retro": ("从前", "老照片", "旧", "年代", "收音机", "磁带", "岁月"),
}

# 背景很暗时适合发光/书法一类；很亮时用简约深色更清楚
DARK_BACKGROUND_STYLES = ("guofeng", "handwrite", "rainy")
BRIGHT_BACKGROUND_STYLES = ("simple", "mv")


def animation_cache_dir(explicit=None):
    """歌词动效资源的缓存目录。"""
    if explicit:
        return Path(explicit)
    local = os.environ.get("LOCALAPPDATA") or os.environ.get("XDG_CACHE_HOME")
    if not local:
        return None
    return Path(local) / "JianyingPro" / "User Data" / "Cache" / "artistEffect"


def local_asset_roots():
    """本机所有可能存放素材的缓存根。

    不同类型的素材散在不同位置：转场在 ``Cache/effect/``，画面特效与歌词动效在
    ``Cache/artistEffect/``，而**歌词模板依赖的字体**在
    ``Cache/lyra-cli/material-cache/font/<id>/`` —— 只查 artistEffect 会把
    字体缺失的模板误判成可用，选出来才发现字形回退成了系统默认字体。
    """
    base = Path(os.environ.get("LOCALAPPDATA", "")) / "JianyingPro" / "User Data" / "Cache"
    roots = []
    if not base.is_dir():
        return roots
    for folder in base.iterdir():
        if not folder.is_dir():
            continue
        roots.append(folder)
        material_cache = folder / "material-cache"
        if material_cache.is_dir():
            roots.extend(child for child in material_cache.iterdir() if child.is_dir())
    return roots


def asset_is_local(resource_id):
    """该素材 id 在本机任意缓存根下有没有目录。"""
    if not resource_id:
        return False
    return any((root / str(resource_id)).is_dir() for root in local_asset_roots())


def animation_dependencies_ready(style_path, cache_dir=None):
    """该动效依赖的素材（字体等）是否都已在本机缓存里。

    套动效时官方会去下载缺失依赖，而 lyra-cli 的沙箱没有网络——缺一个就整条失败
    （实测缺字体时报 ``failed to download ... meta_type: font``）。更隐蔽的是：
    即使下载"成功"了也可能只留下一个 ``font.lock`` 空壳，渲染时回退成系统默认
    字体，看起来就是"字很丑"。所以挑动效时必须先把依赖不全的剔掉。
    """
    root = animation_cache_dir(cache_dir)
    if not style_path:
        return True
    try:
        data = json.loads(Path(style_path).read_text(encoding="utf-8", errors="replace"))
    except (OSError, ValueError):
        return True
    needed = set()

    def walk(node):
        """收集所有资源 id。

        注意：LyricStyle.json 里的依赖**不一定**写成 ``font_id: "..."``，
        实测常见形式是裸的 id 数组（``["7340606325656654345", ...]``）。
        早前只认键名，导致依赖缺失的模板被误判成可用。
        """
        if isinstance(node, dict):
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)
        elif isinstance(node, str) and node.isdigit() and len(node) >= 15:
            needed.add(node)

    walk(data)
    # 自身所在的 artistEffect 目录也要能查到（不带 manifest 时兜底）
    for resource_id in needed:
        if asset_is_local(resource_id):
            continue
        if root and (root / resource_id).is_dir():
            continue
        return False
    return True


def animation_catalog(cache_dir=None):
    """列出本机可用的歌词动效：``[{"id", "title", "style"}]``。"""
    root = animation_cache_dir(cache_dir)
    if not root or not root.is_dir():
        return []
    items = []
    for folder in sorted(root.iterdir()):
        if not folder.is_dir():
            continue
        styles = list(folder.rglob("LyricStyle.json"))
        if not styles:
            continue
        title = None
        try:
            style = json.loads(styles[0].read_text(encoding="utf-8", errors="replace"))
            title = style.get("title")
        except (OSError, ValueError):
            continue
        items.append({"id": folder.name, "title": title or "", "style": str(styles[0])})
    return items


# 贴纸池：名称关键词 -> 情绪/用途标签。
# 贴纸本体在剪映缓存里没有名字（名字在服务器上），但**任何被用过的贴纸**都会把
# name + resource_id 写进草稿，所以可以扫草稿攒出一本"名称 -> 资源id"的词典
# （见 scan_sticker_names.py）。官方素材搜索在当前 lyra-cli 里未开放网络，用不了。
STICKER_STYLE_WORDS = {
    "plead": ("求求你", "求求了", "拜托", "求你"),
    "cry": ("哭", "流泪", "哽咽", "委屈", "悲伤", "哽咽"),
    "hype": ("破防", "装逼", "沙雕", "搞笑", "二哈", "狗头", "舔舌头"),
    "agree": ("达成共识", "入股", "宝藏", "不亏", "认同", "心满意足"),
    "calm": ("开会", "勿扰", "跪下", "我很好", "摸摸头", "强颜欢笑", "苦恼"),
    "funny": ("蜡笔小新", "小熊", "歪嘴", "汤姆猫", "杰瑞"),
    "festive": ("新年", "边框", "节日"),
}

# 某句话术透出这种情绪时，就配对应气质的贴纸
SCRIPT_STYLE_WORDS = {
    "plead": ("别划走", "留下", "求", "帮忙", "看看", "划走"),
    "cry": ("哭", "泪", "心酸", "难过", "遗憾", "心疼", "苦", "等"),
    "hype": ("炸", "燃", "破防", "离谱", "绝了", "居然", "竟然"),
    "agree": ("入股", "收藏", "关注", "句号", "认同", "听懂", "点赞"),
    "calm": ("其实", "只是", "认为", "从未", "没有", "本来"),
}


def _norm(text):
    return str(text or "")


def score_script_styles(line):
    """按一句话术的措辞判断它想要什么情绪的贴纸。"""
    body = _norm(line)
    return {style: sum(body.count(word) for word in words)
            for style, words in SCRIPT_STYLE_WORDS.items()}


def sticker_pool(cache_dir=None, name_map=None):
    """本地可用（有图）的贴纸清单：``[{"id","name","path","styles"}]``。

    ``name_map`` 是 ``{资源id: 名称}``，通常来自扫描剪映草稿得到的结果；
    只有既知道名字、本地又有图片实体的贴纸才算可用。
    """
    catalog = animation_catalog(cache_dir) or []
    images = {}
    root = animation_cache_dir(cache_dir)
    if not root or not root.is_dir():
        return []
    for folder in root.iterdir():
        if not folder.is_dir():
            continue
        pics = list(folder.rglob("singleImage.png"))
        if pics:
            # 模板里贴纸素材的 path 指向资源目录（而非 png 文件本身），保持一致
            images[folder.name] = str(pics[0].parent)
    del catalog  # 只借用目录扫描能力
    pool = []
    for resource_id, name in (name_map or {}).items():
        path = images.get(str(resource_id))
        if not path:
            continue
        styles = [style for style, words in STICKER_STYLE_WORDS.items()
                  if any(word in name for word in words)]
        pool.append({"id": str(resource_id), "name": name, "path": path,
                     "pixels": sticker_pixels(path),
                     "styles": styles or ["funny"]})
    return pool


def pick_stickers(lines, name_map=None, cache_dir=None, slots=None):
    """给每一句片头话术挑一个贴纸，尽量不重复。

    ``slots`` 是每个片头贴纸**位**的原素材像素尺寸。模板里各贴纸尺寸并不相同，
    而 ``clip.scale`` 是按各自素材调的，换成尺寸差很多的贴纸会出现大小突变，
    所以优先在同一档像素的候选里挑；找不到再放宽。

    返回 ``[{"id","name","path","pixels","why"}, ...]``；池子不可用时返回空列表，
    调用方保持模板原贴纸。
    """
    pool = sticker_pool(cache_dir=cache_dir, name_map=name_map)
    if not pool or not lines:
        return []
    used = set()
    picks = []
    for index, line in enumerate(lines):
        candidates = list(pool)
        scores = score_script_styles(line)
        ranked = sorted(scores.items(), key=lambda pair: pair[1], reverse=True)
        chosen, why = None, "neutral"
        for style, score in ranked:
            if score <= 0:
                break
            for item in candidates:
                if style in item["styles"] and item["id"] not in used:
                    chosen, why = item, "%s(%d)" % (style, int(score))
                    break
            if chosen:
                break
        if chosen is None:
            # 兜底也别用"新年边框"这类节日限定贴纸，先挑通用卡通
            for item in candidates:
                if item["id"] not in used and "festive" not in item["styles"]:
                    chosen, why = item, "rotate"
                    break
        if chosen is None:
            for item in candidates:
                if item["id"] not in used:
                    chosen, why = item, "rotate"
                    break
        if chosen is None:
            chosen, why = candidates[0], "reuse"
        used.add(chosen["id"])
        picks.append({"id": chosen["id"], "name": chosen["name"],
                      "path": chosen["path"], "pixels": chosen.get("pixels"),
                      "why": why})
    return picks


# 与模板"开会"那张对齐的基准：它在本机显示大小正常（居中、不压字幕）。
# 所有选中的贴纸都统一成这个画布尺寸与缩放，避免各位 scale 与素材尺寸耦合出错。
STICKER_CANVAS = 240
STICKER_SCALE = 0.5755
STICKER_OFFSET_Y = 0.42

# 歌词模板的"存在感"判据（本机模板实测）：字号 ≥ 16 且不是分散布局。
# 用户明确要求"歌词模板要选中间显眼的"——12 号小字加分散布局基本看不见。
PROMINENT_MIN_FONT_SIZE = 16
SCATTERED_LAYOUT_TOKENS = ("spread", "scatter")


def sticker_pixels(path):
    """贴纸素材的原始像素尺寸。

    优先读图片本身的真实像素——``heycanInfo.json`` 里声明的尺寸未必和图片一致，
    用它判断"尺寸是否接近"会误判，换上去大小就失控了。读图失败才回退声明值。
    """
    folder = Path(path)
    image = folder / "singleImage.png"
    if image.is_file():
        try:
            from PIL import Image

            with Image.open(image) as art:
                return (art.width, art.height)
        except Exception:  # noqa: BLE001 - 回退到声明尺寸
            pass
    info = folder / "heycanInfo.json"
    if not info.is_file():
        return None
    try:
        data = json.loads(info.read_text(encoding="utf-8", errors="replace"))
        width = int(data.get("singleWidth") or 0)
        height = int(data.get("singleHeight") or 0)
    except (OSError, ValueError, TypeError):
        return None
    return (width, height) if width and height else None


def prepare_sticker_images(picks, out_dir):
    """把挑中的贴纸统一成与原贴纸相同的画布尺寸。

    贴纸段里的 ``clip.scale`` 是按模板原贴纸（240x240）定死的；直接换成别的尺寸
    （缓存里有 84x78 这类小图）会被拉伸到同样比例——又糊又铺满屏。
    这里统一居中缩放到 240x240，每个贴纸放一个独立目录，保持与剪映缓存同构
    （素材 path 指向目录，目录里是 singleImage.png）。
    """
    from PIL import Image
    import shutil as _shutil

    root = Path(out_dir) / "stickers"
    prepared = []
    for index, item in enumerate(picks):
        source_dir = Path(item["path"])
        source = source_dir / "singleImage.png"
        if not source.is_file():
            prepared.append(item)
            continue
        target_dir = root / ("sticker-%02d" % (index + 1))
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / "singleImage.png"
        try:
            with Image.open(source) as art:
                art = art.convert("RGBA")
                art.thumbnail((STICKER_CANVAS, STICKER_CANVAS))
                canvas = Image.new("RGBA", (STICKER_CANVAS, STICKER_CANVAS), (0, 0, 0, 0))
                canvas.paste(art, ((STICKER_CANVAS - art.width) // 2,
                                   (STICKER_CANVAS - art.height) // 2), art)
                canvas.save(target)
        except Exception:  # noqa: BLE001 - 单张失败就沿用原路径
            prepared.append(item)
            continue
        # 贴纸资源目录必须带效果定义，缺了引擎会直接丢弃整张贴纸：
        # config.json 描述效果链接、infoSticker.lua 指向图片、heycanInfo 记尺寸。
        for meta in ("config.json", "infoSticker.lua", "heycanInfo.json"):
            origin = source_dir / meta
            if origin.is_file():
                _shutil.copyfile(origin, target_dir / meta)
        info = target_dir / "heycanInfo.json"
        if info.is_file():
            try:
                data = json.loads(info.read_text(encoding="utf-8", errors="replace"))
                data.update({"singleWidth": STICKER_CANVAS, "singleHeight": STICKER_CANVAS,
                             "bigWidth": STICKER_CANVAS, "bigHeight": STICKER_CANVAS})
                info.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            except (OSError, ValueError):
                pass
        prepared.append(dict(item, path=str(target_dir)))
    return prepared


def load_sticker_names(path=None):
    """读取贴纸名称词典（skill 自带的 ``references/sticker-names.json``）。

    这本词典是扫描本机剪映草稿攒出来的：贴纸在素材缓存里没有名字，
    但被用过的贴纸都会把 name + resource_id 写进草稿。
    """
    target = Path(path) if path else (Path(__file__).resolve().parent.parent
                                      / "references" / "sticker-names.json")
    if not target.is_file():
        return {}
    try:
        return json.loads(target.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def background_tone(path):
    """粗略判断背景图的明暗与色温（用于挑字幕配色气质）。"""
    from shutil import which

    tool = which("ffmpeg")
    if not tool or not path:
        return None
    done = subprocess.run([tool, "-v", "error", "-i", str(path), "-vf", "scale=1:1",
                           "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                          capture_output=True)
    if done.returncode != 0 or len(done.stdout) < 3:
        return None
    red, green, blue = done.stdout[0], done.stdout[1], done.stdout[2]
    return {"r": int(red), "g": int(green), "b": int(blue),
            "luma": 0.299 * red + 0.587 * green + 0.114 * blue}


def score_lyric_styles(text):
    """统计歌词内容在各气质上的倾向。"""
    body = str(text)
    return {style: sum(body.count(word) for word in words)
            for style, words in LYRIC_STYLE_WORDS.items()}


# 资源池里的**真实名称**关键词 -> 气质。这些名字是扫草稿挖出来的，
# 有语义（"雨雾氛围感""红白书法""文艺抒情歌"），比 LyricStyle.json 里的
# title（一堆 layout_spread）有用得多。
ANIMATION_NAME_STYLES = {
    "guofeng": ("书法", "国风", "古风", "红白"),
    "rainy": ("雨雾", "抒情", "氛围", "慢调"),
    "sweet": ("粉笺", "心语", "春日", "甜"),
    "rock": ("摇滚", "节奏", "弹动"),
    "handwrite": ("手写",),
    "retro": ("黑胶", "复古"),
    "simple": ("文字拆分", "高级感", "逐字渐显", "政企", "情怀"),
    "mv": ("浪漫氛围", "长句", "emoji"),
}

EFFECT_POOL_PATH = (Path(__file__).resolve().parent.parent
                    / "references" / "effect-pool.json")


def effect_pool(pool_path=None):
    """读取 skill 自带的官方效果资源池（挖自本机草稿，均为本地有实体的）。"""
    target = Path(pool_path) if pool_path else EFFECT_POOL_PATH
    if not target.is_file():
        return {}
    try:
        return json.loads(target.read_text(encoding="utf-8", errors="replace"))
    except (OSError, ValueError):
        return {}


def animation_prominence(style_path):
    """歌词模板在画面中间够不够显眼。

    返回 ``(是否显眼, 字号, 布局名)``。判据来自本机模板实测：

    - 字号取 ``LyricStyle.json`` 的 ``text_style.font_size``。实测 12 号这类小字
      配上分散布局，歌词会被摊到画面边缘、中间空一片，观众**几乎注意不到**；
      18–30 号的居中大字才有存在感。
    - ``layout_spread`` / ``Scatter`` 这类**分散布局**即使字号不小也会把字打散，
      同样判为不显眼。

    这一条是用户明确提过的要求："歌词模板要选中间显眼的"。
    """
    try:
        data = json.loads(Path(style_path).read_text(encoding="utf-8", errors="replace"))
    except (OSError, ValueError, TypeError):
        return True, None, ""
    style = data.get("text_style") or {}
    try:
        size = int(style.get("font_size"))
    except (TypeError, ValueError):
        size = None
    title = str(data.get("title") or "")
    scattered = any(token in title.lower() for token in SCATTERED_LAYOUT_TOKENS)
    prominent = (not scattered) and (size is None or size >= PROMINENT_MIN_FONT_SIZE)
    return prominent, size, title


def search_online_templates(prompt, limit=10, project=None, timeout=180):
    """在剪映官方素材库里搜歌词模板。

    **歌词模板的正路是官方在线素材库**：按意境能搜到几十种（大字、抒情、手写、
    复古…），而本机 ``Cache/artistEffect`` 只有"历史上被使用过"的那几个残留，
    既不能代表可选范围，也常常正好是小字分散布局。只用本地缓存挑模板，会一边
    抱怨"没得选"、一边错过素材库里更合适的东西。

    返回 ``[{"id", "title", "vip"}, ...]``；失败保留具体错误并停止，
    不允许自动改用本地清单。
    """
    if not prompt:
        return []
    project = Path(project or Path.cwd()).resolve()
    from official_materials import execute
    result = execute(project, ["material", "search", "--type", "lyric_animation",
                               "--prompt", str(prompt), "--limit", str(limit)])
    if "envelope" not in result:
        raise RuntimeError("官方歌词模板搜索失败：" + str(result.get("error") or result.get("status")))
    items = (((result.get("envelope") or {}).get("result") or {})
             .get("result") or {}).get("items") or []
    return [{"id": str(item.get("resource_id")), "title": str(item.get("title") or ""),
             "vip": bool(item.get("is_vip"))} for item in items if item.get("resource_id")]


def pick_animation(text, background=None, cache_dir=None, pool_path=None, project=None):
    """仅从官方在线结果选模板并下载；不以本地字体库存过滤候选。

    返回候选资源和选择依据。居中、显眼和不溢出仍须套用后抽帧验证，
    不能用名称、字号或下载成功代替视觉验收。
    """
    from official_materials import execute
    project = Path(project or Path.cwd()).resolve()
    scores = score_lyric_styles(text)
    hints = {
        "guofeng": ("国风", "书法", "古风"),
        "rainy": ("雨雾", "雨滴", "抒情", "文艺"),
        "sweet": ("温柔", "小情歌", "粉", "甜"),
        "rock": ("摇滚", "节奏", "粗体"),
        "handwrite": ("手写", "留痕"),
        "retro": ("复古", "文艺", "胶片"),
    }
    ranked_styles = sorted(scores.items(), key=lambda row: row[1], reverse=True)
    top = next((style for style, score in ranked_styles if score > 0 and style in hints), "rainy")
    terms = hints[top]
    prompts = [terms[0] + " 歌词", "居中 清晰 抒情 歌词"]
    candidates = {}
    for prompt in prompts:
        for item in search_online_templates(prompt, limit=12, project=project):
            candidates.setdefault(item["id"], item)
    if not candidates:
        raise RuntimeError("官方在线搜索没有可选歌词模板；停止，不自动改用本地素材")
    def relevance(item):
        name = item["title"]
        fit = sum((len(terms)-index) * 10 for index, word in enumerate(terms) if word in name)
        return fit + (2 if any(word in name for word in ("居中", "清晰", "大字")) else 0)
    chosen = max(candidates.values(), key=relevance)
    result = execute(project, ["material", "download", "--type", "lyric_animation",
                               "--resource-id", chosen["id"]])
    if "envelope" not in result:
        raise RuntimeError("官方歌词模板下载失败，停止：" + str(result.get("error") or result.get("status")))
    return chosen["id"], "官方在线:%s->%s（已下载，待套用与视觉验收）" % (top, chosen["title"])
