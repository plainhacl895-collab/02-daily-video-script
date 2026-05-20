"""
视频自动剪辑引擎 v1.0

三项核心能力：
1. 脚本解析 — 从 daily-script .md 提取时间线标注（[画面][字幕叠加][语速]）
2. 素材对齐 — Whisper 转录口播素材 → 与脚本文本对齐 → 定位每段在素材中的时间戳
3. FFmpeg 组装 — 自动生成并执行 FFmpeg 命令，输出成片

用法：
    python video_editor.py <脚本路径> <素材路径> [--output 输出路径] [--dry-run]

示例：
    python video_editor.py daily-script-2026-05-18.md raw_footage.mp4
    python video_editor.py daily-script-2026-05-18.md raw_footage.mp4 --dry-run  # 只生成指令，不渲染
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# 1. 脚本解析
# ---------------------------------------------------------------------------

def parse_script(script_path: str) -> list[dict]:
    """解析 daily-script .md，提取每个段落的画面/字幕/语速标注。

    返回列表，每项: {
        'section': '开场' | '分析' | '金句' | '结尾',
        'text': '口播文案原文',
        'visual': '画面描述',
        'subtitle_overlay': '字幕叠层文字或None',
        'speed': '快'|'正常'|'慢',
        'emphasis': True|False,  # 是否需要画面放大
    }
    """
    with open(script_path, encoding='utf-8') as f:
        content = f.read()

    # 切掉 YAML frontmatter
    if content.startswith('---'):
        parts = content.split('---', 2)
        content = parts[2] if len(parts) > 2 else content

    segments = []
    # 按 ## 标题切分段落
    section_blocks = re.split(r'\n## ', content)
    for block in section_blocks:
        if not block.strip():
            continue
        lines = block.strip().split('\n')
        # 第一行是标题
        title = lines[0].strip().lstrip('#').strip()
        body = '\n'.join(lines[1:]).strip()
        if not body:
            continue

        # 提取标注
        visual_match = re.search(r'\[画面:\s*([^\]]+)\]', body)
        subtitle_match = re.search(r'\[字幕叠加:\s*([^\]]+)\]', body)
        speed_match = re.search(r'\[语速:\s*([^\]]+)\]', body)

        # 提取纯口播文本（去掉所有 [标注]）
        text = re.sub(r'\[画面:[^\]]*\]', '', body)
        text = re.sub(r'\[字幕叠加:[^\]]*\]', '', text)
        text = re.sub(r'\[语速:[^\]]*\]', '', text)
        text = text.strip()

        if not text:
            continue

        seg = {
            'section': title,
            'text': text,
            'visual': visual_match.group(1).strip() if visual_match else None,
            'subtitle_overlay': subtitle_match.group(1).strip() if subtitle_match else None,
            'speed': speed_match.group(1).strip() if speed_match else '正常',
            'emphasis': title == '金句' or (subtitle_match is not None),
        }
        segments.append(seg)

    return segments


# ---------------------------------------------------------------------------
# 2. 素材对齐（Whisper）
# ---------------------------------------------------------------------------

def transcribe_footage(video_path: str) -> list[dict]:
    """用 Whisper 转写素材，返回词级时间戳列表。

    每项: {'word': '...', 'start': 0.0, 'end': 0.0}
    """
    import whisper
    # 用 base 模型平衡速度和精度，中文口播 base 足够
    model = whisper.load_model('base')
    result = model.transcribe(video_path, language='zh', word_timestamps=True)

    words = []
    for seg in result.get('segments', []):
        seg_text = seg['text'].strip()
        seg_start = seg['start']
        seg_end = seg['end']
        # 如果是整段没有分词时间戳，用整段
        if not seg.get('words'):
            words.append({'word': seg_text, 'start': seg_start, 'end': seg_end})
            continue
        for w in seg['words']:
            words.append({
                'word': w['word'].strip(),
                'start': w['start'],
                'end': w['end'],
            })
    return words


def simple_text_match(script_text: str, whisper_words: list[dict]) -> tuple[float, float]:
    """在 whisper 转写结果中定位脚本文本的时间区间。

    用滑动窗口对 whisper 连续文本做模糊匹配，找到最佳对齐位置。
    返回 (start_time, end_time)。
    """
    # 将脚本文字清理
    clean_script = re.sub(r'[^一-鿿\w]', '', script_text)
    if len(clean_script) < 3:
        return (0.0, 0.0)

    # 用最长公共子序列找最佳匹配
    windows = []
    for i, w in enumerate(whisper_words):
        # 以每个词为起点，构造长度为 len(clean_script)*2 的窗口
        window_text = ''
        window_start = w['start']
        window_end = w['end']
        for j in range(i, min(i + 200, len(whisper_words))):
            window_text += whisper_words[j]['word']
            window_end = whisper_words[j]['end']
            # 每加一个词检查一次匹配度
            clean_window = re.sub(r'[^一-鿿\w]', '', window_text)
            if len(clean_window) >= len(clean_script):
                break
        else:
            continue
        clean_window = re.sub(r'[^一-鿿\w]', '', window_text)

        # 计算匹配长度
        match_len = _lcs_length(clean_script, clean_window)
        ratio = match_len / max(len(clean_script), 1)
        windows.append((ratio, window_start, window_end, i))

    if not windows:
        return (0.0, 0.0)

    windows.sort(reverse=True)
    best_ratio, t_start, t_end, _ = windows[0]

    if best_ratio < 0.3:
        print(f'  ⚠ 匹配度低 ({best_ratio:.1%})，可能需要手动调整')

    return (t_start, t_end)


def _lcs_length(a: str, b: str) -> int:
    """简化版最长公共子序列长度（足够短文本用）。"""
    m, n = len(a), len(b)
    # 限制长度，避免超慢
    if m > 300:
        a = a[:300]
        m = 300
    if n > 600:
        b = b[:600]
        n = 600
    prev = [0] * (n + 1)
    for i in range(1, m + 1):
        curr = [0] * (n + 1)
        for j in range(1, n + 1):
            if a[i - 1] == b[j - 1]:
                curr[j] = prev[j - 1] + 1
            else:
                curr[j] = max(prev[j], curr[j - 1])
        prev = curr
    return prev[n]


# ---------------------------------------------------------------------------
# 3. FFmpeg 指令生成
# ---------------------------------------------------------------------------

def speed_to_ffmpeg(speed: str) -> str:
    """语速 → FFmpeg setpts 参数。兼容带注释的标注（如"慢，停顿"）。"""
    if '快' in speed:
        return 'setpts=0.85*PTS'
    elif '慢' in speed:
        return 'setpts=1.15*PTS'
    return ''


def speed_factor(speed: str) -> float:
    """语速 → 倍率因子。"""
    if '快' in speed:
        return 0.85
    elif '慢' in speed:
        return 1.15
    return 1.0


def subtitle_to_ass(text: str, start_sec: float, end_sec: float,
                    style: str = 'normal') -> str:
    """生成一条 ASS 字幕事件行。

    style: 'normal' | 'emphasis' | 'jinju'
    """
    from datetime import timedelta

    def _fmt(sec):
        td = timedelta(seconds=sec)
        total_sec = int(td.total_seconds())
        h = total_sec // 3600
        m = (total_sec % 3600) // 60
        s = total_sec % 60
        cs = int((sec - int(sec)) * 100)
        return f'{h}:{m:02d}:{s:02d}.{cs:02d}'

    styles = {
        'normal': r'{\fs55\bord2\shad1\c&HFFFFFF&\3c&H000000&}',
        'emphasis': r'{\fs80\bord3\shad1\c&H00FFFF&\3c&H000000&\an5}',
        'jinju': r'{\fs90\bord4\shad1\c&HFFFFFF&\3c&H000000&\an5}',
    }
    st = styles.get(style, styles['normal'])
    start_tag = _fmt(start_sec)
    end_tag = _fmt(end_sec)
    return f'Dialogue: 0,{start_tag},{end_tag},{style},,0,0,0,,{st}{text}'


def build_ass_header(width: int = 1080, height: int = 1920) -> str:
    """ASS 字幕文件头（竖屏 1080×1920，底部常规字幕 + 居中强调/金句）。"""
    return f"""[Script Info]
