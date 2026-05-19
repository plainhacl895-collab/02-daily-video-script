---
name: douyin-extract
description: 提取抖音视频的完整信息——视频描述、作者数据、互动指标 + ASR 语音转文字获取口播文案
---

# 抖音视频文案提取

从抖音分享链接中提取视频信息，支持两种模式：

- **基础模式**：视频描述、作者信息、点赞/评论/收藏/分享数据、话题标签、时长
- **ASR 模式**：基础信息 + 下载视频 → 提取音频 → AI 语音识别获取完整口播文案
- **评论模式**：基础信息 + 抓取热门评论（含点赞数、回复内容）

## 使用方式

用户提供抖音分享链接（如 `https://v.douyin.com/xxxxx/`），默认用 **ASR 模式** 提取完整口播文案。

## 执行流程

### 1. 确认 API Key

检查环境变量 `SILICONFLOW_API_KEY`，当前值为用户级环境变量中已配置的 Key。如果当前终端未加载，运行时手动传入：

```powershell
$env:SILICONFLOW_API_KEY = "sk-kndroriirpnbtxzqsgdhvpsycmrlpqtnfslsutzlhhlrzgkb"
```

### 2. 运行提取

```bash
python douyin_extractor.py "<用户提供的链接>" --asr
```

超时时间设为 300000ms（5分钟），因为需要下载视频 + ASR 识别。

### 3. 呈现结果

将提取结果整理为清晰格式展示给用户：
- 作者、签名、作品数
- 点赞/评论/收藏/分享数据
- 完整口播文案（ASR）
- 视频描述（对比参考）
- 标签、时长

### 4. 错误处理

- 如遇 `ModuleNotFoundError: No module named 'ffmpeg'`：执行 `python -m pip install ffmpeg-python`
- 如遇 `SILICONFLOW_API_KEY` 未设置：提示用户提供 API Key 并设置环境变量
- 如遇下载失败：先用基础模式（不带 `--asr`）获取视频信息，告知用户再试

## 注意事项

- 仅支持抖音公开视频的分享链接
- ASR 识别结果可能包含少量同音字错误，不影响理解
- 视频文件下载后在临时目录处理，处理完自动清理
