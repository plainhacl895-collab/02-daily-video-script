# 音效使用指南

## 音效的作用

音效不是装饰，是**标点符号**。它在三个层面起作用：
1. **注意力引导**: 告诉观众"这里重要"
2. **节奏感**: 分隔段落、标记转场
3. **情绪强化**: 惊喜、紧张、轻松

## 短视频常用音效类型

| 类型 | 使用场景 | 示例关键词 |
|------|----------|------------|
| 转场 whoosh | 段落切换 | whoosh, swoosh, transition |
| 提示/强调 | 关键数字、金句出现 | pop, ding, notification |
| 氛围铺垫 | 情绪转换 | rise, drone, atmosphere |
| 动作音 | 画面动作同步 | click, tap, impact |
| 喜剧音 | 反转、吐槽 | comedy, funny, cartoon |

## 使用频率

- **60 秒视频**: 2-4 个音效就够了
- **90 秒视频**: 3-6 个
- **原则**: 宁少勿多。每多一个音效，多一分廉价感

## 常用音效库

| 来源 | 特点 | 获取方式 |
|------|------|----------|
| 小森平音效包 | 2000+ 免费可商用 | 官网下载 |
| Mixkit | 高质量，免费商用 | mixkit.co |
| 耳聆网 | 国内实地录音 | ear0.com |
| Pixabay | 一站式免版权 | pixabay.com |

## FFmpeg 音效混入

```bash
# 在 12.5 秒处混入一个 0.3 秒的音效
ffmpeg -i video.mp4 -i effect.wav \
  -filter_complex "[1:a]adelay=12500|12500,volume=0.6[fx];[0:a][fx]amix=inputs=2:duration=first" \
  -c:v copy output.mp4
```

需要在项目中搭建本地音效库 (fonts/ 同级目录 `sfx/`)。