Title: 自动生成字幕
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: normal,思源黑体,55,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,1,2,100,100,60,1
Style: emphasis,思源黑体,80,&H0000FFFF,&H000000FF,&H00000000,&H00000000,1,0,0,0,100,100,0,0,1,3,1,5,100,100,60,1
Style: jinju,思源黑体,90,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,1,0,0,0,110,110,0,0,1,4,1,5,100,100,60,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def build_ffmpeg_filter(segments: list[dict], segment_times: list[tuple[float, float]],
                        video_width: int = 1080, video_height: int = 1920) -> str:
    """生成完整的 FFmpeg filter_complex 字符串。

    包括：trim + setpts（语速） + scale（画面放大） + concat + subtitles
    """
    filter_parts = []
    trim_labels = []

    for i, (seg, (t_start, t_end)) in enumerate(zip(segments, segment_times)):
        label = f'v{i}'
        duration = t_end - t_start
        if duration <= 0:
            continue

        # trim
        trim_parts = [f'[{label}_in]']

        # 语速
        speed_filter = speed_to_ffmpeg(seg['speed'])
        if speed_filter:
            trim_parts.append(speed_filter)

        # 画面放大（金句/强调处 110%）
        if seg.get('emphasis'):
            trim_parts.append(
                f'scale={int(video_width*1.1)}:{int(video_height*1.1)}:force_original_aspect_ratio=increase,'
                f'crop={video_width}:{video_height}'
            )

        filter_parts.append(f'[{label}_in] {",".join(trim_parts[1:]) if len(trim_parts) > 1 else "copy"} [{label}]')
        trim_labels.append(label)

    # 注意：完整的 filter_complex 还需 trim 输入，这里返回简化版
    # 实际执行时用分段渲染 + concat 方案更稳定
    return '; '.join(filter_parts), trim_labels


