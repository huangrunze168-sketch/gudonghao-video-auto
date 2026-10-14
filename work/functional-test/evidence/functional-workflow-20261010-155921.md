# lyra-cli 真实功能测试报告

- 清单命令数：195

## 工作流层

| 步骤 | 状态 | exit | 工程变化 | 说明 |
| --- | --- | --- | --- | --- |
| 01 建工程 | ✅ 成功 | 0 | False | 官方只在草稿根下识别工程 |
| 02 加主视频 | ⚠️ 官方参数/用法拒绝 | 2 | False | 真实 mp4 入轨 |
| 03 加画中画 | ⚠️ 官方参数/用法拒绝 | 2 | False | 同轨第二段 |
| 04 加文字 | ✅ 成功 | 0 | False | success |
| 05 加音频 | ✅ 成功 | 0 | False | success |
| 06 导出结构 | ✅ 成功 | 0 | False | success |
| 07 视频变速 | ➡️ 需真实前置产物 | 2 | False | gen_patch: invalid action: draft video speed target 4BB5AB0C-401F-4BE2-83D3-0D29 |
| 08 视频裁剪 | ➡️ 需真实前置产物 | 2 | False | gen_patch: invalid action: draft video crop target 4BB5AB0C-401F-4BE2-83D3-0D297 |
| 09 视频调色 | ➡️ 需真实前置产物 | 2 | False | gen_patch: invalid action: draft video adjust target 4BB5AB0C-401F-4BE2-83D3-0D2 |
| 10 加关键帧 | ⚠️ 官方参数/用法拒绝 | 2 | False | 官方 REQUIRED --points |
| 11 撤销 | 🚧 仅内嵌库支持 | 2 | False | 官方：standalone 版不支持，验证报错文案 |
| 12 重做 | 🚧 仅内嵌库支持 | 2 | False | draft history undo / redo is only available when lyra-cli is embedded as a clien |
| 13 加字幕条 | ✅ 成功 | 0 | False | success |
| 14 加滤镜 | ➡️ 需真实前置产物 | 2 | False | 需要真实滤镜资源 id |
| 15 导出模板包 | ✅ 成功 | 0 | False | 真实产出模板压缩包 |
| 16 最终结构 | ✅ 成功 | 0 | False | success |
