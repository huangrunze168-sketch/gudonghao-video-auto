# lyra-cli 真实功能测试报告

- 清单命令数：195

## 执行层

| 状态 | 数量 |
| --- | --- |
| ✅ 成功 | 87 |
| ➡️ 需真实前置产物 | 31 |
| 🔐 需要登录 | 31 |
| ⚠️ 官方参数/用法拒绝 | 22 |
| ⚠️ 官方业务拒绝 | 14 |
| 🚧 官方未实现 | 4 |
| 🚧 仅内嵌库支持 | 3 |
| ⏱️ 超时 | 2 |
| 📦 本机缺模型 | 1 |

| 命令 | 状态 | exit | 参数 | 官方消息 |
| --- | --- | --- | --- | --- |
| draft edit | ✅ 成功 | 0 | `edit --ref local://func-test-1010-160233 --op split --target seg_id=A5BDFD04-A7EB-49FF-B5C9-141FC8B596AE --params points` | success |
| draft config | ✅ 成功 | 0 | `config --ref local://func-test-1010-160233 --ratio 16:9` | success |
| draft project create | ✅ 成功 | 0 | `project create --ref local://func-test-1010-160233 --dir C:\Users\Administrator\AppData\Local\JianyingPro\User Data\Proj` | success |
| draft project list | ✅ 成功 | 0 | `project list` | success |
| draft project focus | ✅ 成功 | 0 | `project focus --ref local://func-test-1010-160233` | success |
| draft project delete | ✅ 成功 | 0 | `project delete --ref local://func-test-1010-160233` | success |
| draft cover set | ✅ 成功 | 0 | `cover set --ref local://func-test-1010-160233 --image C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\media` | success |
| draft cover clear | ✅ 成功 | 0 | `cover clear --ref local://func-test-1010-160233` | success |
| draft extract summary | ✅ 成功 | 0 | `extract summary --ref local://func-test-1010-160233 --dir C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\o` | success |
| draft template add | ⚠️ 官方业务拒绝 | 1 | `template add --ref local://func-test-1010-160233 --resource local:///C:/Users/Administrator/AppData/Local/Temp/jianying-` | patch apply failed: template parse failed: code=-10011, msg=unzip failed |
| draft template publish | ✅ 成功 | 0 | `template publish --ref local://func-test-1010-160233 --dir C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\` | success |
| draft template render | ➡️ 需真实前置产物 | 2 | `template render --config C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\media\sample.mp4 --ref local://fun` | invalid argument: draft template render requires a fresh --ref whose workspace does not already exist |
| draft template slots | ✅ 成功 | 0 | `template slots --ref local://func-test-1010-160233 --template-seg-id D2EE9183-D094-4F40-9F37-9EAA0578F9E5` | success |
| draft template replace | ➡️ 需真实前置产物 | 2 | `template replace --ref local://func-test-1010-160233 --template-seg-id D2EE9183-D094-4F40-9F37-9EAA0578F9E5 --slot func-` | invalid argument: slot not found: func-test |
| draft algo query | ➡️ 需真实前置产物 | 2 | `algo query --task-id func-test` | invalid video-tracking task id: func-test |
| draft algo wait | ➡️ 需真实前置产物 | 2 | `algo wait --task-id func-test` | invalid video-tracking task id: func-test |
| draft algo quality-enhance | 🔐 需要登录 | 1 | `algo quality-enhance --ref local://func-test-1010-160233 --seg-id D2EE9183-D094-4F40-9F37-9EAA0578F9E5 --from 1s` | auth credential is missing: not logged in. Please log in and retry |
| draft algo upscale-resolution | 🔐 需要登录 | 1 | `algo upscale-resolution --ref local://func-test-1010-160233 --seg-id D2EE9183-D094-4F40-9F37-9EAA0578F9E5 --mode auto --` | auth credential is missing: not logged in. Please log in and retry |
| draft algo ai-frame-interpolation | 🔐 需要登录 | 1 | `algo ai-frame-interpolation --ref local://func-test-1010-160233 --seg-id D2EE9183-D094-4F40-9F37-9EAA0578F9E5 --fps 30` | auth credential is missing: not logged in. Please log in and retry |
| draft algo ai-matting | 🔐 需要登录 | 1 | `algo ai-matting --ref local://func-test-1010-160233 --seg-id D2EE9183-D094-4F40-9F37-9EAA0578F9E5 --workspace C:\Users\A` | auth credential is missing: not logged in. Please log in and retry |
| draft algo ai-transition | 🔐 需要登录 | 1 | `algo ai-transition --ref local://func-test-1010-160233 --after-seg-id D2EE9183-D094-4F40-9F37-9EAA0578F9E5 --resource lo` | auth credential is missing: not logged in. Please log in and retry |
| draft algo custom-matting | 🔐 需要登录 | 1 | `algo custom-matting --ref local://func-test-1010-160233 --seg-id D2EE9183-D094-4F40-9F37-9EAA0578F9E5 --workspace C:\Use` | auth credential is missing: not logged in. Please log in and retry |
| draft algo chroma-color-matting | 🔐 需要登录 | 1 | `algo chroma-color-matting --ref local://func-test-1010-160233 --seg-id D2EE9183-D094-4F40-9F37-9EAA0578F9E5 --path C:\Us` | auth credential is missing: not logged in. Please log in and retry |
| draft algo video-tracking | ⚠️ 官方业务拒绝 | 1 | `algo video-tracking --ref local://func-test-1010-160233 --seg-id D2EE9183-D094-4F40-9F37-9EAA0578F9E5 --source-seg-id D2` | internal error: process terminated by unhandled Windows exception 0xE06D7363 |
| draft algo sound-separation | 🔐 需要登录 | 1 | `algo sound-separation --ref local://func-test-1010-160233 --seg-id D2EE9183-D094-4F40-9F37-9EAA0578F9E5 --mode auto --ou` | auth credential is missing: not logged in. Please log in and retry |
| draft algo loudness-normalize | 🔐 需要登录 | 1 | `algo loudness-normalize --ref local://func-test-1010-160233 --seg-id D2EE9183-D094-4F40-9F37-9EAA0578F9E5` | auth credential is missing: not logged in. Please log in and retry |
| draft algo denoise | 🔐 需要登录 | 1 | `algo denoise --ref local://func-test-1010-160233 --seg-id D2EE9183-D094-4F40-9F37-9EAA0578F9E5 --path C:\Users\Administr` | auth credential is missing: not logged in. Please log in and retry |
| draft algo voice-enhance | 🔐 需要登录 | 1 | `algo voice-enhance --ref local://func-test-1010-160233 --seg-id D2EE9183-D094-4F40-9F37-9EAA0578F9E5` | auth credential is missing: not logged in. Please log in and retry |
| draft algo video-stabilize | 🔐 需要登录 | 1 | `algo video-stabilize --ref local://func-test-1010-160233 --seg-id D2EE9183-D094-4F40-9F37-9EAA0578F9E5` | auth credential is missing: not logged in. Please log in and retry |
| draft algo tts | 🔐 需要登录 | 1 | `algo tts --ref local://func-test-1010-160233 --seg-id D2EE9183-D094-4F40-9F37-9EAA0578F9E5 --text 功能测试 --speed 1.0 --spe` | auth credential is missing: not logged in. Please log in and retry |
| draft algo subtitle-recognize | 🔐 需要登录 | 1 | `algo subtitle-recognize --ref local://func-test-1010-160233 --seg-id D2EE9183-D094-4F40-9F37-9EAA0578F9E5 --language zh ` | auth credential is missing: not logged in. Please log in and retry |
| draft algo text-add-tone | 🔐 需要登录 | 1 | `algo text-add-tone --ref local://func-test-1010-160233 --seg-id D2EE9183-D094-4F40-9F37-9EAA0578F9E5 --text 功能测试 --speed` | auth credential is missing: not logged in. Please log in and retry |
| draft algo music-beats | 🔐 需要登录 | 1 | `algo music-beats --ref local://func-test-1010-160233 --seg-id D2EE9183-D094-4F40-9F37-9EAA0578F9E5 --mode auto --output-` | auth credential is missing: not logged in. Please log in and retry |
| draft algo material-understand | 🔐 需要登录 | 1 | `algo material-understand --ref local://func-test-1010-160233 --seg-id D2EE9183-D094-4F40-9F37-9EAA0578F9E5 --prompt 花` | auth credential is missing: not logged in. Please log in and retry |
| draft algo subtitle-keywords | 🔐 需要登录 | 1 | `algo subtitle-keywords --ref local://func-test-1010-160233 --seg-id D2EE9183-D094-4F40-9F37-9EAA0578F9E5 --language zh` | auth credential is missing: not logged in. Please log in and retry |
| draft video crop | ✅ 成功 | 0 | `video crop --ref local://func-test-1010-160233 --seg-id D2EE9183-D094-4F40-9F37-9EAA0578F9E5` | success |
| draft video speed | ✅ 成功 | 0 | `video speed --ref local://func-test-1010-160233 --seg-id D2EE9183-D094-4F40-9F37-9EAA0578F9E5 --speed 1.0` | success |
| draft video stabilize | 🔐 需要登录 | 1 | `video stabilize --ref local://func-test-1010-160233 --seg-id D2EE9183-D094-4F40-9F37-9EAA0578F9E5` | auth credential is missing: not logged in. Please log in and retry |
| draft video scale | ✅ 成功 | 0 | `video scale --ref local://func-test-1010-160233 --seg-id D2EE9183-D094-4F40-9F37-9EAA0578F9E5` | success |
| draft video rotate | ✅ 成功 | 0 | `video rotate --ref local://func-test-1010-160233 --seg-id D2EE9183-D094-4F40-9F37-9EAA0578F9E5 --rotation 0` | success |
| draft video translate | ✅ 成功 | 0 | `video translate --ref local://func-test-1010-160233 --seg-id D2EE9183-D094-4F40-9F37-9EAA0578F9E5` | success |
| draft video alpha | ✅ 成功 | 0 | `video alpha --ref local://func-test-1010-160233 --seg-id D2EE9183-D094-4F40-9F37-9EAA0578F9E5 --alpha 1` | success |
| draft video flip | ✅ 成功 | 0 | `video flip --ref local://func-test-1010-160233 --seg-id D2EE9183-D094-4F40-9F37-9EAA0578F9E5` | success |
| draft video layer | ✅ 成功 | 0 | `video layer --ref local://func-test-1010-160233 --seg-id D2EE9183-D094-4F40-9F37-9EAA0578F9E5 --z-order 0` | success |
| draft video volume | ⚠️ 官方参数/用法拒绝 | 2 | `video volume --ref local://func-test-1010-160233 --seg-id D2EE9183-D094-4F40-9F37-9EAA0578F9E5` | gen_patch: invalid action: gen_patch --update has no registered handler for field(s):  |
| draft video freeze | ✅ 成功 | 0 | `video freeze --ref local://func-test-1010-160233 --seg-id D2EE9183-D094-4F40-9F37-9EAA0578F9E5 --time 1s --duration 1s` | success |
| draft video add | ✅ 成功 | 0 | `video add --ref local://func-test-1010-160233 --resource local:///C:/Users/Administrator/AppData/Local/Temp/jianying-fun` | success |
| draft video remove | ✅ 成功 | 0 | `video remove --ref local://func-test-1010-160233 --seg-id D2EE9183-D094-4F40-9F37-9EAA0578F9E5` | success |
| draft video adjust | ⚠️ 官方参数/用法拒绝 | 2 | `video adjust --ref local://func-test-1010-160233 --seg-id D2EE9183-D094-4F40-9F37-9EAA0578F9E5 --resource local:///C:/Us` | gen_patch: invalid action: gen_patch --update has no registered handler for field(s): resource |
| draft video background | ⚠️ 官方参数/用法拒绝 | 2 | `video background --ref local://func-test-1010-160233 --seg-id D2EE9183-D094-4F40-9F37-9EAA0578F9E5 --type text --image C` | gen_patch: invalid action: gen_patch --update canvas: type must be color, blur, image, canvas_color, canvas_blur, or can |
| draft video matting-stroke | ⚠️ 官方参数/用法拒绝 | 2 | `video matting-stroke --enable --ref local://func-test-1010-160233 --seg-id D2EE9183-D094-4F40-9F37-9EAA0578F9E5 --resour` | gen_patch: invalid action: gen_patch --update matting_stroke: invalid resource URI 'local:///C:/Users/Administrator/AppD |
| draft video mix-mode | ⚠️ 官方参数/用法拒绝 | 2 | `video mix-mode --enable --ref local://func-test-1010-160233 --seg-id D2EE9183-D094-4F40-9F37-9EAA0578F9E5 --resource loc` | gen_patch: invalid action: gen_patch --update mix_mode: invalid 'resource' URI 'local:///C:/Users/Administrator/AppData/ |
| draft video face-beauty | ⚠️ 官方参数/用法拒绝 | 2 | `video face-beauty --ref local://func-test-1010-160233 --seg-id D2EE9183-D094-4F40-9F37-9EAA0578F9E5 --resource local:///` | gen_patch: invalid action: gen_patch --update has no registered handler for field(s): resource |
| draft video extract-frames | ✅ 成功 | 0 | `video extract-frames --ref local://func-test-1010-160233 --seg-id D2EE9183-D094-4F40-9F37-9EAA0578F9E5 --output-path C:\` | success |
| draft video extract-music | ➡️ 需真实前置产物 | 2 | `video extract-music --ref local://func-test-1010-160233 --seg-id D2EE9183-D094-4F40-9F37-9EAA0578F9E5 --resource local:/` | gen_patch: invalid action: err_code=-100520: gen_patch --op extract_music: extract_music target mode does not accept 're |
| draft sticker add | ✅ 成功 | 0 | `sticker add --ref local://func-test-1010-160233 --resource local:///C:/Users/Administrator/AppData/Local/Temp/jianying-f` | success |
| draft sticker remove | ➡️ 需真实前置产物 | 2 | `sticker remove --ref local://func-test-1010-160233 --seg-id D2EE9183-D094-4F40-9F37-9EAA0578F9E5` | gen_patch: invalid action: draft sticker remove target D2EE9183-D094-4F40-9F37-9EAA0578F9E5 has type 'segment_video', ex |
| draft text translate | ✅ 成功 | 0 | `text translate --ref local://func-test-1010-160233 --seg-id 19A4F135-6433-410E-9758-CC1C463FDCB3` | success |
| draft text content | ✅ 成功 | 0 | `text content --ref local://func-test-1010-160233 --seg-id 19A4F135-6433-410E-9758-CC1C463FDCB3 --content 功能测试` | success |
| draft text wrap-width | ⚠️ 官方参数/用法拒绝 | 2 | `text wrap-width --ref local://func-test-1010-160233 --seg-id 19A4F135-6433-410E-9758-CC1C463FDCB3 --width 640` | cli parse error: ValidationError: --width: value must be within [0,1] after normalization |
| draft text add | ✅ 成功 | 0 | `text add --ref local://func-test-1010-160233 --content 功能测试 --start 0s --duration 1s` | success |
| draft text remove | ✅ 成功 | 0 | `text remove --ref local://func-test-1010-160233 --seg-id 19A4F135-6433-410E-9758-CC1C463FDCB3` | success |
| draft text style | ⚠️ 官方参数/用法拒绝 | 2 | `text style --ref local://func-test-1010-160233 --seg-id 19A4F135-6433-410E-9758-CC1C463FDCB3` | gen_patch: invalid action: gen_patch --update has no registered handler for field(s):  |
| draft audio volume | ⚠️ 官方参数/用法拒绝 | 2 | `audio volume --ref local://func-test-1010-160233 --seg-id 08581477-768E-4D01-ABB0-60732D396F39` | gen_patch: invalid action: gen_patch --update has no registered handler for field(s):  |
| draft audio fade | ⚠️ 官方参数/用法拒绝 | 2 | `audio fade --ref local://func-test-1010-160233 --seg-id 08581477-768E-4D01-ABB0-60732D396F39 --out 1s --type text` | gen_patch: invalid action: gen_patch --update audio_fade: fade_type must be one of off/fade-in/fade-out/both (got 'text' |
| draft audio speed | ✅ 成功 | 0 | `audio speed --ref local://func-test-1010-160233 --seg-id 08581477-768E-4D01-ABB0-60732D396F39 --speed 1.0` | success |
| draft audio add | ✅ 成功 | 0 | `audio add --ref local://func-test-1010-160233 --resource local:///C:/Users/Administrator/AppData/Local/Temp/jianying-fun` | success |
| draft audio remove | ✅ 成功 | 0 | `audio remove --ref local://func-test-1010-160233 --seg-id 08581477-768E-4D01-ABB0-60732D396F39` | success |
| draft segment remove | ✅ 成功 | 0 | `segment remove --ref local://func-test-1010-160233 --seg-id D2EE9183-D094-4F40-9F37-9EAA0578F9E5` | success |
| draft segment split | ✅ 成功 | 0 | `segment split --ref local://func-test-1010-160233 --seg-id D2EE9183-D094-4F40-9F37-9EAA0578F9E5 --points 1s` | success |
| draft segment duplicate | ✅ 成功 | 0 | `segment duplicate --ref local://func-test-1010-160233 --seg-id D2EE9183-D094-4F40-9F37-9EAA0578F9E5 --start 0s` | success |
| draft segment move | ⚠️ 官方业务拒绝 | 1 | `segment move --ref local://func-test-1010-160233 --seg-id D2EE9183-D094-4F40-9F37-9EAA0578F9E5 --start 0s` | draft edit made no effective segment changes: gen_patch --move made no effective changes; target already has the request |
| draft compound-clip create | ✅ 成功 | 0 | `compound-clip create --ref local://func-test-1010-160233 --seg-id D2EE9183-D094-4F40-9F37-9EAA0578F9E5 --name func-test` | success |
| draft filter add | ✅ 成功 | 0 | `filter add --ref local://func-test-1010-160233 --resource local:///C:/Users/Administrator/AppData/Local/Temp/jianying-fu` | success |
| draft filter remove | ➡️ 需真实前置产物 | 2 | `filter remove --ref local://func-test-1010-160233 --seg-id D2EE9183-D094-4F40-9F37-9EAA0578F9E5` | gen_patch: invalid action: draft filter remove target D2EE9183-D094-4F40-9F37-9EAA0578F9E5 has type 'segment_video', exp |
| draft filter update | ➡️ 需真实前置产物 | 2 | `filter update --ref local://func-test-1010-160233 --seg-id D2EE9183-D094-4F40-9F37-9EAA0578F9E5 --intensity 0` | gen_patch: invalid action: draft filter update target D2EE9183-D094-4F40-9F37-9EAA0578F9E5 has type 'segment_video', exp |
| draft effect add | ⚠️ 官方参数/用法拒绝 | 2 | `effect add --ref local://func-test-1010-160233 --resource local:///C:/Users/Administrator/AppData/Local/Temp/jianying-fu` | cli parse error: ValidationError: MotionGraph-only options require `--type motiongraph` |
| draft effect remove | ➡️ 需真实前置产物 | 2 | `effect remove --ref local://func-test-1010-160233 --seg-id D2EE9183-D094-4F40-9F37-9EAA0578F9E5` | gen_patch: invalid action: draft effect remove target D2EE9183-D094-4F40-9F37-9EAA0578F9E5 has type 'segment_video', exp |
| draft effect generate | ⚠️ 官方业务拒绝 | 1 | `effect generate --ref local://func-test-1010-160233 --dir C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\o` | motiongraph: upstream operation failed: submit stage failed: Lumi HTTP request failed, status=404, body=<html> <head><t |
| draft adjust add | ⚠️ 官方业务拒绝 | 1 | `adjust add --brightness 0.1 --ref local://func-test-1010-160233 --start 0s --duration 1s --resource local:///C:/Users/Ad` | patch apply failed: {"lyra_err_code":102,"lyra_err_msg":"download failed, sub_code: 1006, msg: error: resource query res |
| draft adjust remove | ➡️ 需真实前置产物 | 2 | `adjust remove --ref local://func-test-1010-160233 --seg-id D2EE9183-D094-4F40-9F37-9EAA0578F9E5` | gen_patch: invalid action: draft adjust remove target D2EE9183-D094-4F40-9F37-9EAA0578F9E5 has type 'segment_video', exp |
| draft subtitle add | ✅ 成功 | 0 | `subtitle add --ref local://func-test-1010-160233 --content 功能测试 --start 0s --duration 1s` | success |
| draft subtitle remove | ✅ 成功 | 0 | `subtitle remove --ref local://func-test-1010-160233 --seg-id 19A4F135-6433-410E-9758-CC1C463FDCB3` | success |
| draft subtitle recognize | 🔐 需要登录 | 1 | `subtitle recognize --ref local://func-test-1010-160233 --seg-id 19A4F135-6433-410E-9758-CC1C463FDCB3 --language zh --mod` | auth credential is missing: not logged in. Please log in and retry |
| draft lyrics add | ✅ 成功 | 0 | `lyrics add --ref local://func-test-1010-160233 --content 功能测试 --start 0s --duration 1s` | success |
| draft lyrics remove | ✅ 成功 | 0 | `lyrics remove --ref local://func-test-1010-160233 --seg-id 19A4F135-6433-410E-9758-CC1C463FDCB3` | success |
| draft lyrics recognize | 🔐 需要登录 | 1 | `lyrics recognize --ref local://func-test-1010-160233 --seg-id 19A4F135-6433-410E-9758-CC1C463FDCB3 --language zh --mode ` | auth credential is missing: not logged in. Please log in and retry |
| draft keyframe add | ➡️ 需真实前置产物 | 2 | `keyframe add --ref local://func-test-1010-160233 --seg-id D2EE9183-D094-4F40-9F37-9EAA0578F9E5 --animated-property opaci` | cli parse error: ValidationError: draft keyframe add requires exactly one of `--animated-property` or `--keyframe-type` |
| draft keyframe update | ➡️ 需真实前置产物 | 2 | `keyframe update --ref local://func-test-1010-160233 --seg-id D2EE9183-D094-4F40-9F37-9EAA0578F9E5 --animated-property op` | cli parse error: ValidationError: draft keyframe update requires exactly one of `--animated-property` or `--keyframe-typ |
| draft keyframe remove | ➡️ 需真实前置产物 | 2 | `keyframe remove --ref local://func-test-1010-160233 --seg-id D2EE9183-D094-4F40-9F37-9EAA0578F9E5 --animated-property op` | cli parse error: ValidationError: draft keyframe remove requires exactly one of `--animated-property` or `--keyframe-typ |
| draft blueprint init | ✅ 成功 | 0 | `blueprint init --workspace C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\workspace` | success |
| draft blueprint sync | ✅ 成功 | 0 | `blueprint sync --workspace C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\workspace --ref local://func-tes` | success |
| draft blueprint apply | ✅ 成功 | 0 | `blueprint apply --workspace C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\workspace --ref local://func-te` | success |
| draft blueprint resource | ⚠️ 官方参数/用法拒绝 | 2 | `blueprint resource --workspace C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\workspace` | cli parse error: RequiredError: exactly one of --search, --import, --update, or --sync is required |
| material search | ✅ 成功 | 0 | `search --type text --prompt 花` | success |
| material download | 🔐 需要登录 | 1 | `download --type text --resource-id func-test --resource-dir C:\Users\Administrator\AppData\Local\Temp\jianying-func-test` | material command failed in resource_pool: resource_pool err_code=-7002, err_msg=request failed: download failed, code=-4 |
| material query | ✅ 成功 | 0 | `query --resource-id func-test --type text` | success |
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
| media extract-frames | ⚠️ 官方参数/用法拒绝 | 2 | `extract-frames --input C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\media\sample.mp4 --output-dir C:\Use` | cli parse error: ValidationError: --format: mp4 not in {jpg,jpeg,png} |
| media extract-audio | ✅ 成功 | 0 | `extract-audio --input C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\media\sample.m4a --output C:\Users\Ad` | success |
| media probe | ✅ 成功 | 0 | `probe --input C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\media\sample.mp4` | success |
| media loudness | ✅ 成功 | 0 | `loudness --input C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\media\sample.mp4 --start 0s --duration 1s` | success |
| media measure-box | ⚠️ 官方业务拒绝 | 1 | `measure-box --input C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\media\sample.mp4 --type sticker --resou` | media: processing failed: video sticker measurement requires --allow-video-decode |
| media beats | ⚠️ 官方参数/用法拒绝 | 2 | `beats --input C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\media\sample.mp4 --output C:\Users\Administra` | cli parse error: ValidationError: --mode: Check auto value in {0->0,1->1,beats->1,melody->0} OR {0,1,1,0} FAILED |
| media object-matting-track | 🔐 需要登录 | 1 | `object-matting-track --input C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\media\sample.mp4 --seed-time f` | auth credential is missing: not logged in. Please log in and retry |
| media asr | 🔐 需要登录 | 1 | `asr --input C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\media\sample.m4a --language zh --output C:\User` | auth credential is missing: not logged in. Please log in and retry |
| media vad | 📦 本机缺模型 | 2 | `vad --input C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\media\sample.m4a --output C:\Users\Administrato` | media: platform runtime unsupported: VAD (AED) model not found: C:\Users\Administrator\AppData\Local\JianyingPro\Apps\11 |
| media feature | ✅ 成功 | 0 | `feature --input C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\media\sample.mp4 --module quality` | success |
| media translate | 🔐 需要登录 | 1 | `translate --input C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\media\sample.mp4 --target-language func-t` | auth credential is missing: not logged in. Please log in and retry |
| media understand | 🔐 需要登录 | 1 | `understand --path C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\media\sample.mp4 --prompt 花 --segment-id ` | auth credential is missing: not logged in. Please log in and retry |
| lint command | ➡️ 需真实前置产物 | 2 | `command --output C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\out\lint-command.mp4` | invalid argument: repo root does not look like lyra-cli: C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\ |
| lint media | ✅ 成功 | 0 | `media --input C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\media\sample.mp4 --output C:\Users\Administra` | success |
| lint algorithm-effect | ✅ 成功 | 2 | `algorithm-effect --algorithm func-test --candidate C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\media\sa` | success |
| lint draft | ✅ 成功 | 1 | `draft --ref local://func-test-1010-160233 --output C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\out\lint` | success |
| lint trace | ✅ 成功 | 1 | `trace --trace C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\media\sample.mp4 --output C:\Users\Administra` | success |
| upgrade | 🚧 官方未实现 | 2 | `` | command is not implemented yet (work in progress) |
| draft project duplicate | ✅ 成功 | 0 | `project duplicate --ref local://func-test-1010-160233 --to local://func-test-1010-160233-copy` | success |
| draft project import | ⚠️ 官方业务拒绝 | 1 | `project import --ref local://func-test-1010-160233` | draft already exists: local://func-test-1010-160233 already lives in the default workspace |
| draft history undo | 🚧 仅内嵌库支持 | 2 | `history undo --ref local://func-test-1010-160233` | draft history undo / redo is only available when lyra-cli is embedded as a client library; the standalone executable doe |
| draft history redo | 🚧 仅内嵌库支持 | 2 | `history redo --ref local://func-test-1010-160233` | draft history undo / redo is only available when lyra-cli is embedded as a client library; the standalone executable doe |
| draft deform apply | ✅ 成功 | 0 | `deform apply --scale 1 --ref local://func-test-1010-160233 --mode stretch --deform-seg-id D2EE9183-D094-4F40-9F37-9EAA05` | success |
| draft sticker translate | ➡️ 需真实前置产物 | 2 | `sticker translate --ref local://func-test-1010-160233 --seg-id D2EE9183-D094-4F40-9F37-9EAA0578F9E5` | gen_patch: invalid action: draft sticker translate target D2EE9183-D094-4F40-9F37-9EAA0578F9E5 has type 'segment_video', |
| draft text-template translate | ➡️ 需真实前置产物 | 2 | `text-template translate --ref local://func-test-1010-160233 --seg-id 19A4F135-6433-410E-9758-CC1C463FDCB3` | gen_patch: invalid action: draft text-template translate target 19A4F135-6433-410E-9758-CC1C463FDCB3 has type 'segment_t |
| draft text-template add | ➡️ 需真实前置产物 | 2 | `text-template add --ref local://func-test-1010-160233 --resource local:///C:/Users/Administrator/AppData/Local/Temp/jian` | gen_patch: invalid action: gen_patch --add add_text_template does not support local text template resources |
| draft text-template replace | ➡️ 需真实前置产物 | 2 | `text-template replace --ref local://func-test-1010-160233 --seg-id 19A4F135-6433-410E-9758-CC1C463FDCB3 --resource local` | gen_patch: invalid action: draft text-template replace target 19A4F135-6433-410E-9758-CC1C463FDCB3 has type 'segment_tex |
| draft text-template remove | ➡️ 需真实前置产物 | 2 | `text-template remove --ref local://func-test-1010-160233 --seg-id 19A4F135-6433-410E-9758-CC1C463FDCB3` | gen_patch: invalid action: draft text-template remove target 19A4F135-6433-410E-9758-CC1C463FDCB3 has type 'segment_text |
| draft segment time-range | ⚠️ 官方参数/用法拒绝 | 2 | `segment time-range --ref local://func-test-1010-160233 --seg-id D2EE9183-D094-4F40-9F37-9EAA0578F9E5 --out C:\Users\Admi` | cli parse error: ValidationError: draft segment time-range --duration cannot be combined with endpoint or endpoint-offse |
| draft segment add | ✅ 成功 | 0 | `segment add --ref local://func-test-1010-160233 --type text --resource local:///C:/Users/Administrator/AppData/Local/Tem` | success |
| draft compound-clip break-apart | ⚠️ 官方业务拒绝 | 1 | `compound-clip break-apart --ref local://func-test-1010-160233 --seg-id D2EE9183-D094-4F40-9F37-9EAA0578F9E5` | patch apply failed: break_combination cannot find stored child draft payload |
| draft blueprint plan | ✅ 成功 | 0 | `blueprint plan --workspace C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\workspace` | success |
| draft blueprint cancel | 🚧 仅内嵌库支持 | 2 | `blueprint cancel` | draft blueprint cancel is only available when lyra-cli is embedded as a client library; the standalone executable does n |
| draft blueprint commerce | ✅ 成功 | 0 | `blueprint commerce --workspace C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\workspace` | success |
| draft blueprint patch | ⚠️ 官方业务拒绝 | 1 | `blueprint patch --workspace C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\workspace --patch-file C:\Users` | internal error: process terminated by unhandled Windows exception 0xE06D7363 |
| draft video transition add | ✅ 成功 | 0 | `video transition add --ref local://func-test-1010-160233 --seg-id D2EE9183-D094-4F40-9F37-9EAA0578F9E5 --resource local:` | success |
| draft video transition update | ✅ 成功 | 0 | `video transition update --ref local://func-test-1010-160233 --seg-id D2EE9183-D094-4F40-9F37-9EAA0578F9E5 --resource loc` | success |
| draft video transition remove | ✅ 成功 | 0 | `video transition remove --ref local://func-test-1010-160233 --seg-id D2EE9183-D094-4F40-9F37-9EAA0578F9E5` | success |
| draft video filter add | ✅ 成功 | 0 | `video filter add --ref local://func-test-1010-160233 --seg-id D2EE9183-D094-4F40-9F37-9EAA0578F9E5 --resource local:///C` | success |
| draft video filter update | ✅ 成功 | 0 | `video filter update --ref local://func-test-1010-160233 --seg-id D2EE9183-D094-4F40-9F37-9EAA0578F9E5 --intensity 0` | success |
| draft video filter remove | ✅ 成功 | 0 | `video filter remove --ref local://func-test-1010-160233 --seg-id D2EE9183-D094-4F40-9F37-9EAA0578F9E5` | success |
| draft video effect add | ⚠️ 官方参数/用法拒绝 | 2 | `video effect add --ref local://func-test-1010-160233 --seg-id D2EE9183-D094-4F40-9F37-9EAA0578F9E5 --resource local:///C` | gen_patch: invalid action: gen_patch --add property=effect: type must be video_effect or face_effect |
| draft video effect update | ⚠️ 官方参数/用法拒绝 | 2 | `video effect update --ref local://func-test-1010-160233 --seg-id D2EE9183-D094-4F40-9F37-9EAA0578F9E5 --resource-id func` | cli parse error: ValidationError: draft video effect update: --params-json cannot be empty |
| draft video effect remove | ✅ 成功 | 0 | `video effect remove --ref local://func-test-1010-160233 --seg-id D2EE9183-D094-4F40-9F37-9EAA0578F9E5` | success |
| draft video mask add | ⚠️ 官方参数/用法拒绝 | 2 | `video mask add --ref local://func-test-1010-160233 --seg-id D2EE9183-D094-4F40-9F37-9EAA0578F9E5 --resource local:///C:/` | gen_patch: invalid action: gen_patch --add property=mask: unknown resource_type 'func-test'. Supported: rectangle \| circ |
| draft video mask update | ⚠️ 官方参数/用法拒绝 | 2 | `video mask update --ref local://func-test-1010-160233 --seg-id D2EE9183-D094-4F40-9F37-9EAA0578F9E5` | gen_patch: invalid action: gen_patch --update has no registered handler for field(s):  |
| draft video mask remove | ✅ 成功 | 0 | `video mask remove --ref local://func-test-1010-160233 --seg-id D2EE9183-D094-4F40-9F37-9EAA0578F9E5` | success |
| draft video animation add | ✅ 成功 | 0 | `video animation add --ref local://func-test-1010-160233 --seg-id D2EE9183-D094-4F40-9F37-9EAA0578F9E5 --resource local:/` | success |
| draft video animation update | ➡️ 需真实前置产物 | 2 | `video animation update --ref local://func-test-1010-160233 --seg-id D2EE9183-D094-4F40-9F37-9EAA0578F9E5 --animation-typ` | gen_patch: invalid action: gen_patch --update animation found no existing 'func-test' animation on target; use --add pro |
| draft video animation remove | ✅ 成功 | 0 | `video animation remove --ref local://func-test-1010-160233 --seg-id D2EE9183-D094-4F40-9F37-9EAA0578F9E5` | success |
| draft video beat add | ✅ 成功 | 0 | `video beat add --ref local://func-test-1010-160233 --seg-id D2EE9183-D094-4F40-9F37-9EAA0578F9E5 --times 1s` | success |
| draft video beat remove | ✅ 成功 | 0 | `video beat remove --ref local://func-test-1010-160233 --seg-id D2EE9183-D094-4F40-9F37-9EAA0578F9E5` | success |
| draft video audio-effect add | ⚠️ 官方业务拒绝 | 1 | `video audio-effect add --ref local://func-test-1010-160233 --seg-id D2EE9183-D094-4F40-9F37-9EAA0578F9E5 --resource loca` | patch apply failed: {"lyra_err_code":102,"lyra_err_msg":"download failed, sub_code: 1006, msg: error: resource query res |
| draft video color smart-color | ✅ 成功 | 0 | `video color smart-color --ref local://func-test-1010-160233 --seg-id D2EE9183-D094-4F40-9F37-9EAA0578F9E5 --resource loc` | success |
| draft video color correct | ✅ 成功 | 0 | `video color correct --ref local://func-test-1010-160233 --seg-id D2EE9183-D094-4F40-9F37-9EAA0578F9E5 --resource local:/` | success |
| draft text effect update | ⚠️ 官方业务拒绝 | 1 | `text effect update --ref local://func-test-1010-160233 --seg-id 19A4F135-6433-410E-9758-CC1C463FDCB3 --resource local://` | patch apply failed: {"lyra_err_code":102,"lyra_err_msg":"download failed, sub_code: 1006, msg: error: resource query res |
| draft text effect add | ⚠️ 官方业务拒绝 | 1 | `text effect add --ref local://func-test-1010-160233 --content 功能测试 --resource local:///C:/Users/Administrator/AppData/Lo` | patch apply failed: {"lyra_err_code":102,"lyra_err_msg":"download failed, sub_code: 1006, msg: error: resource query res |
| draft text animation set | ✅ 成功 | 0 | `text animation set --ref local://func-test-1010-160233 --seg-id 19A4F135-6433-410E-9758-CC1C463FDCB3 --resource local://` | success |
| draft text animation remove | ✅ 成功 | 0 | `text animation remove --ref local://func-test-1010-160233 --seg-id 19A4F135-6433-410E-9758-CC1C463FDCB3` | success |
| draft subtitle template add | ➡️ 需真实前置产物 | 2 | `subtitle template add --ref local://func-test-1010-160233 --resource local:///C:/Users/Administrator/AppData/Local/Temp/` | gen_patch: invalid action: gen_patch --add add_subtitle_template does not support local text template resources |
| draft subtitle template replace | ➡️ 需真实前置产物 | 2 | `subtitle template replace --ref local://func-test-1010-160233 --seg-id 19A4F135-6433-410E-9758-CC1C463FDCB3 --resource l` | gen_patch: invalid action: draft subtitle template replace target 19A4F135-6433-410E-9758-CC1C463FDCB3 has type 'segment |
| draft lyrics animation add | ➡️ 需真实前置产物 | 2 | `lyrics animation add --ref local://func-test-1010-160233 --resource local:///C:/Users/Administrator/AppData/Local/Temp/j` | gen_patch: invalid action: gen_patch --add lyric_animation requires a non-zero draft canvas; run `lyra-cli draft config  |
| draft lyrics animation update | ➡️ 需真实前置产物 | 2 | `lyrics animation update --ref local://func-test-1010-160233 --seg-id 19A4F135-6433-410E-9758-CC1C463FDCB3 --resource loc` | gen_patch: invalid action: gen_patch --update lyric_animation requires a non-zero draft canvas; run `lyra-cli draft conf |
| draft lyrics animation replace | ➡️ 需真实前置产物 | 2 | `lyrics animation replace --ref local://func-test-1010-160233 --seg-id 19A4F135-6433-410E-9758-CC1C463FDCB3 --resource lo` | gen_patch: invalid action: gen_patch --update lyric_animation requires a non-zero draft canvas; run `lyra-cli draft conf |
| draft keyframe curve set | ➡️ 需真实前置产物 | 2 | `keyframe curve set --ref local://func-test-1010-160233 --seg-id D2EE9183-D094-4F40-9F37-9EAA0578F9E5 --animated-property` | cli parse error: ValidationError: draft keyframe curve set requires exactly one of `--animated-property` or `--keyframe- |
| material motiongraph build-runtime-manifest | ⚠️ 官方业务拒绝 | 1 | `motiongraph build-runtime-manifest --package func-test --output-dir C:\Users\Administrator\AppData\Local\Temp\jianying-f` | motiongraph: invalid provider response: package not found: func-test |
| material motiongraph track-subject-mask | ➡️ 需真实前置产物 | 2 | `motiongraph track-subject-mask --input C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\media\sample.mp4 --r` | motiongraph: invalid argument: track-subject-mask requires exactly one of --target-object-desc or --seed-mask-rle-json |
| material motiongraph encode-subject-alpha | ➡️ 需真实前置产物 | 2 | `motiongraph encode-subject-alpha --mask-dir func-test --output-dir C:\Users\Administrator\AppData\Local\Temp\jianying-fu` | motiongraph: invalid argument: mask dir is not a directory: func-test |
| material motiongraph track-plane-quad | ⚠️ 官方参数/用法拒绝 | 2 | `motiongraph track-plane-quad --ref local://func-test-1010-160233 --target-seg-id func-test --output-dir C:\Users\Adminis` | motiongraph: invalid argument: direct track-plane-quad requires --plane-desc or a legacy --object-desc when --initial-qu |
| media aigc text2image | 🔐 需要登录 | 1 | `aigc text2image --prompt 花` | auth credential is missing: not logged in. Please log in and retry |
| media aigc image2image | 🔐 需要登录 | 1 | `aigc image2image --images func-test --prompt 花` | auth credential is missing: not logged in. Please log in and retry |
| media aigc text2video | 🔐 需要登录 | 1 | `aigc text2video --prompt 花 --duration 1` | auth credential is missing: not logged in. Please log in and retry |
| media aigc image2video | 🔐 需要登录 | 1 | `aigc image2video --prompt 花 --duration 1` | auth credential is missing: not logged in. Please log in and retry |
| media aigc query | 🔐 需要登录 | 1 | `aigc query --submit-id func-test` | auth credential is missing: not logged in. Please log in and retry |
| auth login | ⏱️ 超时 | 1 | `login` |  |
| auth relogin | ⏱️ 超时 | 1 | `relogin` |  |
| auth qrcode | ⚠️ 官方参数/用法拒绝 | 2 | `qrcode --output C:\Users\Administrator\AppData\Local\Temp\jianying-func-test\out\auth-qrcode.mp4` | cli parse error: RequiredError: url is required |
| auth status | ✅ 成功 | 0 | `status` | success |
| auth me | ✅ 成功 | 0 | `me` | success |
| auth check | ✅ 成功 | 0 | `check` | success |
| auth logout | ✅ 成功 | 0 | `logout` | success |
| draft project version upgrade | 🚧 官方未实现 | 2 | `project version upgrade --ref local://func-test-1010-160233` | command is not implemented yet (work in progress): draft project version upgrade is not implemented yet |
| draft project version downgrade | ✅ 成功 | 0 | `project version downgrade --ref local://func-test-1010-160233` | success |
| draft timeline segment copy | ➡️ 需真实前置产物 | 2 | `timeline segment copy --ref local://func-test-1010-160233 --seg-id D2EE9183-D094-4F40-9F37-9EAA0578F9E5 --source-timelin` | cli parse error: ValidationError: draft timeline segment copy requires different source and target timelines |
| draft timeline segment move | ➡️ 需真实前置产物 | 2 | `timeline segment move --ref local://func-test-1010-160233 --seg-id D2EE9183-D094-4F40-9F37-9EAA0578F9E5 --source-timelin` | cli parse error: ValidationError: draft timeline segment move requires different source and target timelines |
| draft algo object-matting-track | ➡️ 需真实前置产物 | 2 | `algo object-matting-track --ref local://func-test-1010-160233 --seg-id D2EE9183-D094-4F40-9F37-9EAA0578F9E5 --segment-ti` | cli parse error: ValidationError: object-matting-track requires exactly one of --seed-mask-rle-json or --target-object-d |