# ---------------------------------------------------------------------------
# 4. 主流程
# ---------------------------------------------------------------------------

def generate_timeline(script_path: str, video_path: str) -> dict:
    """核心：从脚本 + 素材生成精确时间线。

    返回 {
        'segments': [...],        # 脚本段落
        'timeline': [(start, end), ...],  # 每段在素材中的时间
        'total_duration': float,  # 预估总时长
    }
    """
    print('=' * 60)
    print('  视频自动剪辑引擎 v1.0')
    print('=' * 60)

    # Step 1: 解析脚本
    print('\n[1/3] 解析脚本标注...')
    segments = parse_script(script_path)
    print(f'  共 {len(segments)} 个段落：')
    for seg in segments:
        print(f'    [{seg["section"]}] {seg["text"][:40]}... '
              f'语速={seg["speed"]} 强调={seg["emphasis"]}')

    # Step 2: Whisper 转写
    print('\n[2/3] Whisper 转写素材...')
    words = transcribe_footage(video_path)
    full_text = ''.join(w['word'] for w in words)
    print(f'  转写字数: {len(full_text)} 字符')
    print(f'  素材时长: {words[-1]["end"]:.1f}s')

    # Step 3: 对齐
    print('\n[3/3] 对齐脚本与素材...')
    timeline = []
    for seg in segments:
        t_start, t_end = simple_text_match(seg['text'], words)
        timeline.append((t_start, t_end))
        dur = t_end - t_start
        print(f'  [{seg["section"]}] {t_start:.1f}s → {t_end:.1f}s (时长 {dur:.1f}s)')

    total = sum(max(e - s, 0) for s, e in timeline)
    print(f'\n  预估成片时长: {total:.1f}s')

    return {
        'segments': segments,
        'timeline': timeline,
        'total_duration': total,
    }


