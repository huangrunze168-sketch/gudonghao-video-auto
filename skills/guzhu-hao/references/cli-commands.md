# 剪映官方 CLI 能力清单

由 `engine/lyra_commands.json` 生成。全部命令都经
`engine/draftediting_runtime.py` 在官方 VMSDK 沙箱内执行；
直接调 `lyra-cli.exe` 会报 `unauthorized host process`。

## (顶层)（1 条）

| 命令 | 用途 | 关键参数 |
| --- | --- | --- |
| `upgrade` | Upgrade lyra-cli to the latest version. | - |

## auth（7 条）

| 命令 | 用途 | 关键参数 |
| --- | --- | --- |
| `auth.check` | Check whether the current login is usable | --profile |
| `auth.login` | Log in with Jianying desktop app first, or use QR/link URL login. | --require-jianying-app, --qr-code, --link-url, --no-wait, --device-code, --user-code, --session-handoff, --qr-token … |
| `auth.logout` | Log out of current account | --profile |
| `auth.me` | Show current account profile | --profile |
| `auth.qrcode` | Generate a QR code file or terminal rendering for an authorization URL. | --output, --ascii, --size |
| `auth.relogin` | Log in again and replace the current credential after validation. | --require-jianying-app, --qr-code, --link-url, --no-wait, --device-code, --user-code, --session-handoff, --qr-token … |
| `auth.status` | Show current authentication status | --profile |

## draft（146 条）

