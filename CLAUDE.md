---
title: 佳佳短视频生产系统
description: Claude Code 驱动的个人IP短视频生产系统，打造"佳佳 = 上海板块分析专家"，主攻微信视频号 + 小红书
tags: [video, script, real-estate, content-creation, personal-ip]
---

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 系统定位

Claude Code 驱动的个人IP短视频生产系统。打造 **"佳佳 = 上海板块分析专家"**，主攻微信视频号 + 小红书。

- Claude 负责：创意决策（理解素材、定中心思想、写脚本、分析反馈、战略规划）
- Python 负责：数据计算（策略决策、记录存储、洞察生成）

**北极星指标**：不是粉丝量，是**优质客户转化**——从视频到加微信到最终成交。
**当前阶段策略**：先积累话语权。知识型内容建立"这个人比我还懂"的认知，转化在信任建立后自然发生。

## 长期战略（三阶段）

| 阶段 | 时间 | 目标 |
| ---- | ---- | ---- |
| 验证期 | 第1-8周 | 找到"哪种内容吸引对的人" **← 当前** |
| 深耕期 | 第9-24周 | 把一个已验证模式做到极致 |
| 破圈期 | 第25周+ | 从算法推荐到社交推荐 |

**阶段切换条件**：连续3条获有效私信 + 该模式无选题焦虑 + 至少2-3个客户因视频而联系。

## 人设铁律（每次生成必遵）

以下从 `config/persona.json` 提炼，细节以该文件为准。

**违禁词（12个）**：家人们、绝绝子、震惊、重磅、赶紧、手慢无、错过不再、必看、血赚、抢疯了、暴涨、暴跌

**禁用表达**：爆款/神盘/顶级/天花板（hype类）、赶紧下手/手慢就没了（urgency类）、再不上车就晚了（fear类）

**偏好句式**：我建议、我觉得、你可以考虑、不妨看看、如果不介意、说实话、说白了、其实就一点

**语言风格**：朋友聊天式——像在跟朋友分享发现，不是老师上课，不是中介推销。知识型内容的骨架是数据和判断，但表达方式仍然轻松自然。

**CTA铁律**：视频里只引导点赞/关注/收藏，绝不流露"找我买房"。转化在内容之外自然发生。

**知识型内容四条铁律**：
1. **每期必须有可验证的数据**——至少给出3个具体数字（均价、成交量、房龄、户型占比等）
2. **每期必须给出判断**——不是罗列数据，是"这个数据意味着什么"
3. **每个小区必须讲缺点**——没有十全十美的小区，回避缺点就是推销
4. **不推荐，只分析**——"适合XX类型的人"代替"推荐买这里"

**核心价值观**：不催单 / 帮客户筛选而非推销 / 用真实数据说话 / 承认不完美 / 站在客户立场

**情感杠杆底线**（详见 `config/persona.json` emotional_lever_rules）：
- 允许：用具体数据解释变化、反驳观点给理由、揭示隐藏成本
- 禁止：预测房价走势断言、攻击同行人格、制造时间紧迫感

## 核心工作流

### ⛔ 审批关卡（最高优先级）

**素材提炼完毕后，必须等用户明确说"可以"/"继续"/"写吧"才能动手写脚本。**

### 脚本生成

用户要求写脚本时，调用 `script-writer` 技能（`.claude/skills/script-writer.md`）。该技能包含完整 9 步工作流：策略对齐 → 外部搜索 → 数据洞察 → 素材提炼 → 叙事结构设计 → 写脚本 → 验证 → 记录 → 反馈。

### 视频剪辑

脚本和拍摄完成后，用户说"剪这条"触发 `video-editor` 技能（`.claude/skills/video-editor.md`）。

### 抖音分析

用户给抖音链接时，调用 `douyin-extract` 技能（`.claude/skills/douyin-extract.md`）。

## 环境依赖

**系统工具**：FFmpeg（需在 PATH 中）

**Python 包**（无 requirements.txt，按需安装）：
- `openai-whisper` — `video_editor.py` 语音转写
- `ffmpeg-python` — `douyin_extractor.py` 音频提取
- `requests` — `douyin_extractor.py` HTTP 请求

**可选环境变量**：`SILICONFLOW_API_KEY=sk-xxx` — `douyin_extractor.py --asr` 需要