def render_video(video_path: str, segments: list[dict],
                 timeline: list[tuple[float, float]],
                 output_path: str, bgm_path: Optional[str] = None) -> str:
    """用 FFmpeg 逐段裁剪 + concat 渲染最终视频。

    策略：每段独立裁剪→统一 concat→烧录字幕，比单一 filter_complex 更稳定。
    """
    import shutil

    # 检查 FFmpeg
    if not shutil.which('ffmpeg'):
        raise RuntimeError('未找到 ffmpeg，请确认已安装并加入 PATH')

    tmpdir = tempfile.mkdtemp(prefix='video_edit_')
    clip_files = []

    # 获取原视频尺寸
    probe_cmd = [
        'ffprobe', '-v', 'quiet', '-select_streams', 'v:0',
        '-show_entries', 'stream=width,height', '-of', 'csv=p=0', video_path
    ]
    result = subprocess.run(probe_cmd, capture_output=True, text=True)
    try:
        w, h = result.stdout.strip().split(',')
        width, height = int(w), int(h)
    except Exception:
        width, height = 1080, 1920

    # --- 逐段裁剪 ---
    for i, (seg, (t_start, t_end)) in enumerate(zip(segments, timeline)):
        duration = t_end - t_start
        if duration <= 0.05:
            continue

        clip_path = os.path.join(tmpdir, f'clip_{i:03d}.mp4')

        filters = []
        # 语速
        sf = speed_factor(seg['speed'])
        if sf != 1.0:
            filters.append(f'setpts={sf}*PTS')

        # 画面放大
        if seg.get('emphasis'):
            filters.append(
                f'scale={int(width*1.1)}:{int(height*1.1)}:force_original_aspect_ratio=increase,'
                f'crop={width}:{height}'
            )

        cmd = ['ffmpeg', '-y', '-ss', str(t_start), '-t', str(duration),
               '-i', video_path, '-c:v', 'libx264', '-crf', '20',
               '-preset', 'fast', '-pix_fmt', 'yuv420p',
               '-c:a', 'aac', '-b:a', '128k']

        if filters:
            cmd.insert(-8, '-vf')
            cmd.insert(-7, ','.join(filters))

        cmd.append(clip_path)
        subprocess.run(cmd, capture_output=True)
        clip_files.append(clip_path)

    if not clip_files:
        raise RuntimeError('没有可渲染的片段，请检查脚本与素材是否匹配')

    # --- Concat ---
    concat_list = os.path.join(tmpdir, 'concat.txt')
    with open(concat_list, 'w', encoding='utf-8') as f:
        for cf in clip_files:
            f.write(f"file '{cf}'\n")

    concat_video = os.path.join(tmpdir, 'concat.mp4')
    subprocess.run([
        'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
        '-i', concat_list, '-c', 'copy', concat_video,
    ], capture_output=True)

    # --- 字幕 ---
    sub_path = os.path.join(tmpdir, 'subtitle.ass')
    with open(sub_path, 'w', encoding='utf-8') as f:
        f.write(build_ass_header(width, height))
        # 生成字幕事件
        current_time = 0.0
        for seg, (_, t_end) in zip(segments, timeline):
            dur = (t_end - (timeline[segments.index(seg)][0]))
            if dur <= 0:
                continue
            dur = dur / speed_factor(seg['speed'])
            seg_end = current_time + dur

            # 断句字幕
            sentences = re.split(r'[，。！？]', seg['text'])
            sentence_time = current_time
            for s in sentences:
                s = s.strip()
                if not s:
                    continue
                # 估算每句时长（按字数）
                char_dur = max(len(s) * 0.25, 1.5)
                s_end = min(sentence_time + char_dur, seg_end)
                f.write(subtitle_to_ass(s, sentence_time, s_end, 'normal') + '\n')
                sentence_time = s_end

            # 强调字幕
            if seg.get('subtitle_overlay'):
                overlay = seg['subtitle_overlay']
                style = 'jinju' if seg['section'] == '金句' else 'emphasis'
                overlay_start = current_time + dur * 0.15
                overlay_end = overlay_start + min(2.5, dur * 0.7)
                f.write(subtitle_to_ass(overlay, overlay_start, overlay_end, style) + '\n')

            current_time = seg_end

    # --- BGM ---
    audio_inputs = ['-i', concat_video]
    audio_filters = []
    if bgm_path and os.path.exists(bgm_path):
        audio_inputs.extend(['-i', bgm_path])
        # 获取 concat 时长
        dur_cmd = ['ffprobe', '-v', 'quiet', '-show_entries',
                   'format=duration', '-of', 'csv=p=0', concat_video]
        dur_result = subprocess.run(dur_cmd, capture_output=True, text=True)
        total_dur = float(dur_result.stdout.strip())
        # BGM: 1s 淡入，1s 淡出，音量 30%
        audio_filters = [
            '-filter_complex',
            f'[1:a]afade=t=in:d=1,afade=t=out:st={total_dur-1}:d=1,volume=0.3[bgm];'
            f'[0:a][bgm]amix=inputs=2:duration=first[audio]',
            '-map', '0:v', '-map', '[audio]',
        ]

    cmd = ['ffmpeg', '-y', '-i', concat_video] + audio_inputs + [
        '-vf', f'ass={sub_path}',
    ] + audio_filters + [
        '-c:v', 'libx264', '-crf', '20', '-preset', 'fast', '-pix_fmt', 'yuv420p',
        '-c:a', 'aac', '-b:a', '128k', output_path,
    ]

    # 如果没有 BGM，简化命令
    if not (bgm_path and os.path.exists(bgm_path)):
        cmd = ['ffmpeg', '-y', '-i', concat_video,
               '-vf', f'ass={sub_path}',
               '-c:v', 'libx264', '-crf', '20', '-preset', 'fast', '-pix_fmt', 'yuv420p',
               '-c:a', 'copy', output_path]

    print('\n[渲染] 正在合成最终视频...')
    subprocess.run(cmd, capture_output=True)

    # 清理
    import shutil as _shutil
    _shutil.rmtree(tmpdir, ignore_errors=True)

    return output_path