| 命令 | 用途 | 关键参数 |
| --- | --- | --- |
| `draft.adjust.add` | Add a global picture-adjust segment to the draft. | --ref, --brightness, --contrast, --saturation, --color-temperature, --highlight, --shadow, --sharpening … |
| `draft.adjust.remove` | Remove an adjust segment. | --ref, --seg-id, --seg-type, --target-track, --seg-index, --time-window |
| `draft.algo.ai-frame-interpolation` | Run AI frame interpolation for a target video segment. | --ref, --seg-id, --wait, --timeout, --fps, --model |
| `draft.algo.ai-matting` | Run AI matting on a video or photo segment. | --ref, --seg-id, --feather, --expansion, --reverse, --wait, --workspace, --config-path … |
| `draft.algo.ai-transition` | Generate or write back an AI transition between adjacent videos. | --ref, --after-seg-id, --video-path, --effect-path, --resource, --duration, --overlap, --prompt … |
| `draft.algo.chroma-color-matting` | Run chroma color matting on a target segment. | --ref, --seg-id, --color, --intensity, --shadow, --edge-smooth, --spill, --path |
| `draft.algo.custom-matting` | Run custom matting and validate its mask result when waiting. | --ref, --seg-id, --feather, --expansion, --reverse, --wait, --timeout, --disable … |
| `draft.algo.denoise` | Apply realtime denoising to one audio or video segment. | --ref, --seg-id, --enable, --denoise-mode, --rate, --path, --sami-name, --sami-version … |
| `draft.algo.loudness-normalize` | Normalize one audio or video segment to a target loudness. | --ref, --seg-id, --target-loudness, --average-loudness, --peak-loudness, --true-peak-ceiling, --enable |
| `draft.algo.material-understand` | Understand one draft video segment and persist a reusable sidecar snapshot. | --ref, --seg-id, --prompt, --analysis-module, --analysis-level, --frame-interval, --timeout, --content-fingerprint … |
| `draft.algo.music-beats` | Detect music beats or melody points. | --ref, --seg-id, --level, --mode, --level-count, --apply, --return-beats-info, --need-audio-has-music … |
| `draft.algo.object-matting-track` | Track object matting from a seed mask or a target description. | --ref, --seg-id, --segment-time, --seed-mask-rle-json, --mask-rle-json, --target-object-desc, --sam3-target-object-desc, --feather … |
| `draft.algo.quality-enhance` | Enhance video/image quality for target segment(s). | --ref, --seg-id, --level, --from, --wait, --timeout |
| `draft.algo.query` | Query a persistent video-tracking task. | --task-id |
| `draft.algo.sound-separation` | Run vocal/instrument sound separation. | --ref, --seg-id, --mode, --keep, --sounds, --apply, --output-dir, --format … |
| `draft.algo.subtitle-keywords` | Detect and apply intelligent subtitle keyword highlights. | --ref, --seg-id, --language, --apply, --replace |
| `draft.algo.subtitle-recognize` | Recognize subtitles or lyrics from the draft or a segment. | --ref, --seg-id, --language, --recognize-type, --mode, --timeout, --poll-interval, --clear-previous … |
| `draft.algo.text-add-tone` | Add tone/voice metadata to a text segment. | --ref, --seg-id, --text, --speed, --emotion, --audio-path, --resource-id, --network-mode … |
| `draft.algo.tts` | Synthesize speech for a text segment. | --ref, --seg-id, --text, --speed, --speaker, --audio-path, --resource-id, --network-mode … |
| `draft.algo.upscale-resolution` | Upscale target segment resolution. | --ref, --seg-id, --mode, --from, --input-path, --output-path, --history-node-id, --task-id … |
| `draft.algo.video-stabilize` | Stabilize one video segment and persist its motion matrix. | --ref, --seg-id, --timeout, --level, --disable |
| `draft.algo.video-tracking` | Run video tracking for a target segment. | --ref, --seg-id, --follower-seg-id, --source-seg-id, --tracker-type, --center-x, --center-y, --width … |
| `draft.algo.voice-enhance` | Enhance human voice on one audio or video segment. | --ref, --seg-id, --enable, --ambient-sound-level, --production-path, --from-hd-sounds |
| `draft.algo.wait` | Wait for a persistent video-tracking task. | --task-id, --timeout, --poll-interval |
| `draft.audio.add` | Add an audio segment to the draft. | --ref, --kind, --resource, --track, --start, --duration, --source-from |
| `draft.audio.fade` | Set audio segment fade in/out. | --ref, --seg-id, --seg-type, --target-track, --seg-index, --time-window, --in, --out … |
| `draft.audio.remove` | Remove an audio segment. | --ref, --seg-id, --seg-type, --target-track, --seg-index, --time-window |
| `draft.audio.speed` | Change an audio segment playback speed. | --ref, --seg-id, --seg-type, --target-track, --seg-index, --time-window, --speed |
| `draft.audio.volume` | Set an audio segment volume. | --ref, --seg-id, --seg-type, --target-track, --seg-index, --time-window, --linear, --db |
| `draft.blueprint.apply` | Apply the blueprint workspace onto a real draft. | --workspace, --ref, --selection, --selection-file, --base-revision, --require-material-understanding, --allow-existing-main-deletion, --allow-existing-subtitle-changes … |
| `draft.blueprint.cancel` | Request cancellation of the active blueprint apply for this client session. | - |
| `draft.blueprint.commerce` | Extract XML-only atomic capability keys for commerce precheck. This command | --workspace, --selection, --selection-file, --target-xml, --target-xml-file, --current-xml-file, --allow-existing-main-deletion |
| `draft.blueprint.init` | Create an empty blueprint workspace skeleton. | --workspace, --protocol |
| `draft.blueprint.patch` | Apply a Node Patch to the latest synchronized Draft XML and write the result to | --workspace, --patch-file, --dry-run, --allow-existing-main-deletion |
| `draft.blueprint.plan` | Show the cmd_list a future apply would execute (dry-run). | --workspace, --require-material-understanding, --allow-existing-main-deletion, --allow-existing-subtitle-changes, --allow-segment-deletion, --delete-reason, --allow-subtitle-delete-ids, --delete-target-id |
| `draft.blueprint.resource` | Process declarative material operations (--search), including | --workspace, --search, --import, --update, --sync, --format, --asset-id, --title |
| `draft.blueprint.sync` | Reverse-sync a real draft back into blueprint XML. | --workspace, --ref, --current-only |
| `draft.compound-clip.break-apart` | Break apart a compound clip back into its constituent segments. | --ref, --seg-id |
| `draft.compound-clip.create` | Create a compound clip (a.k.a. group segments) from one or more segments. | --ref, --seg-id, --seg-type, --target-track, --seg-index, --time-window, --name |
| `draft.config` | Configure draft-level settings (no target). | --ref, --ratio |
| `draft.cover.clear` | Clear the draft cover | --ref, --minidraft |
| `draft.cover.set` | Set the draft cover from an image URL, local image, or timeline frame | --ref, --minidraft, --image, --url, --frame |
| `draft.deform.apply` | Apply stretch, corner-pin (video/sticker), or surface-track deformation. | --ref, --mode, --deform-seg-id, --follower-seg-id, --tracked-video-seg-id, --corner-top-left, --corner-bottom-left, --corner-top-right … |
| `draft.edit` | FROZEN LEGACY RAW COMPATIBILITY FOR EXISTING INTEGRATIONS. | --ref, --minidraft, --add, --remove, --move, --update, --op, --target … |
| `draft.effect.add` | Add a global (track) effect segment to the draft. | --ref, --resource, --type, --track, --start, --duration, --apply-type, --dir … |
| `draft.effect.generate` | Generate a MotionGraph effect in the cloud and apply it to the draft. | --ref, --dir, --type, --provider, --execution, --prompt, --start, --duration … |
| `draft.effect.remove` | Remove an effect segment. | --ref, --seg-id, --seg-type, --target-track, --seg-index, --time-window |
| `draft.extract.summary` | Read a compact draft overview for locating segment ids. | --ref, --dir, --seg-id, --protocol |
| `draft.filter.add` | Add a global (track) filter segment to the draft. | --ref, --resource, --track, --start, --duration, --intensity |
| `draft.filter.remove` | Remove a filter segment. | --ref, --seg-id, --seg-type, --target-track, --seg-index, --time-window |
| `draft.filter.update` | Update a global filter segment intensity. | --ref, --seg-id, --seg-type, --target-track, --seg-index, --time-window, --intensity |
| `draft.history.redo` | Redo the most recently undone edit(s) | --ref, --steps, --minidraft |
| `draft.history.undo` | Undo the most recent edit(s) | --ref, --steps, --minidraft |
| `draft.keyframe.add` | Add keyframe point(s) to a segment. | --ref, --seg-id, --seg-type, --target-track, --seg-index, --time-window, --animated-property, --keyframe-type … |
| `draft.keyframe.curve.set` | Set the interpolation curve of an existing keyframe point. | --ref, --seg-id, --seg-type, --target-track, --seg-index, --time-window, --animated-property, --keyframe-type … |
| `draft.keyframe.remove` | Remove keyframe point(s) from a segment. | --ref, --seg-id, --seg-type, --target-track, --seg-index, --time-window, --animated-property, --keyframe-type … |
| `draft.keyframe.update` | Update the value of an existing keyframe point. | --ref, --seg-id, --seg-type, --target-track, --seg-index, --time-window, --animated-property, --keyframe-type … |
| `draft.lyrics.add` | Add a lyrics (plain text) segment to the draft. | --ref, --content, --track, --start, --duration, --wrap-width |
| `draft.lyrics.animation.add` | Apply a lyrics animation resource to recognized lyrics in the draft. | --ref, --resource, --cover-old, --language |
| `draft.lyrics.animation.replace` | Replace the lyrics animation resource on an existing lyrics segment. | --ref, --seg-id, --seg-type, --target-track, --seg-index, --time-window, --resource, --language |
| `draft.lyrics.animation.update` | Update the lyrics animation resource on an existing lyrics segment. | --ref, --seg-id, --seg-type, --target-track, --seg-index, --time-window, --resource, --language |
| `draft.lyrics.recognize` | Recognize lyrics from the draft or a segment. | --ref, --seg-id, --language, --mode, --timeout, --poll-interval, --clear-previous, --translate-language-code … |
| `draft.lyrics.remove` | Remove a lyrics segment. | --ref, --seg-id, --seg-type, --target-track, --seg-index, --time-window |
| `draft.project.create` | Create a new draft project | --ref, --dir |
| `draft.project.delete` | Delete a draft project | --ref |
| `draft.project.duplicate` | Duplicate a draft project | --ref, --to |
| `draft.project.focus` | Focus a draft project, so that the subsequent commands without `--ref` will use | --ref |
| `draft.project.import` | Move an external draft project (created with `draft project create --dir`) back | --ref |
| `draft.project.list` | List draft projects | - |
| `draft.project.version.downgrade` | Downgrade a draft in place and save it back | --ref |
| `draft.project.version.upgrade` | Upgrade a draft in place and save it back (not implemented yet) | --ref |
| `draft.segment.add` | Add a segment to the draft (flat alias of `draft <type> add`). | --ref, --type, --resource, --track, --start, --duration, --width, --height … |
| `draft.segment.duplicate` | Duplicate a segment. | --ref, --seg-id, --seg-type, --target-track, --seg-index, --time-window, --start, --track |
| `draft.segment.move` | Move a segment. | --ref, --seg-id, --seg-type, --target-track, --seg-index, --time-window, --track, --start … |
| `draft.segment.remove` | Remove a segment. | --ref, --seg-id, --seg-type, --target-track, --seg-index, --time-window |
| `draft.segment.split` | Split a segment at given time point(s). | --ref, --seg-id, --seg-type, --target-track, --seg-index, --time-window, --points, --absolute … |
| `draft.segment.time-range` | Update a segment time range or duration. | --ref, --seg-id, --seg-type, --target-track, --seg-index, --time-window, --in, --out … |
| `draft.sticker.add` | Add a sticker segment to the draft. | --ref, --resource, --track, --start, --duration |
| `draft.sticker.remove` | Remove a sticker segment. | --ref, --seg-id, --seg-type, --target-track, --seg-index, --time-window |
| `draft.sticker.translate` | Move a sticker segment on the canvas. | --ref, --seg-id, --seg-type, --target-track, --seg-index, --time-window, --x, --y |
| `draft.subtitle.add` | Add a subtitle (plain text) segment to the draft. | --ref, --content, --track, --start, --duration, --wrap-width |
| `draft.subtitle.recognize` | Recognize subtitles from the draft or a segment. | --ref, --seg-id, --language, --mode, --timeout, --poll-interval, --clear-previous, --translate-language-code … |
| `draft.subtitle.remove` | Remove a subtitle segment. | --ref, --seg-id, --seg-type, --target-track, --seg-index, --time-window |
| `draft.subtitle.template.add` | Add a subtitle-template segment to the draft. | --ref, --resource, --content, --start, --duration, --keyword-range |
| `draft.subtitle.template.replace` | Replace a subtitle-template segment's template resource. | --ref, --seg-id, --seg-type, --target-track, --seg-index, --time-window, --resource, --apply-to-all … |
| `draft.template.add` | Add a draft template package as a template segment. | --ref, --resource, --title, --start, --track-index, --scene, --duration, --muted … |
| `draft.template.publish` | Publish the current designer draft as a standard local template package. | --ref, --slot, --dir, --source-mode, --source-json, --source-root, --selection-start-ms, --selection-duration-ms |
| `draft.template.render` | Compile template_config.json through Blueprint XML, apply it, and export MP4. | --config, --ref, --output, --dir |
| `draft.template.replace` | Replace one slot inside an added template segment. | --ref, --template-seg-id, --slot, --resource, --content, --inherit, --sync-group |
| `draft.template.slots` | List replaceable slots inside an added template segment. | --ref, --template-seg-id |
| `draft.text-template.add` | Add a text-template segment to the draft. | --ref, --resource, --content, --start, --duration |
| `draft.text-template.remove` | Remove a text-template segment. | --ref, --seg-id, --seg-type, --target-track, --seg-index, --time-window |
| `draft.text-template.replace` | Replace a text-template segment's template resource. | --ref, --seg-id, --seg-type, --target-track, --seg-index, --time-window, --resource, --apply-to-all … |
| `draft.text-template.translate` | Move a text-template segment on the canvas. | --ref, --seg-id, --seg-type, --target-track, --seg-index, --time-window, --x, --y |
| `draft.text.add` | Add a plain text segment to the draft. | --ref, --content, --track, --start, --duration, --text-type, --wrap-width, --background … |
| `draft.text.animation.remove` | Remove a text segment animation. | --ref, --seg-id, --seg-type, --target-track, --seg-index, --time-window, --animation-type |
| `draft.text.animation.set` | Set a text segment animation of one type (upsert/replace). | --ref, --seg-id, --seg-type, --target-track, --seg-index, --time-window, --resource, --animation-type … |
| `draft.text.content` | Update text content with one atomic shortcut operation. | --ref, --seg-id, --seg-type, --target-track, --seg-index, --time-window, --content, --find … |
| `draft.text.effect.add` | Add a text-effect (a.k.a. flower / text effect) segment to the draft. | --ref, --content, --resource, --name, --category-id, --track, --start, --duration … |
| `draft.text.effect.update` | Update a text segment's text-effect (a.k.a. flower / text effect) resource. | --ref, --seg-id, --seg-type, --target-track, --seg-index, --time-window, --resource |
| `draft.text.remove` | Remove a text segment. | --ref, --seg-id, --seg-type, --target-track, --seg-index, --time-window |
| `draft.text.style` | Update one or more text style parameters in a single command. | --ref, --seg-id, --seg-type, --target-track, --seg-index, --time-window, --size, --color … |
| `draft.text.translate` | Move a text segment on the canvas. | --ref, --seg-id, --seg-type, --target-track, --seg-index, --time-window, --x, --y |
| `draft.text.wrap-width` | Set a text segment's fixed text-box width (auto-wrap on overflow). | --ref, --seg-id, --seg-type, --target-track, --seg-index, --time-window, --width |
| `draft.timeline.segment.copy` | Copy one or more segments between timelines. | --ref, --seg-id, --seg-type, --target-track, --seg-index, --time-window, --source-timeline, --target-timeline … |
| `draft.timeline.segment.move` | Move one or more complete segments between timelines in one batch. | --ref, --seg-id, --seg-type, --target-track, --seg-index, --time-window, --source-timeline, --target-timeline … |
| `draft.video.add` | Add a video (or photo) segment to the draft. | --ref, --resource, --track, --start, --duration, --width, --height, --is-photo … |
| `draft.video.adjust` | Adjust picture parameters of a video segment. | --ref, --seg-id, --seg-type, --target-track, --seg-index, --time-window, --brightness, --contrast … |
| `draft.video.alpha` | Set a video segment opacity. | --ref, --seg-id, --seg-type, --target-track, --seg-index, --time-window, --alpha |
| `draft.video.animation.add` | Add an animation to a video segment. | --ref, --seg-id, --seg-type, --target-track, --seg-index, --time-window, --resource, --animation-type … |
| `draft.video.animation.remove` | Remove a video segment animation. | --ref, --seg-id, --seg-type, --target-track, --seg-index, --time-window, --animation-type |
| `draft.video.animation.update` | Update a video segment animation. | --ref, --seg-id, --seg-type, --target-track, --seg-index, --time-window, --animation-type, --duration … |
| `draft.video.audio-effect.add` | Add an audio effect (voice change) to a video or audio segment. | --ref, --seg-id, --seg-type, --target-track, --seg-index, --time-window, --resource, --source-from |
| `draft.video.background` | Set the background canvas of a video segment. | --ref, --seg-id, --seg-type, --target-track, --seg-index, --time-window, --type, --color … |
| `draft.video.beat.add` | Add beat marker(s) to a segment. | --ref, --seg-id, --seg-type, --target-track, --seg-index, --time-window, --times |
| `draft.video.beat.remove` | Remove beat marker(s) from a segment. | --ref, --seg-id, --seg-type, --target-track, --seg-index, --time-window, --all, --times |
| `draft.video.color.correct` | Apply color correction to a video segment. | --ref, --seg-id, --seg-type, --target-track, --seg-index, --time-window, --enable, --resource … |
| `draft.video.color.smart-color` | Apply smart color to a video segment. | --ref, --seg-id, --seg-type, --target-track, --seg-index, --time-window, --enable, --resource … |
| `draft.video.crop` | Crop a video segment. | --ref, --seg-id, --seg-type, --target-track, --seg-index, --time-window, --ratio, --box … |
| `draft.video.effect.add` | Add an effect to a video segment. | --ref, --seg-id, --seg-type, --target-track, --seg-index, --time-window, --resource, --type |
| `draft.video.effect.remove` | Remove a video segment effect. | --ref, --seg-id, --seg-type, --target-track, --seg-index, --time-window |
| `draft.video.effect.update` | Update a video segment effect adjust parameters. | --ref, --seg-id, --seg-type, --target-track, --seg-index, --time-window, --resource-id, --params-json |
| `draft.video.extract-frames` | Extract frame image(s) from the draft or a segment. | --ref, --seg-id, --seg-type, --target-track, --seg-index, --time-window, --output-path, --timestamp … |
| `draft.video.extract-music` | Extract music/audio from a local resource or a segment. | --ref, --seg-id, --seg-type, --target-track, --seg-index, --time-window, --resource, --start |
| `draft.video.face-beauty` | Apply or clear one face-beauty category, or apply one preset package. | --ref, --seg-id, --seg-type, --target-track, --seg-index, --time-window, --skin, --shape … |
| `draft.video.filter.add` | Add a filter to a video segment. | --ref, --seg-id, --seg-type, --target-track, --seg-index, --time-window, --resource, --intensity |
| `draft.video.filter.remove` | Remove a video segment filter. | --ref, --seg-id, --seg-type, --target-track, --seg-index, --time-window |
| `draft.video.filter.update` | Update a video segment filter intensity. | --ref, --seg-id, --seg-type, --target-track, --seg-index, --time-window, --intensity |
| `draft.video.flip` | Flip a video segment horizontally and/or vertically. | --ref, --seg-id, --seg-type, --target-track, --seg-index, --time-window, --horizontal, --vertical |
| `draft.video.freeze` | Freeze a frame of a video segment. | --ref, --seg-id, --seg-type, --target-track, --seg-index, --time-window, --time, --duration |
| `draft.video.layer` | Set a video segment render layer. | --ref, --seg-id, --seg-type, --target-track, --seg-index, --time-window, --z-order |
| `draft.video.mask.add` | Add a mask to a video segment. | --ref, --seg-id, --seg-type, --target-track, --seg-index, --time-window, --resource, --resource-type … |
| `draft.video.mask.remove` | Remove a video segment mask. | --ref, --seg-id, --seg-type, --target-track, --seg-index, --time-window, --mask-id |
| `draft.video.mask.update` | Update a video segment mask geometry. | --ref, --seg-id, --seg-type, --target-track, --seg-index, --time-window, --width, --height … |
| `draft.video.matting-stroke` | Apply / update / cancel matting stroke on a video or photo segment. | --ref, --seg-id, --seg-type, --target-track, --seg-index, --time-window, --enable, --disable … |
| `draft.video.mix-mode` | Apply / cancel PIP blend (mix) mode on a picture-in-picture video segment. | --ref, --seg-id, --seg-type, --target-track, --seg-index, --time-window, --enable, --disable … |
| `draft.video.remove` | Remove a video segment. | --ref, --seg-id, --seg-type, --target-track, --seg-index, --time-window |
| `draft.video.rotate` | Rotate a video segment. | --ref, --seg-id, --seg-type, --target-track, --seg-index, --time-window, --rotation |
| `draft.video.scale` | Scale a video segment. | --ref, --seg-id, --seg-type, --target-track, --seg-index, --time-window, --scale, --x … |
| `draft.video.speed` | Change a video segment playback speed, or apply a curve speed. | --ref, --seg-id, --seg-type, --target-track, --seg-index, --time-window, --speed, --curve-name … |
| `draft.video.stabilize` | Apply or disable video stabilization. | --ref, --seg-id, --level, --disable, --timeout |
| `draft.video.transition.add` | Add a transition to a video segment. | --ref, --seg-id, --seg-type, --target-track, --seg-index, --time-window, --resource, --duration … |
| `draft.video.transition.remove` | Remove a video segment transition. | --ref, --seg-id, --seg-type, --target-track, --seg-index, --time-window |
| `draft.video.transition.update` | Update a video segment transition (resource / duration). | --ref, --seg-id, --seg-type, --target-track, --seg-index, --time-window, --resource, --duration |
| `draft.video.translate` | Move a video segment on the canvas. | --ref, --seg-id, --seg-type, --target-track, --seg-index, --time-window, --x, --y |
| `draft.video.volume` | Set a video segment volume. | --ref, --seg-id, --seg-type, --target-track, --seg-index, --time-window, --linear, --db |

