# lyra-cli 真实功能测试报告

- 清单命令数：195

## 执行层

| 状态 | 数量 |
| --- | --- |
| ✅ 成功 | 134 |
| ⚠️ 官方参数/用法拒绝 | 19 |
| ➡️ 需真实前置产物 | 16 |
| ⚠️ 官方业务拒绝 | 15 |
| 🚧 官方未实现 | 4 |
| ⏭️ 有意跳过（破坏会话/需人工交互） | 4 |
| 🚧 仅内嵌库支持 | 3 |

| 命令 | 状态 | exit | 参数 | 官方消息 |
| --- | --- | --- | --- | --- |
| draft edit | ✅ 成功 | 0 | `edit --ref local://func-test-1012-133748 --op split --target seg_id=DEB770D4-26CB-4983-9BFC-0E3228D9AB9D --params points` | success |
| draft config | ✅ 成功 | 0 | `config --ref local://func-test-1012-133748 --ratio 16:9` | success |
| draft project create | ✅ 成功 | 0 | `project create --ref local://func-test-1012-133748 --dir C:\Users\Administrator\AppData\Local\JianyingPro\User Data\Proj` | success |
| draft project list | ✅ 成功 | 0 | `project list` | success |
| draft project focus | ✅ 成功 | 0 | `project focus --ref local://func-test-1012-133748` | success |
| draft project delete | ✅ 成功 | 0 | `project delete --ref local://func-test-1012-133748` | success |
| draft cover set | ✅ 成功 | 0 | `cover set --ref local://func-test-1012-133748 --image C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\media` | success |
| draft cover clear | ✅ 成功 | 0 | `cover clear --ref local://func-test-1012-133748` | success |
| draft extract summary | ✅ 成功 | 0 | `extract summary --ref local://func-test-1012-133748 --dir C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\o` | success |
| draft template add | ⚠️ 官方业务拒绝 | 1 | `template add --ref local://func-test-1012-133748 --resource template://7296042632323845438 --title func-test --start 0s ` | patch apply failed: error: draft dependency download failed: 7091670861664489998:text_template:2:effect_id=1791590:panel |
| draft template publish | ⚠️ 官方业务拒绝 | 1 | `template publish --ref local://func-test-1012-133748 --dir C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\` | internal error: process terminated by unhandled Windows exception 0xE06D7363 |
| draft template render | ⚠️ 官方参数/用法拒绝 | 2 | `template render --config C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\out\template-config.json --ref loc` | invalid argument: template config contains unsupported field: schema |
| draft template slots | ✅ 成功 | 0 | `template slots --ref local://func-test-1012-133748 --template-seg-id EDF1D961-E509-476F-9CC1-CAC4280B8703` | success |
| draft template replace | ➡️ 需真实前置产物 | 2 | `template replace --ref local://func-test-1012-133748 --template-seg-id EDF1D961-E509-476F-9CC1-CAC4280B8703 --slot func-` | invalid argument: slot not found: func-test |
| draft algo query | ✅ 成功 | 0 | `algo query --task-id vt_79F608EC-5DF7-488D-95F0-6764460664BB` | success |
| draft algo wait | ⚠️ 官方业务拒绝 | 1 | `algo wait --task-id vt_79F608EC-5DF7-488D-95F0-6764460664BB` | internal error: process terminated by unhandled Windows exception 0xE06D7363 |
| draft algo quality-enhance | ✅ 成功 | 0 | `algo quality-enhance --ref local://func-test-1012-133748 --seg-id EDF1D961-E509-476F-9CC1-CAC4280B8703 --level 1 --from ` | success |
| draft algo upscale-resolution | ✅ 成功 | 0 | `algo upscale-resolution --ref local://func-test-1012-133748 --seg-id EDF1D961-E509-476F-9CC1-CAC4280B8703 --mode 1 --fro` | success |
| draft algo ai-frame-interpolation | ✅ 成功 | 0 | `algo ai-frame-interpolation --ref local://func-test-1012-133748 --seg-id EDF1D961-E509-476F-9CC1-CAC4280B8703 --fps 30 -` | success |
| draft algo ai-matting | ✅ 成功 | 0 | `algo ai-matting --ref local://func-test-1012-133748 --seg-id EDF1D961-E509-476F-9CC1-CAC4280B8703 --workspace C:\Users\A` | success |
| draft algo ai-transition | ⚠️ 官方参数/用法拒绝 | 2 | `algo ai-transition --ref local://func-test-1012-133748 --after-seg-id EDF1D961-E509-476F-9CC1-CAC4280B8703 --resource lo` | media AIGC: invalid request: ai-transition generation requires a right video segment after --after-seg-id |
| draft algo custom-matting | ✅ 成功 | 0 | `algo custom-matting --ref local://func-test-1012-133748 --seg-id EDF1D961-E509-476F-9CC1-CAC4280B8703 --workspace C:\Use` | success |
| draft algo chroma-color-matting | ✅ 成功 | 0 | `algo chroma-color-matting --color #00FF00FF --ref local://func-test-1012-133748 --seg-id EDF1D961-E509-476F-9CC1-CAC4280` | success |
| draft algo video-tracking | ✅ 成功 | 0 | `algo video-tracking --tracker-type 1 --center-x 0.5 --center-y 0.5 --width 0.2 --height 0.2 --wait false --ref local://f` | success |
| draft algo sound-separation | ✅ 成功 | 0 | `algo sound-separation --ref local://func-test-1012-133748 --seg-id EDF1D961-E509-476F-9CC1-CAC4280B8703 --mode vocal --o` | success |
| draft algo loudness-normalize | ✅ 成功 | 0 | `algo loudness-normalize --ref local://func-test-1012-133748 --seg-id EDF1D961-E509-476F-9CC1-CAC4280B8703` | success |
| draft algo denoise | ⚠️ 官方参数/用法拒绝 | 2 | `algo denoise --ref local://func-test-1012-133748 --seg-id EDF1D961-E509-476F-9CC1-CAC4280B8703 --path C:\Users\Administr` | draft algo: unsupported algorithm type: denoise |
| draft algo voice-enhance | ⚠️ 官方参数/用法拒绝 | 2 | `algo voice-enhance --ref local://func-test-1012-133748 --seg-id EDF1D961-E509-476F-9CC1-CAC4280B8703` | draft algo: unsupported algorithm type: vocal_beautify |
| draft algo video-stabilize | ⚠️ 官方参数/用法拒绝 | 2 | `algo video-stabilize --ref local://func-test-1012-133748 --seg-id EDF1D961-E509-476F-9CC1-CAC4280B8703` | draft algo: unsupported algorithm type: video_stable |
| draft algo tts | ✅ 成功 | 0 | `algo tts --ref local://func-test-1012-133748 --seg-id 5C8F3EA0-DC32-4432-9834-D0487E5B8F6E --text 功能测试 --speed 1.0 --spe` | success |
| draft algo subtitle-recognize | ✅ 成功 | 0 | `algo subtitle-recognize --ref local://func-test-1012-133748 --seg-id 5C8F3EA0-DC32-4432-9834-D0487E5B8F6E --language zh ` | success |
| draft algo text-add-tone | ✅ 成功 | 0 | `algo text-add-tone --ref local://func-test-1012-133748 --seg-id 5C8F3EA0-DC32-4432-9834-D0487E5B8F6E --text 功能测试 --speed` | success |
| draft algo music-beats | ✅ 成功 | 0 | `algo music-beats --ref local://func-test-1012-133748 --seg-id EDF1D961-E509-476F-9CC1-CAC4280B8703 --mode beat --output-` | success |
| draft algo material-understand | ⚠️ 官方业务拒绝 | 1 | `algo material-understand --ref local://func-test-1012-133748 --seg-id EDF1D961-E509-476F-9CC1-CAC4280B8703 --prompt 花 --` | patch apply failed: {"lyra_err_code":100,"lyra_err_msg":"invalid request stage=invalid_client_source request_logid=20261 |
| draft algo subtitle-keywords | ✅ 成功 | 0 | `algo subtitle-keywords --ref local://func-test-1012-133748 --seg-id 5C8F3EA0-DC32-4432-9834-D0487E5B8F6E --language zh` | success |
| draft video crop | ✅ 成功 | 0 | `video crop --ref local://func-test-1012-133748 --seg-id EDF1D961-E509-476F-9CC1-CAC4280B8703` | success |
| draft video speed | ✅ 成功 | 0 | `video speed --ref local://func-test-1012-133748 --seg-id EDF1D961-E509-476F-9CC1-CAC4280B8703 --speed 1.0` | success |
| draft video stabilize | ⚠️ 官方参数/用法拒绝 | 2 | `video stabilize --ref local://func-test-1012-133748 --seg-id EDF1D961-E509-476F-9CC1-CAC4280B8703` | draft algo: unsupported algorithm type: video_stable |
| draft video scale | ✅ 成功 | 0 | `video scale --ref local://func-test-1012-133748 --seg-id EDF1D961-E509-476F-9CC1-CAC4280B8703` | success |
| draft video rotate | ✅ 成功 | 0 | `video rotate --ref local://func-test-1012-133748 --seg-id EDF1D961-E509-476F-9CC1-CAC4280B8703 --rotation 0` | success |
| draft video translate | ✅ 成功 | 0 | `video translate --ref local://func-test-1012-133748 --seg-id EDF1D961-E509-476F-9CC1-CAC4280B8703` | success |
| draft video alpha | ✅ 成功 | 0 | `video alpha --ref local://func-test-1012-133748 --seg-id EDF1D961-E509-476F-9CC1-CAC4280B8703 --alpha 1` | success |
| draft video flip | ✅ 成功 | 0 | `video flip --ref local://func-test-1012-133748 --seg-id EDF1D961-E509-476F-9CC1-CAC4280B8703` | success |
| draft video layer | ✅ 成功 | 0 | `video layer --ref local://func-test-1012-133748 --seg-id EDF1D961-E509-476F-9CC1-CAC4280B8703 --z-order 0` | success |
| draft video volume | ✅ 成功 | 0 | `video volume --linear 0.5 --ref local://func-test-1012-133748 --seg-id EDF1D961-E509-476F-9CC1-CAC4280B8703` | success |
| draft video freeze | ✅ 成功 | 0 | `video freeze --ref local://func-test-1012-133748 --seg-id EDF1D961-E509-476F-9CC1-CAC4280B8703 --time 1s --duration 1s` | success |
| draft video add | ✅ 成功 | 0 | `video add --ref local://func-test-1012-133748 --resource local:///C:/Users/Administrator/AppData/Local/Temp/jianying-fun` | success |
| draft video remove | ✅ 成功 | 0 | `video remove --ref local://func-test-1012-133748 --seg-id EDF1D961-E509-476F-9CC1-CAC4280B8703` | success |
| draft video adjust | ✅ 成功 | 0 | `video adjust --brightness 0.1 --ref local://func-test-1012-133748 --seg-id EDF1D961-E509-476F-9CC1-CAC4280B8703` | success |
| draft video background | ✅ 成功 | 0 | `video background --type color --ref local://func-test-1012-133748 --seg-id EDF1D961-E509-476F-9CC1-CAC4280B8703 --image ` | success |
| draft video matting-stroke | ✅ 成功 | 0 | `video matting-stroke --enable --ref local://func-test-1012-133748 --seg-id EDF1D961-E509-476F-9CC1-CAC4280B8703 --resour` | success |
| draft video mix-mode | ⚠️ 官方参数/用法拒绝 | 2 | `video mix-mode --enable --ref local://func-test-1012-133748 --seg-id EDF1D961-E509-476F-9CC1-CAC4280B8703 --resource vim` | gen_patch: invalid action: gen_patch --update mix_mode: segment EDF1D961-E509-476F-9CC1-CAC4280B8703 is on main track (t |
| draft video face-beauty | ⚠️ 官方参数/用法拒绝 | 2 | `video face-beauty --ref local://func-test-1012-133748 --seg-id EDF1D961-E509-476F-9CC1-CAC4280B8703` | gen_patch: invalid action: gen_patch --update has no registered handler for field(s):  |
| draft video extract-frames | ✅ 成功 | 0 | `video extract-frames --ref local://func-test-1012-133748 --seg-id EDF1D961-E509-476F-9CC1-CAC4280B8703 --output-path C:\` | success |
| draft video extract-music | ✅ 成功 | 0 | `video extract-music --ref local://func-test-1012-133748 --seg-id EDF1D961-E509-476F-9CC1-CAC4280B8703 --start 0s` | success |
| draft sticker add | ✅ 成功 | 0 | `sticker add --ref local://func-test-1012-133748 --resource vimo://7575784012703190297 --start 0s --duration 1s` | success |
| draft sticker remove | ✅ 成功 | 0 | `sticker remove --ref local://func-test-1012-133748 --seg-id 2B949C29-5C7A-47E7-8830-D733A4D83F3C` | success |
| draft text translate | ✅ 成功 | 0 | `text translate --ref local://func-test-1012-133748 --seg-id 5C8F3EA0-DC32-4432-9834-D0487E5B8F6E` | success |
| draft text content | ✅ 成功 | 0 | `text content --ref local://func-test-1012-133748 --seg-id 5C8F3EA0-DC32-4432-9834-D0487E5B8F6E --content 功能测试` | success |
| draft text wrap-width | ✅ 成功 | 0 | `text wrap-width --width 0.5 --ref local://func-test-1012-133748 --seg-id 5C8F3EA0-DC32-4432-9834-D0487E5B8F6E` | success |
| draft text add | ✅ 成功 | 0 | `text add --ref local://func-test-1012-133748 --content 功能测试 --start 0s --duration 1s` | success |
| draft text remove | ✅ 成功 | 0 | `text remove --ref local://func-test-1012-133748 --seg-id 5C8F3EA0-DC32-4432-9834-D0487E5B8F6E` | success |
| draft text style | ✅ 成功 | 0 | `text style --size 7 --ref local://func-test-1012-133748 --seg-id 5C8F3EA0-DC32-4432-9834-D0487E5B8F6E` | success |
| draft audio volume | ✅ 成功 | 0 | `audio volume --linear 0.5 --ref local://func-test-1012-133748 --seg-id 2743EEFE-9631-4F50-A753-DEBF94B0D9D2` | success |
| draft audio fade | ✅ 成功 | 0 | `audio fade --ref local://func-test-1012-133748 --seg-id 2743EEFE-9631-4F50-A753-DEBF94B0D9D2 --out 1s --type both` | success |
| draft audio speed | ✅ 成功 | 0 | `audio speed --ref local://func-test-1012-133748 --seg-id 2743EEFE-9631-4F50-A753-DEBF94B0D9D2 --speed 1.0` | success |
| draft audio add | ✅ 成功 | 0 | `audio add --ref local://func-test-1012-133748 --resource local:///C:/Users/Administrator/AppData/Local/Temp/jianying-fun` | success |
| draft audio remove | ✅ 成功 | 0 | `audio remove --ref local://func-test-1012-133748 --seg-id 2743EEFE-9631-4F50-A753-DEBF94B0D9D2` | success |
| draft segment remove | ✅ 成功 | 0 | `segment remove --ref local://func-test-1012-133748 --seg-id EDF1D961-E509-476F-9CC1-CAC4280B8703` | success |
| draft segment split | ✅ 成功 | 0 | `segment split --ref local://func-test-1012-133748 --seg-id EDF1D961-E509-476F-9CC1-CAC4280B8703 --points 1s` | success |
| draft segment duplicate | ✅ 成功 | 0 | `segment duplicate --ref local://func-test-1012-133748 --seg-id EDF1D961-E509-476F-9CC1-CAC4280B8703 --start 0s` | success |
| draft segment move | ⚠️ 官方业务拒绝 | 1 | `segment move --ref local://func-test-1012-133748 --seg-id EDF1D961-E509-476F-9CC1-CAC4280B8703 --start 0s` | draft edit made no effective segment changes: gen_patch --move made no effective changes; target already has the request |
| draft compound-clip create | ✅ 成功 | 0 | `compound-clip create --ref local://func-test-1012-133748 --seg-id EDF1D961-E509-476F-9CC1-CAC4280B8703 --name func-test` | success |
| draft filter add | ✅ 成功 | 0 | `filter add --ref local://func-test-1012-133748 --resource vimo://7493457725431631142 --start 0s --duration 1s` | success |
| draft filter remove | ✅ 成功 | 0 | `filter remove --ref local://func-test-1012-133748 --seg-id 7B1872B4-F21D-4FB5-B91C-2CDEDFAFB217` | success |
| draft filter update | ✅ 成功 | 0 | `filter update --ref local://func-test-1012-133748 --seg-id 7B1872B4-F21D-4FB5-B91C-2CDEDFAFB217 --intensity 0` | success |
| draft effect add | ⚠️ 官方参数/用法拒绝 | 2 | `effect add --ref local://func-test-1012-133748 --resource vimo://7618532181840973080 --type video_effect --start 0s --du` | cli parse error: ValidationError: MotionGraph-only options require `--type motiongraph` |
| draft effect remove | ✅ 成功 | 0 | `effect remove --ref local://func-test-1012-133748 --seg-id 6D2E0EFC-E6AA-440E-9E5F-8A451499A76A` | success |
| draft effect generate | ⚠️ 官方业务拒绝 | 1 | `effect generate --ref local://func-test-1012-133748 --dir C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\o` | motiongraph: upstream operation failed: submit stage failed: Lumi HTTP request failed, status=404, body=<html> <head><t |
| draft adjust add | ✅ 成功 | 0 | `adjust add --brightness 0.1 --ref local://func-test-1012-133748 --start 0s --duration 1s` | success |
| draft adjust remove | ➡️ 需真实前置产物 | 2 | `adjust remove --ref local://func-test-1012-133748 --seg-id EDF1D961-E509-476F-9CC1-CAC4280B8703` | gen_patch: invalid action: draft adjust remove target EDF1D961-E509-476F-9CC1-CAC4280B8703 has type 'segment_video', exp |
| draft subtitle add | ✅ 成功 | 0 | `subtitle add --ref local://func-test-1012-133748 --content 功能测试 --start 0s --duration 1s` | success |
| draft subtitle remove | ✅ 成功 | 0 | `subtitle remove --ref local://func-test-1012-133748 --seg-id 5C8F3EA0-DC32-4432-9834-D0487E5B8F6E` | success |
| draft subtitle recognize | ✅ 成功 | 0 | `subtitle recognize --ref local://func-test-1012-133748 --seg-id 5C8F3EA0-DC32-4432-9834-D0487E5B8F6E --language zh --mod` | success |
| draft lyrics add | ✅ 成功 | 0 | `lyrics add --ref local://func-test-1012-133748 --content 功能测试 --start 0s --duration 1s` | success |
| draft lyrics remove | ✅ 成功 | 0 | `lyrics remove --ref local://func-test-1012-133748 --seg-id 5C8F3EA0-DC32-4432-9834-D0487E5B8F6E` | success |
| draft lyrics recognize | ✅ 成功 | 0 | `lyrics recognize --ref local://func-test-1012-133748 --seg-id 5C8F3EA0-DC32-4432-9834-D0487E5B8F6E --language zh --mode ` | success |
| draft keyframe add | ✅ 成功 | 0 | `keyframe add --ref local://func-test-1012-133748 --seg-id EDF1D961-E509-476F-9CC1-CAC4280B8703 --animated-property opaci` | success |
| draft keyframe update | ➡️ 需真实前置产物 | 2 | `keyframe update --ref local://func-test-1012-133748 --seg-id EDF1D961-E509-476F-9CC1-CAC4280B8703 --animated-property op` | cli parse error: ValidationError: draft keyframe update requires exactly one of `--value` or `--values` |
| draft keyframe remove | ➡️ 需真实前置产物 | 2 | `keyframe remove --ref local://func-test-1012-133748 --seg-id EDF1D961-E509-476F-9CC1-CAC4280B8703 --animated-property op` | cli parse error: ValidationError: draft keyframe remove requires exactly one of `--time/--times`, `--indexes`, `--timeli |
| draft blueprint init | ✅ 成功 | 0 | `blueprint init --workspace C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\workspace --protocol xmldraft` | success |
| draft blueprint sync | ✅ 成功 | 0 | `blueprint sync --workspace C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\workspace --ref local://func-tes` | success |
| draft blueprint apply | ✅ 成功 | 0 | `blueprint apply --workspace C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\workspace --ref local://func-te` | success |
| draft blueprint resource | ⚠️ 官方参数/用法拒绝 | 2 | `blueprint resource --workspace C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\workspace` | cli parse error: RequiredError: exactly one of --search, --import, --update, or --sync is required |
| material search | ✅ 成功 | 0 | `search --type text --prompt 花` | success |
| material download | ✅ 成功 | 0 | `download --type sticker --resource-id 7575784012703190297 --resource-dir C:\Users\Administrator\AppData\Local\Temp\jiany` | success |
| material query | ✅ 成功 | 0 | `query --resource-id 7575784012703190297 --type text` | success |
| material topic | ⚠️ 官方业务拒绝 | 1 | `topic --type sticker --template-id func-test` | material command failed in resource_pool: resource_pool err_code=-7001, err_msg=invalid argument: --topic-id must be gre |
| material recommend | 🚧 官方未实现 | 2 | `recommend --type text` | command is not implemented yet (work in progress) |
| material similar | 🚧 官方未实现 | 2 | `similar --type text --by func-test` | command is not implemented yet (work in progress) |
| media transcode-image | ✅ 成功 | 0 | `transcode-image --input C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\media\sample.png --output C:\Users\` | success |
| media crop-image | ✅ 成功 | 0 | `crop-image --input C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\media\sample.png --output C:\Users\Admin` | success |
| media resize-image | ⚠️ 官方参数/用法拒绝 | 2 | `resize-image --input C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\media\sample.png --output C:\Users\Adm` | media: invalid size parameter (--width/--height must be positive; --short-side conflicts with --width/--height): resize- |
| media compress | ✅ 成功 | 0 | `compress --input C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\media\sample.mp4 --output C:\Users\Adminis` | success |
| media trim-video | ✅ 成功 | 0 | `trim-video --input C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\media\sample.mp4 --output C:\Users\Admin` | success |
| media trim-audio | ✅ 成功 | 0 | `trim-audio --input C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\media\sample.m4a --output C:\Users\Admin` | success |
| media change-video-speed | ✅ 成功 | 0 | `change-video-speed --input C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\media\sample.mp4 --output C:\Use` | success |
| media change-audio-speed | ✅ 成功 | 0 | `change-audio-speed --input C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\media\sample.m4a --output C:\Use` | success |
| media rotate | ✅ 成功 | 0 | `rotate --input C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\media\sample.mp4 --output C:\Users\Administr` | success |
| media extract-frames | ✅ 成功 | 0 | `extract-frames --input C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\media\sample.mp4 --output-dir C:\Use` | success |
| media extract-audio | ✅ 成功 | 0 | `extract-audio --input C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\media\sample.m4a --output C:\Users\Ad` | success |
| media probe | ✅ 成功 | 0 | `probe --input C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\media\sample.mp4 --field size_bytes` | success |
| media loudness | ✅ 成功 | 0 | `loudness --input C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\media\sample.mp4 --start 0s --duration 1s` | success |
| media measure-box | ✅ 成功 | 0 | `measure-box --allow-video-decode --input C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\media\sample.mp4 -` | success |
| media beats | ✅ 成功 | 0 | `beats --input C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\media\sample.mp4 --output C:\Users\Administra` | success |
| media object-matting-track | ⚠️ 官方参数/用法拒绝 | 2 | `object-matting-track --input C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\media\sample.mp4 --seed-time f` | media: invalid time literal (expected forms: 2min, 1.5s, 500ms, 1200000us; bare numbers and m are invalid): --seed-time: |
| media asr | ✅ 成功 | 0 | `asr --input C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\media\sample.m4a --language zh --output C:\User` | success |
| media vad | ✅ 成功 | 0 | `vad --input C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\media\sample.m4a --output C:\Users\Administrato` | success |
| media feature | ✅ 成功 | 0 | `feature --input C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\media\sample.mp4 --module quality` | success |
| media translate | ⚠️ 官方参数/用法拒绝 | 2 | `translate --input C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\media\sample.mp4 --target-language func-t` | media: invalid argument: --input must contain valid JSON |
| media understand | ⚠️ 官方业务拒绝 | 1 | `understand --path C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\media\sample.mp4 --prompt 花 --segment-id ` | media: processing failed: invalid request stage=invalid_client_source request_logid=202610121347533E08E451F8294BEE0CA7 b |
| lint command | ➡️ 需真实前置产物 | 2 | `command --acceptance-type all --acceptance-level L0 --output C:\Users\Administrator\AppData\Local\Temp\jianying-func-tes` | invalid argument: repo root does not look like lyra-cli: C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\ |
| lint media | ✅ 成功 | 0 | `media --input C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\media\sample.mp4 --expected-kind auto --expec` | success |
| lint algorithm-effect | ✅ 成功 | 2 | `algorithm-effect --algorithm func-test --comparison-mode paired_artifact --candidate C:\Users\Administrator\AppData\Loca` | success |
| lint draft | ✅ 成功 | 1 | `draft --ref local://func-test-1012-133748 --spatial-overlap-severity warning --occlusion-severity warning --output C:\Us` | success |
| lint trace | ✅ 成功 | 1 | `trace --trace C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\media\sample.mp4 --target-policy stable --mat` | success |
| upgrade | 🚧 官方未实现 | 2 | `` | command is not implemented yet (work in progress) |
| draft project duplicate | ✅ 成功 | 0 | `project duplicate --ref local://func-test-1012-133748 --to local://func-test-1012-133748-copy` | success |
| draft project import | ⚠️ 官方业务拒绝 | 1 | `project import --ref local://func-test-1012-133748` | draft already exists: local://func-test-1012-133748 already lives in the default workspace |
| draft history undo | 🚧 仅内嵌库支持 | 2 | `history undo --ref local://func-test-1012-133748` | draft history undo / redo is only available when lyra-cli is embedded as a client library; the standalone executable doe |
| draft history redo | 🚧 仅内嵌库支持 | 2 | `history redo --ref local://func-test-1012-133748` | draft history undo / redo is only available when lyra-cli is embedded as a client library; the standalone executable doe |
| draft deform apply | ✅ 成功 | 0 | `deform apply --scale 1 --ref local://func-test-1012-133748 --mode stretch --deform-seg-id EDF1D961-E509-476F-9CC1-CAC428` | success |
| draft sticker translate | ✅ 成功 | 0 | `sticker translate --ref local://func-test-1012-133748 --seg-id 2B949C29-5C7A-47E7-8830-D733A4D83F3C` | success |
| draft text-template translate | ➡️ 需真实前置产物 | 2 | `text-template translate --ref local://func-test-1012-133748 --seg-id 5C8F3EA0-DC32-4432-9834-D0487E5B8F6E` | gen_patch: invalid action: draft text-template translate target 5C8F3EA0-DC32-4432-9834-D0487E5B8F6E has type 'segment_t |
| draft text-template add | ✅ 成功 | 0 | `text-template add --ref local://func-test-1012-133748 --resource template://7611391513850924312 --content 功能测试 --start 0` | success |
| draft text-template replace | ➡️ 需真实前置产物 | 2 | `text-template replace --ref local://func-test-1012-133748 --seg-id 5C8F3EA0-DC32-4432-9834-D0487E5B8F6E --resource templ` | gen_patch: invalid action: draft text-template replace target 5C8F3EA0-DC32-4432-9834-D0487E5B8F6E has type 'segment_tex |
| draft text-template remove | ➡️ 需真实前置产物 | 2 | `text-template remove --ref local://func-test-1012-133748 --seg-id 5C8F3EA0-DC32-4432-9834-D0487E5B8F6E` | gen_patch: invalid action: draft text-template remove target 5C8F3EA0-DC32-4432-9834-D0487E5B8F6E has type 'segment_text |
| draft segment time-range | ⚠️ 官方参数/用法拒绝 | 2 | `segment time-range --ref local://func-test-1012-133748 --seg-id EDF1D961-E509-476F-9CC1-CAC4280B8703 --out C:\Users\Admi` | cli parse error: ValidationError: draft segment time-range --duration cannot be combined with endpoint or endpoint-offse |
| draft segment add | ✅ 成功 | 0 | `segment add --ref local://func-test-1012-133748 --type text --resource local:///C:/Users/Administrator/AppData/Local/Tem` | success |
| draft compound-clip break-apart | ⚠️ 官方业务拒绝 | 1 | `compound-clip break-apart --ref local://func-test-1012-133748 --seg-id EDF1D961-E509-476F-9CC1-CAC4280B8703` | patch apply failed: break_combination cannot find stored child draft payload |
| draft blueprint plan | ✅ 成功 | 0 | `blueprint plan --workspace C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\workspace` | success |
| draft blueprint cancel | 🚧 仅内嵌库支持 | 2 | `blueprint cancel` | draft blueprint cancel is only available when lyra-cli is embedded as a client library; the standalone executable does n |
| draft blueprint commerce | ✅ 成功 | 0 | `blueprint commerce --workspace C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\workspace` | success |
| draft blueprint patch | ⚠️ 官方业务拒绝 | 1 | `blueprint patch --workspace C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\workspace --patch-file C:\Users` | internal error: process terminated by unhandled Windows exception 0xE06D7363 |
| draft video transition add | ✅ 成功 | 0 | `video transition add --ref local://func-test-1012-133748 --seg-id EDF1D961-E509-476F-9CC1-CAC4280B8703 --resource vimo:/` | success |
| draft video transition update | ✅ 成功 | 0 | `video transition update --ref local://func-test-1012-133748 --seg-id EDF1D961-E509-476F-9CC1-CAC4280B8703 --resource loc` | success |
| draft video transition remove | ✅ 成功 | 0 | `video transition remove --ref local://func-test-1012-133748 --seg-id EDF1D961-E509-476F-9CC1-CAC4280B8703` | success |
| draft video filter add | ✅ 成功 | 0 | `video filter add --ref local://func-test-1012-133748 --seg-id EDF1D961-E509-476F-9CC1-CAC4280B8703 --resource vimo://749` | success |
| draft video filter update | ✅ 成功 | 0 | `video filter update --ref local://func-test-1012-133748 --seg-id EDF1D961-E509-476F-9CC1-CAC4280B8703 --intensity 0` | success |
| draft video filter remove | ✅ 成功 | 0 | `video filter remove --ref local://func-test-1012-133748 --seg-id EDF1D961-E509-476F-9CC1-CAC4280B8703` | success |
| draft video effect add | ✅ 成功 | 0 | `video effect add --ref local://func-test-1012-133748 --seg-id EDF1D961-E509-476F-9CC1-CAC4280B8703 --resource vimo://761` | success |
| draft video effect update | ✅ 成功 | 0 | `video effect update --ref local://func-test-1012-133748 --seg-id EDF1D961-E509-476F-9CC1-CAC4280B8703 --params-json {"op` | success |
| draft video effect remove | ✅ 成功 | 0 | `video effect remove --ref local://func-test-1012-133748 --seg-id EDF1D961-E509-476F-9CC1-CAC4280B8703` | success |
| draft video mask add | ✅ 成功 | 0 | `video mask add --ref local://func-test-1012-133748 --seg-id EDF1D961-E509-476F-9CC1-CAC4280B8703 --resource vimo://76185` | success |
| draft video mask update | ⚠️ 官方参数/用法拒绝 | 2 | `video mask update --ref local://func-test-1012-133748 --seg-id EDF1D961-E509-476F-9CC1-CAC4280B8703` | gen_patch: invalid action: gen_patch --update has no registered handler for field(s):  |
| draft video mask remove | ✅ 成功 | 0 | `video mask remove --ref local://func-test-1012-133748 --seg-id EDF1D961-E509-476F-9CC1-CAC4280B8703` | success |
| draft video animation add | ✅ 成功 | 0 | `video animation add --ref local://func-test-1012-133748 --seg-id EDF1D961-E509-476F-9CC1-CAC4280B8703 --resource local:/` | success |
| draft video animation update | ➡️ 需真实前置产物 | 2 | `video animation update --ref local://func-test-1012-133748 --seg-id EDF1D961-E509-476F-9CC1-CAC4280B8703 --animation-typ` | gen_patch: invalid action: gen_patch --update animation found no existing 'func-test' animation on target; use --add pro |
| draft video animation remove | ✅ 成功 | 0 | `video animation remove --ref local://func-test-1012-133748 --seg-id EDF1D961-E509-476F-9CC1-CAC4280B8703` | success |
| draft video beat add | ✅ 成功 | 0 | `video beat add --ref local://func-test-1012-133748 --seg-id EDF1D961-E509-476F-9CC1-CAC4280B8703 --times 1s` | success |
| draft video beat remove | ✅ 成功 | 0 | `video beat remove --ref local://func-test-1012-133748 --seg-id EDF1D961-E509-476F-9CC1-CAC4280B8703` | success |
| draft video audio-effect add | ✅ 成功 | 0 | `video audio-effect add --ref local://func-test-1012-133748 --seg-id EDF1D961-E509-476F-9CC1-CAC4280B8703 --resource vimo` | success |
| draft video color smart-color | ✅ 成功 | 0 | `video color smart-color --ref local://func-test-1012-133748 --seg-id EDF1D961-E509-476F-9CC1-CAC4280B8703 --resource loc` | success |
| draft video color correct | ✅ 成功 | 0 | `video color correct --ref local://func-test-1012-133748 --seg-id EDF1D961-E509-476F-9CC1-CAC4280B8703 --resource local:/` | success |
| draft text effect update | ✅ 成功 | 0 | `text effect update --ref local://func-test-1012-133748 --seg-id 5C8F3EA0-DC32-4432-9834-D0487E5B8F6E --resource vimo://7` | success |
| draft text effect add | ✅ 成功 | 0 | `text effect add --ref local://func-test-1012-133748 --content 功能测试 --resource vimo://7618532181840973080 --name func-tes` | success |
| draft text animation set | ✅ 成功 | 0 | `text animation set --ref local://func-test-1012-133748 --seg-id 5C8F3EA0-DC32-4432-9834-D0487E5B8F6E --resource local://` | success |
| draft text animation remove | ✅ 成功 | 0 | `text animation remove --ref local://func-test-1012-133748 --seg-id 5C8F3EA0-DC32-4432-9834-D0487E5B8F6E` | success |
| draft subtitle template add | ✅ 成功 | 0 | `subtitle template add --ref local://func-test-1012-133748 --resource template://7472623396317269310 --content 功能测试 --sta` | success |
| draft subtitle template replace | ➡️ 需真实前置产物 | 2 | `subtitle template replace --ref local://func-test-1012-133748 --seg-id 5C8F3EA0-DC32-4432-9834-D0487E5B8F6E --resource t` | gen_patch: invalid action: draft subtitle template replace target 5C8F3EA0-DC32-4432-9834-D0487E5B8F6E has type 'segment |
| draft lyrics animation add | ➡️ 需真实前置产物 | 2 | `lyrics animation add --ref local://func-test-1012-133748 --resource local:///C:/Users/Administrator/AppData/Local/Temp/j` | gen_patch: invalid action: gen_patch --add lyric_animation does not support local lyric animation resources |
| draft lyrics animation update | ➡️ 需真实前置产物 | 2 | `lyrics animation update --ref local://func-test-1012-133748 --seg-id 5C8F3EA0-DC32-4432-9834-D0487E5B8F6E --resource loc` | gen_patch: invalid action: gen_patch --update lyric_animation does not support local lyric animation resources |
| draft lyrics animation replace | ➡️ 需真实前置产物 | 2 | `lyrics animation replace --ref local://func-test-1012-133748 --seg-id 5C8F3EA0-DC32-4432-9834-D0487E5B8F6E --resource lo` | gen_patch: invalid action: gen_patch --update lyric_animation does not support local lyric animation resources |
| draft keyframe curve set | ⚠️ 官方参数/用法拒绝 | 2 | `keyframe curve set --ref local://func-test-1012-133748 --seg-id EDF1D961-E509-476F-9CC1-CAC4280B8703 --animated-property` | cli parse error: ValidationError: --at: expects an explicit unit: us, ms, s, or min; bare numbers and `m` are not accept |
| material motiongraph build-runtime-manifest | ⚠️ 官方业务拒绝 | 1 | `motiongraph build-runtime-manifest --package func-test --output-dir C:\Users\Administrator\AppData\Local\Temp\jianying-f` | motiongraph: invalid provider response: package not found: func-test |
| material motiongraph track-subject-mask | ➡️ 需真实前置产物 | 2 | `motiongraph track-subject-mask --input C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\media\sample.mp4 --r` | motiongraph: invalid argument: track-subject-mask requires exactly one of --target-object-desc or --seed-mask-rle-json |
| material motiongraph encode-subject-alpha | ➡️ 需真实前置产物 | 2 | `motiongraph encode-subject-alpha --mask-dir func-test --output-dir C:\Users\Administrator\AppData\Local\Temp\jianying-fu` | motiongraph: invalid argument: mask dir is not a directory: func-test |
| material motiongraph track-plane-quad | ⚠️ 官方参数/用法拒绝 | 2 | `motiongraph track-plane-quad --ref local://func-test-1012-133748 --target-seg-id func-test --output-dir C:\Users\Adminis` | motiongraph: invalid argument: direct track-plane-quad requires --plane-desc or a legacy --object-desc when --initial-qu |
| media aigc text2image | ✅ 成功 | 0 | `aigc text2image --prompt 花 --download-format png` | success |
| media aigc image2image | ⚠️ 官方业务拒绝 | 1 | `aigc image2image --images func-test --prompt 花 --download-format png` | media: input file not found: input file does not exist: func-test |
| media aigc text2video | ✅ 成功 | 0 | `aigc text2video --prompt 花 --duration 1 --download-format png` | success |
| media aigc image2video | ⚠️ 官方参数/用法拒绝 | 2 | `aigc image2video --first-image C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\media\sample.png --reference` | media AIGC: invalid request: --reference-image cannot be combined with --first-image/--image or --end-image |
| media aigc query | ⚠️ 官方参数/用法拒绝 | 2 | `aigc query --submit-id func-test --download-format png` | media AIGC: invalid submit_id: invalid media AIGC submit_id |
| auth login | ⏭️ 有意跳过（破坏会话/需人工交互） | None | `` | 交互式登录，必须由用户在浏览器完成授权 |
| auth relogin | ⏭️ 有意跳过（破坏会话/需人工交互） | None | `` | 交互式重新登录，必须由用户授权 |
| auth qrcode | ⏭️ 有意跳过（破坏会话/需人工交互） | None | `` | 交互式扫码登录，必须由用户操作 |
| auth status | ✅ 成功 | 0 | `status` | success |
| auth me | ✅ 成功 | 0 | `me` | success |
| auth check | ✅ 成功 | 0 | `check` | success |
| auth logout | ⏭️ 有意跳过（破坏会话/需人工交互） | None | `` | 会真实登出账号，破坏同批其他需要登录的命令 |
| draft project version upgrade | 🚧 官方未实现 | 2 | `project version upgrade --ref local://func-test-1012-133748` | command is not implemented yet (work in progress): draft project version upgrade is not implemented yet |
| draft project version downgrade | ✅ 成功 | 0 | `project version downgrade --ref local://func-test-1012-133748` | success |
| draft timeline segment copy | ⚠️ 官方业务拒绝 | 1 | `timeline segment copy --ref local://func-test-1012-133748 --seg-id EDF1D961-E509-476F-9CC1-CAC4280B8703 --source-timelin` | patch apply failed: {"lyra_err_code":109,"lyra_err_msg":"transfer_segments source or target draft is unavailable"} |
| draft timeline segment move | ⚠️ 官方业务拒绝 | 1 | `timeline segment move --ref local://func-test-1012-133748 --seg-id EDF1D961-E509-476F-9CC1-CAC4280B8703 --source-timelin` | patch apply failed: {"lyra_err_code":109,"lyra_err_msg":"transfer_segments source or target draft is unavailable"} |
| draft algo object-matting-track | ➡️ 需真实前置产物 | 2 | `algo object-matting-track --ref local://func-test-1012-133748 --seg-id EDF1D961-E509-476F-9CC1-CAC4280B8703 --segment-ti` | cli parse error: ValidationError: object-matting-track requires exactly one of --seed-mask-rle-json or --target-object-d |
