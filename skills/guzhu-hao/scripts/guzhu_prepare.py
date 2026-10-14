"""新歌素材准备：把上传的 wav/txt 放好、清只读、生成 input 目录。

为什么需要这一步（都是实测踩过的坑）：
1. **只读属性**：从只读附件复制来的 wav 会带 `ReadOnly`，脚本读取时报
   `[WinError 5] 拒绝访问`；
2. **源文件被覆盖**：把源 wav 放在 `<out>/songs/` 下时，脚本裁剪前会先
   `unlink()` 同名目标（正好是源），随后 ffmpeg 报"没有找到文件"，源也被删。
   所以素材统一放在 `<项目>/input/`，与脚本的输出目录分开。
3. **中文路径**：官方沙箱对非 ASCII 路径敏感，素材仍放在项目 input/ 下由脚本
   再复制到临时 ASCII 工作区，不需要手工处理。

用法：
    python guzhu_prepare.py <项目名> <wav路径> <歌词txt路径> [歌曲显示名]
"""
import shutil
import sys
from pathlib import Path

ROOT = Path.cwd()


def main(argv):
    if len(argv) < 4:
        print(__doc__)
        return 2
    project_name, wav, lyric = argv[1], Path(argv[2]), Path(argv[3])
    display = argv[4] if len(argv) > 4 else wav.stem
    project = ROOT / 'work' / project_name
    input_dir = project / 'input'
    input_dir.mkdir(parents=True, exist_ok=True)

    # 歌曲：统一命名 <显示名>.wav
    song_target = input_dir / (display + wav.suffix.lower())
    if wav.resolve() != song_target.resolve():
        shutil.copyfile(wav, song_target)
    # 歌词：统一命名 <显示名>.txt
    lyric_target = input_dir / (display + '.txt')
    if lyric.resolve() != lyric_target.resolve():
        shutil.copyfile(lyric, lyric_target)

    # 清除只读（关键：否则后续读取会 WinError 5）
    cleared = []
    for path in [song_target, lyric_target] + list(input_dir.glob('background.png')):
        if path.is_file() and path.stat().st_file_attributes & 1:  # FILE_ATTRIBUTE_READONLY
            path.chmod(0o666)
            cleared.append(path.name)

    print('项目目录: %s' % project)
    print('歌曲: %s (%.2f MB)' % (song_target.name, song_target.stat().st_size / 1048576))
    print('歌词: %s' % lyric_target.name)
    if cleared:
        print('已清除只读: %s' % '、'.join(cleared))
    print()
    print('注意：素材必须留在 input/ 下，不要放进 out_dir/songs/（会被脚本覆盖）。')
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