## lint（5 条）

| 命令 | 用途 | 关键参数 |
| --- | --- | --- |
| `lint.algorithm-effect` | Measure a supported algorithm's observable effect through the configured | --algorithm, --comparison-mode, --baseline, --candidate, --prompt, --analyzer, --artifacts, --output … |
| `lint.command` | Validate command contracts and declarative Acceptance Cards for lyra-cli. | --repo-root, --binary, --cards-root, --execution-plan, --acceptance-type, --protected-repo, --suite, --capability … |
| `lint.draft` | Screen a real lv-draft or offline lv-draft JSON snapshot for structural validity | --ref, --input, --suite, --require-segment, --require-contiguous, --require-timeline-evidence, --local-resource-root, --spatial-overlap-threshold … |
| `lint.media` | Screen media with CCCreator metadata/quality probes and an optional | --input, --expected-kind, --expected-format, --expected-orientation, --suite, --min-duration, --max-duration, --min-width … |
| `lint.trace` | Evaluate an existing command/workflow trace without executing or repairing it. | --trace, --suite, --workflow, --expect-step, --expect-order, --target-policy, --material-policy, --material-check … |

## material（10 条）

| 命令 | 用途 | 关键参数 |
| --- | --- | --- |
| `material.download` | Download an asset file by type and resource ID. | --type, --resource-id, --resource-platform, --resource-dir, --channel |
| `material.motiongraph.build-runtime-manifest` | Orchestrate MG runtime data strictly from the package | --package, --target-material-id, --target-seg-id, --output-dir, --recipe-json, --materials-xml, --runtime-target-json, --ref … |
| `material.motiongraph.encode-subject-alpha` | Atomic: encode mask frames into subject_alpha.v1 (RLE) + subject_transform.v1 | --mask-dir, --maskinfo-path, --output-dir, --effect-start-us, --fps, --runtime-key, --channel |
| `material.motiongraph.track-plane-quad` | Atomic: plane seed + in-memory video-tracking into plane_quad.v1 | --ref, --target-seg-id, --object-desc, --plane-desc, --seed-time, --initial-quad-json, --duration-us, --output-dir … |
| `material.motiongraph.track-subject-mask` | Atomic: subject mask/VOS. Uses draft-aware mask_tracking_matting when --ref + | --input, --ref, --seg-id, --target-object-desc, --seed-mask-rle-json, --seed-time, --output-dir, --channel |
| `material.query` | Inspect metadata for a known material resource ID. | --resource-id, --type, --channel |
| `material.recommend` | Fetch a recommended / hot material list for the given asset type. (WIP) | --type, --limit, --channel |
| `material.search` | Search assets by type and natural-language intent. | --type, --prompt, --limit, --need-recommend, --filter-commercial, --filter-ai-transition, --search-scene, --category-list … |
| `material.similar` | Fetch similar materials seeded by an existing resource ID. (WIP) | --type, --by, --limit, --channel |
| `material.topic` | Browse material topic collections, or list assets inside a specific topic. | --type, --resource-platform, --scene, --id, --topic-key, --list-source, --limit, --cursor … |

