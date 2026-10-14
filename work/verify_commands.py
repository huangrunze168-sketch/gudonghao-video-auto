"""验证清单驱动的封装是否覆盖全部命令。"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "engine"))
import lyra_cli  # noqa: E402

print("清单命令数:", lyra_cli.COMMAND_COUNT)
print("索引条目:", len(lyra_cli.COMMAND_INDEX))
print("保留的手写封装:", lyra_cli.COMMAND_SKIPPED)

samples = ["video_speed", "video_crop", "video_adjust", "text_style", "text_add",
           "algo_tts", "algo_quality_enhance", "algo_ai_matting", "algo_custom_matting",
           "algo_video_tracking", "media_probe", "media_compress", "media_extract_frames",
           "material_search", "material_download", "template_render", "keyframe_add",
           "effect_generate", "subtitle_add", "audio_add", "lint_draft", "lyrics_recognize"]
print("\n抽样:")
for name in samples:
    fn = getattr(lyra_cli, name, None)
    params = len(getattr(fn, "allowed_options", []) or []) if fn else 0
    print(f"  {name:26s} {'有' if callable(fn) else '缺失'}  参数 {params}")

missing = [name for name in lyra_cli.COMMAND_INDEX if not callable(getattr(lyra_cli, name, None))]
print("\n未装成函数的命令:", missing or "无")
