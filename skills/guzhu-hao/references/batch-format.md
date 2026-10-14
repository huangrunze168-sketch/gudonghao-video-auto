# 批次清单格式

清单是一个 UTF-8 JSON 文件；所有相对路径都按**清单文件所在目录**解析。

```json
{
  "template": "C:/path/股东号模板.jypack",
  "out": "C:/path/work/guzhu-batch-1",
  "media": { "solid_color": "black" },
  "intro": {
    "lines": ["家人们别划走", "主播认为家产从未易主", "一个句号就是入股"],
    "tts": { "mode": "sapi", "voice": "Microsoft Huihui Desktop", "rate": 2, "gap_ms": 0 }
  },
  "render": { "width": 1280, "height": 720, "fps": 30, "bitrate": 6000000, "timeout": 900 },
  "songs": [
    { "name": "问春风", "file": "D:/songs/问春风.mp3", "lyrics": "D:/songs/问春风.lrc", "start": "auto" },
    { "name": "晚风",   "file": "D:/songs/晚风.mp3",   "lyrics": "D:/songs/晚风.lrc",   "start": 95.5 }
  ]
}
```

## 顶层字段

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `template` | 是 | 股东号模板 `.jypack` |
| `out` | 否 | 输出目录；省略时为 `work/guzhu-<时间戳>` |
| `intro` | 是 | 引流话术与配音设置 |
| `media` | 否 | `solid_color`：不可读图片的替代色，默认 `black` |
| `render` | 否 | 导出参数 |
| `songs` | 是 | 歌曲数组，至少一首 |

## `intro`

| 字段 | 说明 |
| --- | --- |
| `lines` | 话术文本数组，一句一组。**条数不得超过模板的引流组数**（`check` 会显示，模板通常 5 组） |
| `file` | 话术文本文件（一行一句，`#` 开头为注释）；与 `lines` 二选一 |
| `tts.mode` | `official`（默认，剪映官方音色，与模板同源）/ `sapi`（本机离线合成）/ `files`（自备音频） |
| `tts.speaker` | `official` 模式的官方音色 id；留空自动沿用模板 TTS 素材的 `tone_speaker` |
| `tts.timeout` | `official` 模式单句合成的超时秒数，默认 `900` |
| `tts.voice` | `sapi` 模式的音色名。留空自动选第一个中文音色；用 `voices` 子命令列出全部可用音色 |
| `tts.rate` | `sapi` 模式语速 `-10..10`，默认 `0`；`2` 接近短视频口播节奏 |
| `tts.files` | `mode=files` 时按顺序对应 `lines` 的音频文件数组 |
| `tts.gap_ms` | 每句话术尾部附加静音毫秒，默认 `0`（组与组首尾相接） |

### `mode: "official"` 的前置与边界

需要：剪映主进程在运行、账号已登录、可以联网。前置自检：

```powershell
python engine\draftediting_runtime.py doctor   # 官方 VMSDK 与 Bun 副本
python tools\lyra_login.py --status            # 登录态
```

- 合成会走剪映官方 TTS 服务并**消耗账号权益**（本机实测为 VIP 账号）。
- 官方命令**不改字幕文本**（`--text` 只用于合成），也**不重排时间线**；
  本 Skill 因此只取回音频，字幕改写与整条时间线重排仍由自己的离线逻辑完成。
- 临时草稿与官方工作区都使用纯 ASCII 路径——官方沙箱遇到非 ASCII 路径会直接崩溃。

配音在合成后会**自动去掉首尾静音**，否则留白会把片头拖长、节奏变慢。

片头总时长 = 各句配音时长之和。这个值决定主歌从哪里开始，**整条时间线会随之自动重排**
（贴纸、字幕、主歌、歌词一起平移）。

## `songs[]`

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `name` | 否 | 视频名与草稿名，默认取音频文件名 |
| `file` | 是 | 歌曲文件，支持 wav/mp3/m4a/aac/flac/ogg/wma |
| `lyrics` | 否 | 歌词文件，`.lrc`（时间精确）或纯文本（主歌段内按行均分） |
| `start` | 否 | 选段起点。`"auto"`/省略=自动；秒数如 `95.5`；或 `"2:05"` |
| `min_lead_ms` | 否 | 自动选段时避开歌曲开头的最小毫秒，默认 `5000` |