## 常用命令

```bash
python engine.py status                                     # 今日策略/支柱/格式推荐
python engine.py status --no-venue                          # 同上，假设无法进入房源（实拍→口播降级）
python engine.py history [n]                                # 查看最近 n 条生成记录（默认10）
python engine.py series [板块]                              # 查看系列拍摄进度
python engine.py listings [小区名]                          # 查询优质房源表（实时挂牌数据+分数分布）
python engine.py analyze                                    # 分析已发布数据（需≥3条）
python viral_validator.py <脚本路径>                         # 9维爆款验证（27分制）
python pleasure_scorer.py <脚本路径>                         # 爽点评分（12分制）
python douyin_extractor.py <链接> --asr --comments           # 提取抖音口播+评论
python video_editor.py <脚本> <素材>                          # 全自动剪辑
python video_editor.py <脚本> <素材> -o <输出路径>             # 指定输出路径
python video_editor.py <素材> --transcribe-only               # 只转录素材
python video_editor.py <脚本> --plan-only                    # 只出剪辑计划
python video_editor.py <脚本> <素材> --align-only             # 只对齐脚本与素材，输出JSON
python video_editor.py <脚本> <素材> --dry-run                # 只生成指令不渲染
python video_editor.py <脚本> <素材> --font <黑体.ttf> --bgm <BGM.mp3>  # 带字体+BGM
```

**记录到 history.json**：
```bash
# 生成后记录
python -c "from engine import VideoEngine; e = VideoEngine(); e.record_generation({'strategy':'专业分析','pillar':'Property','video_format':'property_walk','topic':'<标题>','word_count':350,'duration_sec':90,'pleasure_score':8,'community':'<小区名>','district':'<板块>','series':'<系列名>','episode':1})"

# 发布后回填播放数据
python -c "from engine import VideoEngine; e = VideoEngine(); e.record_feedback('YYYY-MM-DD', {'views':1200,'completion_rate':0.45,'engagement_rate':0.038,'likes':56,'comments':12,'shares':8})"
```

> `viral_validator.py` 自动加载 `config/persona.json` 做人设违禁词检测。
> `record_generation` 按日期 upsert，同一天多条脚本后一条覆盖前一条。
> `history.json` 的 `max_window: 30` 会丢弃旧记录，长期趋势分析需在 25 条时备份或调大 `max_window`。
> `--transcribe-only` 模式下位置参数不同：`python video_editor.py <素材> --transcribe-only`。

## 平台合规

- 敏感词替换：投资→资产配置，升值→保值，抄底→入手时机
- 绝对化用语软化：千万别买→建议谨慎考虑
- 引流话术：私信我/加微信→评论区交流（引导关注/点赞可以做，不属于引流敏感词）

## 文件结构（关键文件）

```text
├── CLAUDE.md                        # 本文件（身份+规则）
├── engine.py                        # 策略引擎（status/record/analyze）
├── video_editor.py                  # 视频剪辑引擎
├── viral_validator.py               # 9维爆款验证器
├── pleasure_scorer.py               # 爽点评分器
├── douyin_extractor.py              # 抖音文案提取
├── config/
│   ├── persona.json                 # 人设配置
│   └── video_format_matrix.json     # 画面形式决策矩阵
├── data/
│   ├── history.json                 # 生成记录+发布数据
│   └── insights.json                # 自动洞察
├── memory/
│   ├── layer1-identity/             # 定位、核心观点
│   ├── layer2-strategy/             # 内容模式、复盘、竞品、CTA策略
│   ├── layer3-execution/            # 文案技巧、钩子库、金句记录、拍摄指南
│   │   └── video-editing-knowledge/ # 剪辑知识库（BGM/字体/字幕/布局/音效）
│   └── layer4-feedback/             # 客户咨询来源
└── .claude/skills/
    ├── script-writer.md             # ★ 脚本生成技能（完整9步工作流）
    ├── douyin-extract.md            # 抖音提取技能
    └── video-editor.md              # 视频自动剪辑技能
```

## 每周复盘

每5-7天跑 `python engine.py analyze`，汇报策略互动率、完播率、趋势、下周建议。每4周额外检查定位修正、客户来源质量、赛道变化、阶段切换判断，写入 `memory/layer2-strategy/phase-review.md`。
