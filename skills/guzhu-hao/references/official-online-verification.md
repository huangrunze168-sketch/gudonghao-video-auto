# 官方在线能力：当前实测证据

## 已成功

运行环境：剪映运行、官方授权宿主、ASCII 临时工作区仅授予该目录读写、显式联网开关。

- `material search --type sticker --prompt 悲伤 --limit 3`：`err_code=0`，返回 3 条在线素材。
- `material download --type sticker --resource-id 7617494741940440344 --resource-dir <ASCII输出>`：`err_code=0`，落地 singleImage.png（16230 字节）、config.json、infoSticker.lua、heycanInfo.json。
- `material search --type font --prompt 手写 --limit 3`：`err_code=0`，返回松弛感、字由物语、字由热烈体，包含 ID、下载地址和会员标记。
- `material download --type font --resource-id 7588070438018796863 --resource-dir <ASCII输出>`：`err_code=0`，落地 font.ttf（7464428 字节）及 config.json。

对应字体搜索和下载的完整证据位于系统 ASCII 临时工作区 jy-online 下的 evidence.json。不得将成功的一个资源推广为全部模板已解禁。

## 尚未成功

字体 `7340606325656654345`：官方返回 upstream `-100202`，resource_pool `-7002`，下载错误 `-1008`，`cannot unzip file`，`from_net=1`。目标目录只有 0 字节 lock，没有字体实体。其他字体成功表明不能再把此资源失败归因为“全域禁网”。仍需验证该字体的服务端包及官方恢复路径。

13 个歌词模板没有完成逐项套用及渲染验证；先前“全因缺字体、全部可解禁”结论无依据。

## 官方模板字体批量验证

读取 13 个现有官方 LyricStyle.json 的明确 font_id 字段（含数组），去重得到 38 个字体 ID。官方下载核验：27 个产生非空字体实体，11 个失败。字体清单全部成功的模板包括文字拆分（2/2）、红白书法（3/3）、浪漫氛围（1/1）、粉笺心语（1/1）、续写情怀（2/2）。这不代表其他依赖、套用及渲染验收通过。

完整记录：工作区 work/guzhu-test/font-verification.json。未修改现有成片草稿。失败的默陌专辑手写体资源包 HTTP 200、标准 ZIP、哈希与官方一致；包内字体名称编码异常，授予单次 TEMP 读写后官方解压仍失败，根因尚未最终确定。

## 结论边界

ASCII 可写工作区下搜索与下载已成功，不能据此断言原先所有 exitCode 5 的唯一根因就是中文路径。SDK net_counts 为网络规则/使用指标，非请求成功证明；业务以完整返回和真实文件为准。

旧资源池仅作为历史 ID 线索，旧 cli-status.json 的 usable 为参数探测兜底，不是实际可用性矩阵。
