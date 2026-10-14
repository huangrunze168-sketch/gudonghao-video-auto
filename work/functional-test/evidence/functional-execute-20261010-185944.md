# lyra-cli 真实功能测试报告

- 清单命令数：195

## 执行层

| 状态 | 数量 |
| --- | --- |
| ✅ 成功 | 126 |
| ➡️ 需真实前置产物 | 23 |
| ⚠️ 官方参数/用法拒绝 | 20 |
| ⚠️ 官方业务拒绝 | 14 |
| 🚧 官方未实现 | 4 |
| ⏭️ 有意跳过（破坏会话/需人工交互） | 4 |
| 🚧 仅内嵌库支持 | 3 |
| 🔐 需要登录 | 1 |

| 命令 | 状态 | exit | 参数 | 官方消息 |
| --- | --- | --- | --- | --- |
| draft edit | ✅ 成功 | 0 | `edit --ref local://func-test-1010-184835 --op split --target seg_id=6FAEA893-1BFB-47D9-87D0-B87827F48F10 --params points` | success |
| draft config | ✅ 成功 | 0 | `config --ref local://func-test-1010-184835 --ratio 16:9` | success |
| draft project create | ✅ 成功 | 0 | `project create --ref local://func-test-1010-184835 --dir C:\Users\Administrator\AppData\Local\JianyingPro\User Data\Proj` | success |
| draft project list | ✅ 成功 | 0 | `project list` | success |
| draft project focus | ✅ 成功 | 0 | `project focus --ref local://func-test-1010-184835` | success |
| draft project delete | ✅ 成功 | 0 | `project delete --ref local://func-test-1010-184835` | success |
| draft cover set | ✅ 成功 | 0 | `cover set --ref local://func-test-1010-184835 --image C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\media` | success |
| draft cover clear | ✅ 成功 | 0 | `cover clear --ref local://func-test-1010-184835` | success |
| draft extract summary | ✅ 成功 | 0 | `extract summary --ref local://func-test-1010-184835 --dir C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\o` | success |
| draft template add | ⚠️ 官方业务拒绝 | 1 | `template add --ref local://func-test-1010-184835 --resource local:///C:/Users/Administrator/AppData/Local/Temp/jianying-` | patch apply failed: template parse failed: code=-10011, msg=unzip failed |
| draft template publish | ✅ 成功 | 0 | `template publish --ref local://func-test-1010-184835 --dir C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\` | success |
| draft template render | ⚠️ 官方参数/用法拒绝 | 2 | `template render --config C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\out\template-config.json --ref loc` | invalid argument: template config contains unsupported field: schema |
| draft template slots | ✅ 成功 | 0 | `template slots --ref local://func-test-1010-184835 --template-seg-id 1044EEC8-615A-4089-8CA7-D28007A9F7BD` | success |
| draft template replace | ➡️ 需真实前置产物 | 2 | `template replace --ref local://func-test-1010-184835 --template-seg-id 1044EEC8-615A-4089-8CA7-D28007A9F7BD --slot func-` | invalid argument: slot not found: func-test |
| draft algo query | ➡️ 需真实前置产物 | 2 | `algo query --task-id func-test` | invalid video-tracking task id: func-test |
| draft algo wait | ➡️ 需真实前置产物 | 2 | `algo wait --task-id func-test` | invalid video-tracking task id: func-test |
| draft algo quality-enhance | ✅ 成功 | 0 | `algo quality-enhance --ref local://func-test-1010-184835 --seg-id 1044EEC8-615A-4089-8CA7-D28007A9F7BD --level 1 --from ` | success |
| draft algo upscale-resolution | ✅ 成功 | 0 | `algo upscale-resolution --ref local://func-test-1010-184835 --seg-id 1044EEC8-615A-4089-8CA7-D28007A9F7BD --mode 1 --fro` | success |
| draft algo ai-frame-interpolation | ✅ 成功 | 0 | `algo ai-frame-interpolation --ref local://func-test-1010-184835 --seg-id 1044EEC8-615A-4089-8CA7-D28007A9F7BD --fps 30 -` | success |
| draft algo ai-matting | ✅ 成功 | 0 | `algo ai-matting --ref local://func-test-1010-184835 --seg-id 1044EEC8-615A-4089-8CA7-D28007A9F7BD --workspace C:\Users\A` | success |
| draft algo ai-transition | ⚠️ 官方参数/用法拒绝 | 2 | `algo ai-transition --ref local://func-test-1010-184835 --after-seg-id 1044EEC8-615A-4089-8CA7-D28007A9F7BD --resource lo` | media AIGC: invalid request: ai-transition generation requires a right video segment after --after-seg-id |
| draft algo custom-matting | ✅ 成功 | 0 | `algo custom-matting --ref local://func-test-1010-184835 --seg-id 1044EEC8-615A-4089-8CA7-D28007A9F7BD --workspace C:\Use` | success |
| draft algo chroma-color-matting | ✅ 成功 | 0 | `algo chroma-color-matting --color #00FF00FF --ref local://func-test-1010-184835 --seg-id 1044EEC8-615A-4089-8CA7-D28007A` | success |
| draft algo video-tracking | ⚠️ 官方业务拒绝 | 1 | `algo video-tracking --tracker-type point --center-x 0.5 --center-y 0.5 --width 0.2 --height 0.2 --ref local://func-test-` | internal error: process terminated by unhandled Windows exception 0xE06D7363 |
| draft algo sound-separation | ✅ 成功 | 0 | `algo sound-separation --ref local://func-test-1010-184835 --seg-id 1044EEC8-615A-4089-8CA7-D28007A9F7BD --mode vocal --o` | success |
| draft algo loudness-normalize | ✅ 成功 | 0 | `algo loudness-normalize --ref local://func-test-1010-184835 --seg-id 1044EEC8-615A-4089-8CA7-D28007A9F7BD` | success |
| draft algo denoise | ⚠️ 官方参数/用法拒绝 | 2 | `algo denoise --ref local://func-test-1010-184835 --seg-id 1044EEC8-615A-4089-8CA7-D28007A9F7BD --path C:\Users\Administr` | draft algo: unsupported algorithm type: denoise |
| draft algo voice-enhance | ⚠️ 官方参数/用法拒绝 | 2 | `algo voice-enhance --ref local://func-test-1010-184835 --seg-id 1044EEC8-615A-4089-8CA7-D28007A9F7BD` | draft algo: unsupported algorithm type: vocal_beautify |
| draft algo video-stabilize | ⚠️ 官方参数/用法拒绝 | 2 | `algo video-stabilize --ref local://func-test-1010-184835 --seg-id 1044EEC8-615A-4089-8CA7-D28007A9F7BD` | draft algo: unsupported algorithm type: video_stable |
| draft algo tts | ✅ 成功 | 0 | `algo tts --ref local://func-test-1010-184835 --seg-id C421001B-6650-4C9F-9496-CE34BCBB677F --text 功能测试 --speed 1.0 --spe` | success |
| draft algo subtitle-recognize | ✅ 成功 | 0 | `algo subtitle-recognize --ref local://func-test-1010-184835 --seg-id C421001B-6650-4C9F-9496-CE34BCBB677F --language zh ` | success |
| draft algo text-add-tone | ✅ 成功 | 0 | `algo text-add-tone --ref local://func-test-1010-184835 --seg-id C421001B-6650-4C9F-9496-CE34BCBB677F --text 功能测试 --speed` | success |
| draft algo music-beats | ✅ 成功 | 0 | `algo music-beats --ref local://func-test-1010-184835 --seg-id 1044EEC8-615A-4089-8CA7-D28007A9F7BD --mode beat --output-` | success |
| draft algo material-understand | ⚠️ 官方业务拒绝 | 1 | `algo material-understand --ref local://func-test-1010-184835 --seg-id 1044EEC8-615A-4089-8CA7-D28007A9F7BD --prompt 花 --` | patch apply failed: {"lyra_err_code":100,"lyra_err_msg":"invalid request stage=invalid_client_source request_logid=20261 |
| draft algo subtitle-keywords | ✅ 成功 | 0 | `algo subtitle-keywords --ref local://func-test-1010-184835 --seg-id C421001B-6650-4C9F-9496-CE34BCBB677F --language zh` | success |
| draft video crop | ✅ 成功 | 0 | `video crop --ref local://func-test-1010-184835 --seg-id 1044EEC8-615A-4089-8CA7-D28007A9F7BD` | success |
| draft video speed | ✅ 成功 | 0 | `video speed --ref local://func-test-1010-184835 --seg-id 1044EEC8-615A-4089-8CA7-D28007A9F7BD --speed 1.0` | success |
| draft video stabilize | ⚠️ 官方参数/用法拒绝 | 2 | `video stabilize --ref local://func-test-1010-184835 --seg-id 1044EEC8-615A-4089-8CA7-D28007A9F7BD` | draft algo: unsupported algorithm type: video_stable |
| draft video scale | ✅ 成功 | 0 | `video scale --ref local://func-test-1010-184835 --seg-id 1044EEC8-615A-4089-8CA7-D28007A9F7BD` | success |
| draft video rotate | ✅ 成功 | 0 | `video rotate --ref local://func-test-1010-184835 --seg-id 1044EEC8-615A-4089-8CA7-D28007A9F7BD --rotation 0` | success |
| draft video translate | ✅ 成功 | 0 | `video translate --ref local://func-test-1010-184835 --seg-id 1044EEC8-615A-4089-8CA7-D28007A9F7BD` | success |
| draft video alpha | ✅ 成功 | 0 | `video alpha --ref local://func-test-1010-184835 --seg-id 1044EEC8-615A-4089-8CA7-D28007A9F7BD --alpha 1` | success |
| draft video flip | ✅ 成功 | 0 | `video flip --ref local://func-test-1010-184835 --seg-id 1044EEC8-615A-4089-8CA7-D28007A9F7BD` | success |
| draft video layer | ✅ 成功 | 0 | `video layer --ref local://func-test-1010-184835 --seg-id 1044EEC8-615A-4089-8CA7-D28007A9F7BD --z-order 0` | success |
| draft video volume | ✅ 成功 | 0 | `video volume --linear 0.5 --ref local://func-test-1010-184835 --seg-id 1044EEC8-615A-4089-8CA7-D28007A9F7BD` | success |
| draft video freeze | ✅ 成功 | 0 | `video freeze --ref local://func-test-1010-184835 --seg-id 1044EEC8-615A-4089-8CA7-D28007A9F7BD --time 1s --duration 1s` | success |
| draft video add | ✅ 成功 | 0 | `video add --ref local://func-test-1010-184835 --resource local:///C:/Users/Administrator/AppData/Local/Temp/jianying-fun` | success |
| draft video remove | ✅ 成功 | 0 | `video remove --ref local://func-test-1010-184835 --seg-id 1044EEC8-615A-4089-8CA7-D28007A9F7BD` | success |
| draft video adjust | ✅ 成功 | 0 | `video adjust --brightness 0.1 --ref local://func-test-1010-184835 --seg-id 1044EEC8-615A-4089-8CA7-D28007A9F7BD` | success |
| draft video background | ✅ 成功 | 0 | `video background --type color --ref local://func-test-1010-184835 --seg-id 1044EEC8-615A-4089-8CA7-D28007A9F7BD --image ` | success |
| draft video matting-stroke | ✅ 成功 | 0 | `video matting-stroke --enable --ref local://func-test-1010-184835 --seg-id 1044EEC8-615A-4089-8CA7-D28007A9F7BD --resour` | success |
| draft video mix-mode | ⚠️ 官方参数/用法拒绝 | 2 | `video mix-mode --enable --ref local://func-test-1010-184835 --seg-id 1044EEC8-615A-4089-8CA7-D28007A9F7BD --resource vim` | gen_patch: invalid action: gen_patch --update mix_mode: segment 1044EEC8-615A-4089-8CA7-D28007A9F7BD is on main track (t |
| draft video face-beauty | ⚠️ 官方参数/用法拒绝 | 2 | `video face-beauty --ref local://func-test-1010-184835 --seg-id 1044EEC8-615A-4089-8CA7-D28007A9F7BD` | gen_patch: invalid action: gen_patch --update has no registered handler for field(s):  |
| draft video extract-frames | ✅ 成功 | 0 | `video extract-frames --ref local://func-test-1010-184835 --seg-id 1044EEC8-615A-4089-8CA7-D28007A9F7BD --output-path C:\` | success |
| draft video extract-music | ✅ 成功 | 0 | `video extract-music --ref local://func-test-1010-184835 --seg-id 1044EEC8-615A-4089-8CA7-D28007A9F7BD --start 0s` | success |
| draft sticker add | ✅ 成功 | 0 | `sticker add --ref local://func-test-1010-184835 --resource vimo://7575784012703190297 --start 0s --duration 1s` | success |
| draft sticker remove | ✅ 成功 | 0 | `sticker remove --ref local://func-test-1010-184835 --seg-id CEC3C33C-7BB6-4DEC-A627-1321E4F4BAB9` | success |
| draft text translate | ✅ 成功 | 0 | `text translate --ref local://func-test-1010-184835 --seg-id C421001B-6650-4C9F-9496-CE34BCBB677F` | success |
| draft text content | ✅ 成功 | 0 | `text content --ref local://func-test-1010-184835 --seg-id C421001B-6650-4C9F-9496-CE34BCBB677F --content 功能测试` | success |
| draft text wrap-width | ✅ 成功 | 0 | `text wrap-width --width 0.5 --ref local://func-test-1010-184835 --seg-id C421001B-6650-4C9F-9496-CE34BCBB677F` | success |
| draft text add | ✅ 成功 | 0 | `text add --ref local://func-test-1010-184835 --content 功能测试 --start 0s --duration 1s` | success |
| draft text remove | ✅ 成功 | 0 | `text remove --ref local://func-test-1010-184835 --seg-id C421001B-6650-4C9F-9496-CE34BCBB677F` | success |
| draft text style | ✅ 成功 | 0 | `text style --size 7 --ref local://func-test-1010-184835 --seg-id C421001B-6650-4C9F-9496-CE34BCBB677F` | success |
| draft audio volume | ✅ 成功 | 0 | `audio volume --linear 0.5 --ref local://func-test-1010-184835 --seg-id 3739008F-F8EF-4D1E-8BBF-643C4587AF2A` | success |
| draft audio fade | ✅ 成功 | 0 | `audio fade --ref local://func-test-1010-184835 --seg-id 3739008F-F8EF-4D1E-8BBF-643C4587AF2A --out 1s --type both` | success |
| draft audio speed | ✅ 成功 | 0 | `audio speed --ref local://func-test-1010-184835 --seg-id 3739008F-F8EF-4D1E-8BBF-643C4587AF2A --speed 1.0` | success |
| draft audio add | ✅ 成功 | 0 | `audio add --ref local://func-test-1010-184835 --resource local:///C:/Users/Administrator/AppData/Local/Temp/jianying-fun` | success |
| draft audio remove | ✅ 成功 | 0 | `audio remove --ref local://func-test-1010-184835 --seg-id 3739008F-F8EF-4D1E-8BBF-643C4587AF2A` | success |
| draft segment remove | ✅ 成功 | 0 | `segment remove --ref local://func-test-1010-184835 --seg-id 1044EEC8-615A-4089-8CA7-D28007A9F7BD` | success |
| draft segment split | ✅ 成功 | 0 | `segment split --ref local://func-test-1010-184835 --seg-id 1044EEC8-615A-4089-8CA7-D28007A9F7BD --points 1s` | success |
| draft segment duplicate | ✅ 成功 | 0 | `segment duplicate --ref local://func-test-1010-184835 --seg-id 1044EEC8-615A-4089-8CA7-D28007A9F7BD --start 0s` | success |
| draft segment move | ⚠️ 官方业务拒绝 | 1 | `segment move --ref local://func-test-1010-184835 --seg-id 1044EEC8-615A-4089-8CA7-D28007A9F7BD --start 0s` | draft edit made no effective segment changes: gen_patch --move made no effective changes; target already has the request |
| draft compound-clip create | ✅ 成功 | 0 | `compound-clip create --ref local://func-test-1010-184835 --seg-id 1044EEC8-615A-4089-8CA7-D28007A9F7BD --name func-test` | success |
| draft filter add | ✅ 成功 | 0 | `filter add --ref local://func-test-1010-184835 --resource local:///C:/Users/Administrator/AppData/Local/Temp/jianying-fu` | success |
| draft filter remove | ➡️ 需真实前置产物 | 2 | `filter remove --ref local://func-test-1010-184835 --seg-id 1044EEC8-615A-4089-8CA7-D28007A9F7BD` | gen_patch: invalid action: draft filter remove target 1044EEC8-615A-4089-8CA7-D28007A9F7BD has type 'segment_video', exp |
| draft filter update | ➡️ 需真实前置产物 | 2 | `filter update --ref local://func-test-1010-184835 --seg-id 1044EEC8-615A-4089-8CA7-D28007A9F7BD --intensity 0` | gen_patch: invalid action: draft filter update target 1044EEC8-615A-4089-8CA7-D28007A9F7BD has type 'segment_video', exp |
| draft effect add | ⚠️ 官方参数/用法拒绝 | 2 | `effect add --ref local://func-test-1010-184835 --resource vimo://7618532181840973080 --type video_effect --start 0s --du` | cli parse error: ValidationError: MotionGraph-only options require `--type motiongraph` |
| draft effect remove | ➡️ 需真实前置产物 | 2 | `effect remove --ref local://func-test-1010-184835 --seg-id 1044EEC8-615A-4089-8CA7-D28007A9F7BD` | gen_patch: invalid action: draft effect remove target 1044EEC8-615A-4089-8CA7-D28007A9F7BD has type 'segment_video', exp |
| draft effect generate | ⚠️ 官方业务拒绝 | 1 | `effect generate --ref local://func-test-1010-184835 --dir C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\o` | motiongraph: upstream operation failed: submit stage failed: Lumi HTTP request failed, status=404, body=<html> <head><t |
| draft adjust add | ✅ 成功 | 0 | `adjust add --brightness 0.1 --ref local://func-test-1010-184835 --start 0s --duration 1s` | success |
| draft adjust remove | ➡️ 需真实前置产物 | 2 | `adjust remove --ref local://func-test-1010-184835 --seg-id 1044EEC8-615A-4089-8CA7-D28007A9F7BD` | gen_patch: invalid action: draft adjust remove target 1044EEC8-615A-4089-8CA7-D28007A9F7BD has type 'segment_video', exp |
| draft subtitle add | ✅ 成功 | 0 | `subtitle add --ref local://func-test-1010-184835 --content 功能测试 --start 0s --duration 1s` | success |
| draft subtitle remove | ✅ 成功 | 0 | `subtitle remove --ref local://func-test-1010-184835 --seg-id C421001B-6650-4C9F-9496-CE34BCBB677F` | success |
| draft subtitle recognize | ✅ 成功 | 0 | `subtitle recognize --ref local://func-test-1010-184835 --seg-id C421001B-6650-4C9F-9496-CE34BCBB677F --language zh --mod` | success |
| draft lyrics add | ✅ 成功 | 0 | `lyrics add --ref local://func-test-1010-184835 --content 功能测试 --start 0s --duration 1s` | success |
| draft lyrics remove | ✅ 成功 | 0 | `lyrics remove --ref local://func-test-1010-184835 --seg-id C421001B-6650-4C9F-9496-CE34BCBB677F` | success |
| draft lyrics recognize | ✅ 成功 | 0 | `lyrics recognize --ref local://func-test-1010-184835 --seg-id C421001B-6650-4C9F-9496-CE34BCBB677F --language zh --mode ` | success |
| draft keyframe add | ⚠️ 官方参数/用法拒绝 | 2 | `keyframe add --ref local://func-test-1010-184835 --seg-id 1044EEC8-615A-4089-8CA7-D28007A9F7BD --animated-property opaci` | cli parse error: ValidationError: draft keyframe add --curve-type expects a non-negative integer draft enum |
| draft keyframe update | ➡️ 需真实前置产物 | 2 | `keyframe update --ref local://func-test-1010-184835 --seg-id 1044EEC8-615A-4089-8CA7-D28007A9F7BD --animated-property op` | cli parse error: ValidationError: draft keyframe update requires exactly one of `--value` or `--values` |
| draft keyframe remove | ➡️ 需真实前置产物 | 2 | `keyframe remove --ref local://func-test-1010-184835 --seg-id 1044EEC8-615A-4089-8CA7-D28007A9F7BD --animated-property op` | cli parse error: ValidationError: draft keyframe remove requires exactly one of `--time/--times`, `--indexes`, `--timeli |
| draft blueprint init | ✅ 成功 | 0 | `blueprint init --workspace C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\workspace --protocol xmldraft` | success |
| draft blueprint sync | ✅ 成功 | 0 | `blueprint sync --workspace C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\workspace --ref local://func-tes` | success |
| draft blueprint apply | ✅ 成功 | 0 | `blueprint apply --workspace C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\workspace --ref local://func-te` | success |
| draft blueprint resource | ⚠️ 官方参数/用法拒绝 | 2 | `blueprint resource --workspace C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\workspace` | cli parse error: RequiredError: exactly one of --search, --import, --update, or --sync is required |
| material search | ✅ 成功 | 0 | `search --type text --prompt 花` | success |
| material download | 🔐 需要登录 | 1 | `download --type text --resource-id vimo://7575784012703190297 --resource-dir C:\Users\Administrator\AppData\Local\Temp\j` | material command failed in resource_pool: resource_pool err_code=-7002, err_msg=request failed: download failed, code=-4 |
| material query | ✅ 成功 | 0 | `query --resource-id vimo://7575784012703190297 --type text` | success |
| material topic | ⚠️ 官方业务拒绝 | 1 | `topic --type text --template-id func-test` | material command failed in resource_pool: resource_pool err_code=-7007, err_msg=unsupported material type: unsupported m |
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
| media understand | ⚠️ 官方业务拒绝 | 1 | `understand --path C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\media\sample.mp4 --prompt 花 --segment-id ` | media: processing failed: invalid request stage=invalid_client_source request_logid=20261010185635B7D41F2003C02383D60D b |
| lint command | ➡️ 需真实前置产物 | 2 | `command --acceptance-type all --acceptance-level L0 --output C:\Users\Administrator\AppData\Local\Temp\jianying-func-tes` | invalid argument: repo root does not look like lyra-cli: C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\ |
| lint media | ✅ 成功 | 0 | `media --input C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\media\sample.mp4 --expected-kind auto --expec` | success |
| lint algorithm-effect | ✅ 成功 | 2 | `algorithm-effect --algorithm func-test --comparison-mode paired_artifact --candidate C:\Users\Administrator\AppData\Loca` | success |
| lint draft | ✅ 成功 | 0 | `draft --ref local://func-test-1010-184835 --spatial-overlap-severity warning --occlusion-severity warning --output C:\Us` | success |
| lint trace | ✅ 成功 | 1 | `trace --trace C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\media\sample.mp4 --target-policy stable --mat` | success |
| upgrade | 🚧 官方未实现 | 2 | `` | command is not implemented yet (work in progress) |
| draft project duplicate | ✅ 成功 | 0 | `project duplicate --ref local://func-test-1010-184835 --to local://func-test-1010-184835-copy` | success |
| draft project import | ⚠️ 官方业务拒绝 | 1 | `project import --ref local://func-test-1010-184835` | draft already exists: local://func-test-1010-184835 already lives in the default workspace |
| draft history undo | 🚧 仅内嵌库支持 | 2 | `history undo --ref local://func-test-1010-184835` | draft history undo / redo is only available when lyra-cli is embedded as a client library; the standalone executable doe |
| draft history redo | 🚧 仅内嵌库支持 | 2 | `history redo --ref local://func-test-1010-184835` | draft history undo / redo is only available when lyra-cli is embedded as a client library; the standalone executable doe |
| draft deform apply | ✅ 成功 | 0 | `deform apply --scale 1 --ref local://func-test-1010-184835 --mode stretch --deform-seg-id 1044EEC8-615A-4089-8CA7-D28007` | success |
| draft sticker translate | ✅ 成功 | 0 | `sticker translate --ref local://func-test-1010-184835 --seg-id CEC3C33C-7BB6-4DEC-A627-1321E4F4BAB9` | success |
| draft text-template translate | ➡️ 需真实前置产物 | 2 | `text-template translate --ref local://func-test-1010-184835 --seg-id C421001B-6650-4C9F-9496-CE34BCBB677F` | gen_patch: invalid action: draft text-template translate target C421001B-6650-4C9F-9496-CE34BCBB677F has type 'segment_t |
| draft text-template add | ➡️ 需真实前置产物 | 2 | `text-template add --ref local://func-test-1010-184835 --resource local:///C:/Users/Administrator/AppData/Local/Temp/jian` | gen_patch: invalid action: gen_patch --add add_text_template does not support local text template resources |
| draft text-template replace | ➡️ 需真实前置产物 | 2 | `text-template replace --ref local://func-test-1010-184835 --seg-id C421001B-6650-4C9F-9496-CE34BCBB677F --resource local` | gen_patch: invalid action: draft text-template replace target C421001B-6650-4C9F-9496-CE34BCBB677F has type 'segment_tex |
| draft text-template remove | ➡️ 需真实前置产物 | 2 | `text-template remove --ref local://func-test-1010-184835 --seg-id C421001B-6650-4C9F-9496-CE34BCBB677F` | gen_patch: invalid action: draft text-template remove target C421001B-6650-4C9F-9496-CE34BCBB677F has type 'segment_text |
| draft segment time-range | ⚠️ 官方参数/用法拒绝 | 2 | `segment time-range --ref local://func-test-1010-184835 --seg-id 1044EEC8-615A-4089-8CA7-D28007A9F7BD --out C:\Users\Admi` | cli parse error: ValidationError: draft segment time-range --duration cannot be combined with endpoint or endpoint-offse |
| draft segment add | ✅ 成功 | 0 | `segment add --ref local://func-test-1010-184835 --type text --resource local:///C:/Users/Administrator/AppData/Local/Tem` | success |
| draft compound-clip break-apart | ⚠️ 官方业务拒绝 | 1 | `compound-clip break-apart --ref local://func-test-1010-184835 --seg-id 1044EEC8-615A-4089-8CA7-D28007A9F7BD` | patch apply failed: break_combination cannot find stored child draft payload |
| draft blueprint plan | ✅ 成功 | 0 | `blueprint plan --workspace C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\workspace` | success |
| draft blueprint cancel | 🚧 仅内嵌库支持 | 2 | `blueprint cancel` | draft blueprint cancel is only available when lyra-cli is embedded as a client library; the standalone executable does n |
| draft blueprint commerce | ✅ 成功 | 0 | `blueprint commerce --workspace C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\workspace` | success |
| draft blueprint patch | ⚠️ 官方业务拒绝 | 1 | `blueprint patch --workspace C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\workspace --patch-file C:\Users` | internal error: process terminated by unhandled Windows exception 0xE06D7363 |
| draft video transition add | ✅ 成功 | 0 | `video transition add --ref local://func-test-1010-184835 --seg-id 1044EEC8-615A-4089-8CA7-D28007A9F7BD --resource local:` | success |
| draft video transition update | ✅ 成功 | 0 | `video transition update --ref local://func-test-1010-184835 --seg-id 1044EEC8-615A-4089-8CA7-D28007A9F7BD --resource loc` | success |
| draft video transition remove | ✅ 成功 | 0 | `video transition remove --ref local://func-test-1010-184835 --seg-id 1044EEC8-615A-4089-8CA7-D28007A9F7BD` | success |
| draft video filter add | ✅ 成功 | 0 | `video filter add --ref local://func-test-1010-184835 --seg-id 1044EEC8-615A-4089-8CA7-D28007A9F7BD --resource vimo://749` | success |
| draft video filter update | ✅ 成功 | 0 | `video filter update --ref local://func-test-1010-184835 --seg-id 1044EEC8-615A-4089-8CA7-D28007A9F7BD --intensity 0` | success |
| draft video filter remove | ✅ 成功 | 0 | `video filter remove --ref local://func-test-1010-184835 --seg-id 1044EEC8-615A-4089-8CA7-D28007A9F7BD` | success |
| draft video effect add | ✅ 成功 | 0 | `video effect add --ref local://func-test-1010-184835 --seg-id 1044EEC8-615A-4089-8CA7-D28007A9F7BD --resource vimo://761` | success |
| draft video effect update | ✅ 成功 | 0 | `video effect update --ref local://func-test-1010-184835 --seg-id 1044EEC8-615A-4089-8CA7-D28007A9F7BD --params-json {"op` | success |
| draft video effect remove | ✅ 成功 | 0 | `video effect remove --ref local://func-test-1010-184835 --seg-id 1044EEC8-615A-4089-8CA7-D28007A9F7BD` | success |
| draft video mask add | ✅ 成功 | 0 | `video mask add --ref local://func-test-1010-184835 --seg-id 1044EEC8-615A-4089-8CA7-D28007A9F7BD --resource vimo://76185` | success |
| draft video mask update | ⚠️ 官方参数/用法拒绝 | 2 | `video mask update --ref local://func-test-1010-184835 --seg-id 1044EEC8-615A-4089-8CA7-D28007A9F7BD` | gen_patch: invalid action: gen_patch --update has no registered handler for field(s):  |
| draft video mask remove | ✅ 成功 | 0 | `video mask remove --ref local://func-test-1010-184835 --seg-id 1044EEC8-615A-4089-8CA7-D28007A9F7BD` | success |
| draft video animation add | ✅ 成功 | 0 | `video animation add --ref local://func-test-1010-184835 --seg-id 1044EEC8-615A-4089-8CA7-D28007A9F7BD --resource local:/` | success |
| draft video animation update | ➡️ 需真实前置产物 | 2 | `video animation update --ref local://func-test-1010-184835 --seg-id 1044EEC8-615A-4089-8CA7-D28007A9F7BD --animation-typ` | gen_patch: invalid action: gen_patch --update animation found no existing 'func-test' animation on target; use --add pro |
| draft video animation remove | ✅ 成功 | 0 | `video animation remove --ref local://func-test-1010-184835 --seg-id 1044EEC8-615A-4089-8CA7-D28007A9F7BD` | success |
| draft video beat add | ✅ 成功 | 0 | `video beat add --ref local://func-test-1010-184835 --seg-id 1044EEC8-615A-4089-8CA7-D28007A9F7BD --times 1s` | success |
| draft video beat remove | ✅ 成功 | 0 | `video beat remove --ref local://func-test-1010-184835 --seg-id 1044EEC8-615A-4089-8CA7-D28007A9F7BD` | success |
| draft video audio-effect add | ✅ 成功 | 0 | `video audio-effect add --ref local://func-test-1010-184835 --seg-id 1044EEC8-615A-4089-8CA7-D28007A9F7BD --resource vimo` | success |
| draft video color smart-color | ✅ 成功 | 0 | `video color smart-color --ref local://func-test-1010-184835 --seg-id 1044EEC8-615A-4089-8CA7-D28007A9F7BD --resource loc` | success |
| draft video color correct | ✅ 成功 | 0 | `video color correct --ref local://func-test-1010-184835 --seg-id 1044EEC8-615A-4089-8CA7-D28007A9F7BD --resource local:/` | success |
| draft text effect update | ✅ 成功 | 0 | `text effect update --ref local://func-test-1010-184835 --seg-id C421001B-6650-4C9F-9496-CE34BCBB677F --resource vimo://7` | success |
| draft text effect add | ✅ 成功 | 0 | `text effect add --ref local://func-test-1010-184835 --content 功能测试 --resource vimo://7618532181840973080 --name func-tes` | success |
| draft text animation set | ✅ 成功 | 0 | `text animation set --ref local://func-test-1010-184835 --seg-id C421001B-6650-4C9F-9496-CE34BCBB677F --resource local://` | success |
| draft text animation remove | ✅ 成功 | 0 | `text animation remove --ref local://func-test-1010-184835 --seg-id C421001B-6650-4C9F-9496-CE34BCBB677F` | success |
| draft subtitle template add | ➡️ 需真实前置产物 | 2 | `subtitle template add --ref local://func-test-1010-184835 --resource local:///C:/Users/Administrator/AppData/Local/Temp/` | gen_patch: invalid action: gen_patch --add add_subtitle_template does not support local text template resources |
| draft subtitle template replace | ➡️ 需真实前置产物 | 2 | `subtitle template replace --ref local://func-test-1010-184835 --seg-id C421001B-6650-4C9F-9496-CE34BCBB677F --resource l` | gen_patch: invalid action: draft subtitle template replace target C421001B-6650-4C9F-9496-CE34BCBB677F has type 'segment |
| draft lyrics animation add | ➡️ 需真实前置产物 | 2 | `lyrics animation add --ref local://func-test-1010-184835 --resource local:///C:/Users/Administrator/AppData/Local/Temp/j` | gen_patch: invalid action: gen_patch --add lyric_animation does not support local lyric animation resources |
| draft lyrics animation update | ➡️ 需真实前置产物 | 2 | `lyrics animation update --ref local://func-test-1010-184835 --seg-id C421001B-6650-4C9F-9496-CE34BCBB677F --resource loc` | gen_patch: invalid action: gen_patch --update lyric_animation does not support local lyric animation resources |
| draft lyrics animation replace | ➡️ 需真实前置产物 | 2 | `lyrics animation replace --ref local://func-test-1010-184835 --seg-id C421001B-6650-4C9F-9496-CE34BCBB677F --resource lo` | gen_patch: invalid action: gen_patch --update lyric_animation does not support local lyric animation resources |
| draft keyframe curve set | ⚠️ 官方参数/用法拒绝 | 2 | `keyframe curve set --ref local://func-test-1010-184835 --seg-id 1044EEC8-615A-4089-8CA7-D28007A9F7BD --animated-property` | cli parse error: ValidationError: --at: expects an explicit unit: us, ms, s, or min; bare numbers and `m` are not accept |
| material motiongraph build-runtime-manifest | ⚠️ 官方业务拒绝 | 1 | `motiongraph build-runtime-manifest --package func-test --output-dir C:\Users\Administrator\AppData\Local\Temp\jianying-f` | motiongraph: invalid provider response: package not found: func-test |
| material motiongraph track-subject-mask | ➡️ 需真实前置产物 | 2 | `motiongraph track-subject-mask --input C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\media\sample.mp4 --r` | motiongraph: invalid argument: track-subject-mask requires exactly one of --target-object-desc or --seed-mask-rle-json |
| material motiongraph encode-subject-alpha | ➡️ 需真实前置产物 | 2 | `motiongraph encode-subject-alpha --mask-dir func-test --output-dir C:\Users\Administrator\AppData\Local\Temp\jianying-fu` | motiongraph: invalid argument: mask dir is not a directory: func-test |
| material motiongraph track-plane-quad | ⚠️ 官方参数/用法拒绝 | 2 | `motiongraph track-plane-quad --ref local://func-test-1010-184835 --target-seg-id func-test --output-dir C:\Users\Adminis` | motiongraph: invalid argument: direct track-plane-quad requires --plane-desc or a legacy --object-desc when --initial-qu |
| media aigc text2image | ✅ 成功 | 0 | `aigc text2image --prompt 花 --download-format png` | success |
| media aigc image2image | ⚠️ 官方业务拒绝 | 1 | `aigc image2image --images func-test --prompt 花 --download-format png` | media: input file not found: input file does not exist: func-test |
| media aigc text2video | ✅ 成功 | 0 | `aigc text2video --prompt 花 --duration 1 --download-format png` | success |
| media aigc image2video | ⚠️ 官方参数/用法拒绝 | 2 | `aigc image2video --prompt 花 --duration 1 --download-format png` | media AIGC: invalid request: image2video requires --first-image/--image or --reference-image |
| media aigc query | ⚠️ 官方参数/用法拒绝 | 2 | `aigc query --submit-id func-test --download-format png` | media AIGC: invalid submit_id: invalid media AIGC submit_id |
| auth login | ⏭️ 有意跳过（破坏会话/需人工交互） | None | `` | 交互式登录，必须由用户在浏览器完成授权 |
| auth relogin | ⏭️ 有意跳过（破坏会话/需人工交互） | None | `` | 交互式重新登录，必须由用户授权 |
| auth qrcode | ⏭️ 有意跳过（破坏会话/需人工交互） | None | `` | 交互式扫码登录，必须由用户操作 |
| auth status | ✅ 成功 | 0 | `status` | success |
| auth me | ✅ 成功 | 0 | `me` | success |
| auth check | ✅ 成功 | 0 | `check` | success |
| auth logout | ⏭️ 有意跳过（破坏会话/需人工交互） | None | `` | 会真实登出账号，破坏同批其他需要登录的命令 |
| draft project version upgrade | 🚧 官方未实现 | 2 | `project version upgrade --ref local://func-test-1010-184835` | command is not implemented yet (work in progress): draft project version upgrade is not implemented yet |
| draft project version downgrade | ✅ 成功 | 0 | `project version downgrade --ref local://func-test-1010-184835` | success |
| draft timeline segment copy | ⚠️ 官方业务拒绝 | 1 | `timeline segment copy --ref local://func-test-1010-184835 --seg-id 1044EEC8-615A-4089-8CA7-D28007A9F7BD --source-timelin` | patch apply failed: {"lyra_err_code":109,"lyra_err_msg":"transfer_segments source or target draft is unavailable"} |
| draft timeline segment move | ⚠️ 官方业务拒绝 | 1 | `timeline segment move --ref local://func-test-1010-184835 --seg-id 1044EEC8-615A-4089-8CA7-D28007A9F7BD --source-timelin` | patch apply failed: {"lyra_err_code":109,"lyra_err_msg":"transfer_segments source or target draft is unavailable"} |
| draft algo object-matting-track | ➡️ 需真实前置产物 | 2 | `algo object-matting-track --ref local://func-test-1010-184835 --seg-id 1044EEC8-615A-4089-8CA7-D28007A9F7BD --segment-ti` | cli parse error: ValidationError: object-matting-track requires exactly one of --seed-mask-rle-json or --target-object-d |
