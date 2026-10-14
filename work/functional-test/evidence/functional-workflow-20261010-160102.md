# lyra-cli 真实功能测试报告

- 清单命令数：195

## 工作流层

| 步骤 | 状态 | exit | 工程变化 | 说明 |
| --- | --- | --- | --- | --- |
| 01 建工程 | ✅ 成功 | 0 | False | 官方只在草稿根下识别工程 |
| 02 加主视频 | ✅ 成功 | 0 | True | 真实 mp4 入轨（--track 官方要求整数轨道号） |
| 03 加画中画 | ✅ 成功 | 0 | True | 同轨第二段 |
| 04 加文字 | ✅ 成功 | 0 | True | success |
| 05 加音频 | ✅ 成功 | 0 | True | success |
| 06 导出结构 | ✅ 成功 | 0 | False | success |
| 07 视频变速 | ✅ 成功 | 0 | True | success |
| 08 视频裁剪 | ✅ 成功 | 0 | True | success |
| 09 视频调色 | ✅ 成功 | 0 | True | success |
| 10 加关键帧 | ⚠️ 官方参数/用法拒绝 | 2 | False | 官方只接受 position-x/scale/opacity 等属性名，--points 为 REQUIRED |
| 11 撤销 | 🚧 仅内嵌库支持 | 2 | False | 官方：standalone 版不支持，验证报错文案 |
| 12 重做 | 🚧 仅内嵌库支持 | 2 | False | draft history undo / redo is only available when lyra-cli is embedded as a clien |
| 13 加字幕条 | ✅ 成功 | 0 | True | success |
| 14 加滤镜 | ✅ 成功 | 0 | True | 需要真实滤镜资源 id |
| 15 导出模板包 | ⚠️ 官方业务拒绝 | 1 | False | 真实产出模板压缩包 |
| 16 最终结构 | ✅ 成功 | 0 | False | success |
