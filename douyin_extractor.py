#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抖音视频信息提取器 + ASR 语音转文字（进阶版）
从分享链接提取视频描述、作者信息、数据指标 + 完整口播文案（AI 语音识别）

用法:
  python douyin_extractor.py <抖音分享链接>              # 基础版：提取描述
  python douyin_extractor.py <抖音分享链接> --asr        # 进阶版：提取完整口播文案
"""

import re
import json
import sys
import io
import os
import tempfile
import shutil
import requests
from pathlib import Path
from typing import Optional

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) EdgiOS/121.0.2277.107 Version/17.0 Mobile/15E148 Safari/604.1'
}

SILICONFLOW_API = "https://api.siliconflow.cn/v1/audio/transcriptions"
ASR_MODEL = "FunAudioLLM/SenseVoiceSmall"


def extract_video_info(share_url: str) -> dict:
    """从抖音分享链接提取视频信息，无需 API Key"""
    r = requests.get(share_url, headers=HEADERS, allow_redirects=True)
    video_id = r.url.split("?")[0].strip("/").split("/")[-1]

    ies_url = f'https://www.iesdouyin.com/share/video/{video_id}'
    r = requests.get(ies_url, headers=HEADERS)
    r.raise_for_status()

    pattern = re.compile(r"window\._ROUTER_DATA\s*=\s*(.*?)</script>", re.DOTALL)
    match = pattern.search(r.text)
    if not match:
        raise ValueError("无法从页面提取视频数据")

    data = json.loads(match.group(1).strip())
    loader = data.get("loaderData", {})

    video_info = None
    for key in loader:
        if "video" in key and "page" in key:
            video_info = loader[key].get("videoInfoRes")
            break

    if not video_info:
        raise ValueError("无法解析视频信息")

    item = video_info["item_list"][0]
    author = item["author"]
    stats = item.get("statistics", {})
    video = item["video"]

    return {
        "video_id": video_id,
        "desc": item.get("desc", ""),
        "create_time": item.get("create_time", 0),
        "author": {
            "nickname": author.get("nickname", ""),
            "signature": author.get("signature", ""),
            "unique_id": author.get("unique_id", ""),
            "aweme_count": author.get("aweme_count", 0),
        },
        "stats": {
            "digg_count": stats.get("digg_count", 0),
            "comment_count": stats.get("comment_count", 0),
            "play_count": stats.get("play_count", 0),
            "share_count": stats.get("share_count", 0),
            "collect_count": stats.get("collect_count", 0),
        },
        "video_url": video["play_addr"]["url_list"][0].replace("playwm", "play"),
        "duration": video.get("duration", 0),
        "hashtags": [
            te.get("hashtag_name", "")
            for te in item.get("text_extra", [])
            if "hashtag_name" in te
        ],
    }


def extract_audio(video_path: Path, output_path: Path) -> Path:
    """从视频提取音频为 MP3"""
    import ffmpeg
    (
        ffmpeg
        .input(str(video_path))
        .output(str(output_path), acodec='libmp3lame', q=0)
        .run(capture_stdout=True, capture_stderr=True, overwrite_output=True)
    )
    return output_path


def transcribe_audio(audio_path: Path, api_key: str) -> str:
    """使用硅基流动 SenseVoice 转文字"""
    with open(audio_path, 'rb') as f:
        response = requests.post(
            SILICONFLOW_API,
            files={
                'file': (audio_path.name, f, 'audio/mpeg'),
                'model': (None, ASR_MODEL),
            },
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=120,
        )
    response.raise_for_status()
    result = response.json()
    return result.get('text', response.text)


def asr_extract(share_url: str, api_key: str) -> dict:
    """进阶版：提取完整口播文案（下载视频 + ASR）"""
    print(">>> 解析视频信息...")
    info = extract_video_info(share_url)

    temp_dir = Path(tempfile.mkdtemp())
    try:
        # 下载视频
        print(f">>> 下载视频: {info['desc'][:40]}...")
        video_path = temp_dir / f"{info['video_id']}.mp4"
        r = requests.get(info['video_url'], headers=HEADERS, stream=True, timeout=120)
        r.raise_for_status()
        total = int(r.headers.get('content-length', 0))
        downloaded = 0
        with open(video_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total:
                        pct = downloaded / total * 100
                        print(f"\r  下载进度: {pct:.0f}%", end="", flush=True)
        print()

        # 提取音频
        print(">>> 提取音频...")
        audio_path = temp_dir / f"{info['video_id']}.mp3"
        extract_audio(video_path, audio_path)

        # ASR 转文字
        print(">>> AI 语音识别...")
        transcript = transcribe_audio(audio_path, api_key)

        info["transcript"] = transcript
        return info

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def print_info(info: dict):
    """打印提取结果"""
    print("=" * 60)
    print(f"【作者】{info['author']['nickname']}")
    print(f"  签名: {info['author']['signature']}")
    print(f"  作品数: {info['author']['aweme_count']}")
    print()
    print(f"【数据】点赞 {info['stats']['digg_count']} | 评论 {info['stats']['comment_count']} | 收藏 {info['stats']['collect_count']} | 分享 {info['stats']['share_count']}")
    print()

    if info.get('transcript'):
        print(f"【🎙️ 完整口播文案 (ASR)】")
        print(info['transcript'])
        print()
        print(f"【📝 视频描述 (对比参考)】")
        print(info['desc'])
    else:
        print(f"【📝 文案/描述】")
        print(info['desc'])

    if info['hashtags']:
        print(f"\n【标签】{' '.join('#' + t for t in info['hashtags'])}")
    print(f"\n【视频ID】{info['video_id']}")
    print(f"【时长】{info['duration']}ms")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法:")
        print("  python douyin_extractor.py <抖音分享链接>              # 基础版")
        print("  python douyin_extractor.py <抖音分享链接> --asr        # 进阶版（ASR语音转文字）")
        sys.exit(1)

    url = sys.argv[1]
    use_asr = "--asr" in sys.argv

    if use_asr:
        api_key = os.environ.get("SILICONFLOW_API_KEY", "")
        if not api_key:
            print("错误: 请设置环境变量 SILICONFLOW_API_KEY")
            print("  export SILICONFLOW_API_KEY=sk-xxx")
            sys.exit(1)
        info = asr_extract(url, api_key)
    else:
        info = extract_video_info(url)

    print_info(info)