## media（26 条）

| 命令 | 用途 | 关键参数 |
| --- | --- | --- |
| `media.aigc.image2image` | Submit a provider image-to-image asset task with one or more reference images. | --images, --image, --prompt, --ratio, --resolution-type, --provider, --provider-params-json, --model-version … |
| `media.aigc.image2video` | Submit an image-to-video task using explicit first/end frames or repeatable | --first-image, --image, --end-image, --reference-image, --prompt, --duration, --video-resolution, --ratio … |
| `media.aigc.query` | Query one AIGC async task by submit id and optionally download artifacts. | --submit-id, --download-dir, --download-format, --poll, --wait, --provider, --provider-params-json |
| `media.aigc.text2image` | Submit a provider text-to-image asset task. Default is async; use --wait/--poll | --prompt, --ratio, --resolution-type, --provider, --provider-params-json, --model-version, --download-dir, --download-format … |
| `media.aigc.text2video` | Submit a provider text-to-video asset task. Default is async; use --wait/--poll | --prompt, --duration, --video-resolution, --ratio, --provider, --provider-params-json, --model-version, --download-dir … |
| `media.asr` | Recognize speech from a local audio or video file and return ASR sentences. | --input, --language, --output, --clear-talking-head, --timeout |
| `media.beats` | Detect music beat positions in a local audio or video file. Video inputs are | --input, --output, --mode, --level, --level-count, --upload-vid |
| `media.change-audio-speed` | Change a whole local audio file's playback speed and create a new file. | --input, --output, --speed, --preserve-pitch, --no-preserve-pitch |
| `media.change-video-speed` | Change a whole local video's playback speed and create a new video. | --input, --output, --speed |
| `media.compress` | Compress a video file to a target resolution. Bitrate auto-derives from | --input, --output, --width, --height, --bitrate, --codec, --quality, --fps … |
| `media.crop-image` | Crop a display-oriented pixel rectangle from a local image. | --input, --output, --left, --top, --width, --height, --format, --quality |
| `media.extract-audio` | Extract the audio track from a video file. | --input, --output, --bitrate |
| `media.extract-frames` | Extract display-oriented JPEG/PNG frames at exact timestamps or a fixed | --input, --output-dir, --start, --end, --duration, --timestamp, --interval, --format … |
| `media.feature` | Extract deterministic L2 visual features from local media or prepared image | --input, --frame, --module |
| `media.loudness` | Detect average and peak loudness of a local audio or video file. | --input, --start, --end, --duration |
| `media.measure-box` | Measure a sticker or picture-in-picture media layout box without creating a VE | --input, --type, --element-type, --resource-dir, --canvas-width, --canvas-height, --longest-edge, --clip-scale … |
| `media.object-matting-track` | Track an object in a local video and generate a complete timestamped mask | --input, --seed-time, --output-dir, --seed-mask-rle-json, --mask-rle-json, --target-object-desc, --sam3-target-object-desc, --feather … |
| `media.probe` | Probe a local audio, image, or video file and return stable technical metadata. | --input, --field |
| `media.resize-image` | Resize a local image, preserving aspect ratio when one dimension is omitted. | --input, --output, --width, --height, --format, --quality |
| `media.rotate` | Physically rotate the displayed input video by 0, 90, 180, or 270 degrees and | --input, --output, --degrees, --bitrate, --codec, --quality, --fps |
| `media.transcode-image` | Convert a local image to a web-safe JPEG/PNG file. | --input, --output, --format, --quality |
| `media.translate` | Translate sentence-level JSON produced by media asr without rerunning ASR. | --input, --source-language, --target-language, --output, --timeout |
| `media.trim-audio` | Keep the source audio interval [start,end). | --input, --output, --start, --end |
| `media.trim-video` | Keep the source video interval [start,end), including synchronized audio. | --input, --output, --start, --end |
| `media.understand` | Analyze a local media file and return material understanding metadata. | --path, --input, --prompt, --asset-id, --material-id, --segment-id, --type, --start-time … |
| `media.vad` | Detect voice-active segments in a local audio or video file (VAD). | --input, --output, --start, --end, --duration |