## `lyrics`（可选）

| 字段 | 说明 |
| --- | --- |
| `engine` | `official`（默认，走剪映 CLI：官方识别 + 官方歌词动效）/ `off`（不生成歌词） |
| `animation` | 官方歌词动效资源。默认 `"auto"`：按**歌词内容 + 背景明暗**自动挑。也可写死某个资源 id（必须是 **`lyric_animation`** 类；传 `subtitle_template` 会报 `failed to read LyricStyle.json`） |
| `language` | 歌词识别语言，默认 `zh` |
| `animation_language` | 动效语言，默认 `zh-CN` |
| `recognize_timeout` | 识别超时秒数，默认 `1800` |

`animation: "auto"` 会在本机剪映缓存（`User Data/Cache/artistEffect`，实测 62 个）里
找歌词动效，用标题判断气质、结合歌词关键词与背景明暗挑选，例如：

| 歌词气质 | 选中的动效 |
| --- | --- |
| 古风战歌（金戈铁马、孤烟大漠…） | `ChineseCalligraphy`（毛笔书法） |
| 雨夜伤感（雨、泪、思念…） | `雨雾渐显` |
| 甜系（喜欢、拥抱、阳光…） | `lovely_pink` |

报告里会记录 `animation_pick`（选了哪个、依据什么）。

`engine: "official"` 时歌词**默认由官方识别**：
`blueprint sync` 定位主歌音乐段 → `lyrics recognize --mode segment` 只识别主歌段
→ 官方写成不带 template 的 `<text>` 段 → `lyrics animation update` 套官方动效
→ 同步镜像 → 原生渲染。实测成片带官方歌词动效出字。

**要精确文本就提供 `songs[].lyrics`**：脚本会在识别之后、套动效之前，用你的歌词行替换
识别文本（按顺序单调对齐，官方时间轴保留）；官方识别的分句比歌词行粗时，
**会把"一段含多行"拆成一行一段**，各段时间按行内字数占比切分，
避免两行共用一条时间轴导致逐词动效与演唱错位。

该模式要求剪映运行中 + 账号已登录 + 联网，会消耗账号权益；草稿目录名由脚本生成为
纯 ASCII（官方沙箱遇非 ASCII 路径会崩溃）。

`songs[].lyrics` 只有在 `engine` 非 `official` 时才作为字幕文本来源使用。

### 自动选段规则

1. 若提供了 `.lrc`：先按歌词行时间生成候选窗口，**优先选歌词行足够多（≥3 句）且能量较高**的窗口——
   避免自动落到没有歌词的间奏上。
2. 否则/都不满足时：用能量包络找平均能量最高的窗口（通常就是副歌）。

报告里的 `start_pick` 会写明依据，例如 `lyrics+energy(10 句歌词)` 或 `energy`。

### 手动指定起点

`start` 会与 LRC 交叉校验：**若该窗口内没有任何歌词行，直接报错**，不生成没有歌词的成片。
若确实要用间奏或纯音乐段，请不要提供 `lyrics`（或改用手写歌词文件）。

## `render`

| 字段 | 默认 | 说明 |
| --- | --- | --- |
| `width` / `height` | 沿用模板画布 | 输出分辨率。只改分辨率不会重排画面布局 |
| `fps` | `30` | 帧率 |
| `bitrate` | `6000000` | 视频码率 |
| `timeout` | `900` | 单条渲染超时秒数 |

## 输出目录结构

```
<out>/
├── report.json               全批次状态、选段依据、成片规格与哈希
├── tts/                      话术配音（含 tts.json 缓存键）
├── songs/<歌名>.wav          按选段裁好的歌曲音频
├── repair/                   替换不可读图片时生成的纯色图
├── jypack/<歌名>.jypack      可直接在剪映打开的成品草稿
└── render/<歌名>/
    ├── render.mp4            成品
    ├── result.json           渲染证据（时长、帧数、哈希）
    └── ffprobe.json
```

`tts/` 与 `songs/` 会复用：话术不变时不重复合成配音。改了 `intro.lines` 会自动重建配音缓存。