# ---------------------------------------------------------------------------
# 5. CLI
# ---------------------------------------------------------------------------

def main():
    # 强制 UTF-8 输出
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

    parser = argparse.ArgumentParser(
        description='视频自动剪辑引擎 — 脚本 + 素材 → 成片')
    parser.add_argument('script', help='daily-script .md 路径')
    parser.add_argument('footage', help='口播素材视频路径')
    parser.add_argument('--output', '-o', default=None, help='输出路径（默认桌面）')
    parser.add_argument('--bgm', default=None, help='BGM 音频文件路径')
    parser.add_argument('--dry-run', action='store_true', help='只生成时间线，不渲染')
    parser.add_argument('--align-only', action='store_true', help='只做对齐，输出时间线 JSON')

    args = parser.parse_args()

    if not os.path.exists(args.script):
        print(f'错误：脚本文件不存在 — {args.script}')
        sys.exit(1)
    if not os.path.exists(args.footage):
        print(f'错误：素材文件不存在 — {args.footage}')
        sys.exit(1)

    result = generate_timeline(args.script, args.footage)

    if args.align_only:
        # 输出 JSON 供 Claude 阅读
        output = {
            'script': args.script,
            'footage': args.footage,
            'segments': [
                {
                    'section': s['section'],
                    'text': s['text'],
                    'speed': s['speed'],
                    'emphasis': s['emphasis'],
                    'subtitle_overlay': s['subtitle_overlay'],
                    'time_start': tl[0],
                    'time_end': tl[1],
                    'duration': tl[1] - tl[0],
                }
                for s, tl in zip(result['segments'], result['timeline'])
            ],
            'total_duration': result['total_duration'],
        }
        print('\n' + json.dumps(output, ensure_ascii=False, indent=2))
        return

    if args.dry_run:
        print('\n[Dry-run] 跳过渲染。实际运行时将生成视频文件。')
        return

    # 确定输出路径
    if args.output:
        output_path = args.output
    else:
        desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
        script_name = os.path.splitext(os.path.basename(args.script))[0]
        output_path = os.path.join(desktop, f'{script_name}-成片.mp4')

    render_video(args.footage, result['segments'], result['timeline'],
                 output_path, args.bgm)
    print(f'\n✅ 完成！成片已输出到: {output_path}')


if __name__ == '__main__':
    main()
