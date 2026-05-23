# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 系统定位

Claude Code 驱动的个人IP短视频生产系统。打造 **"佳佳 = 上海改善置换专家"**，主攻微信视频号 + 小红书。

- Claude 负责：创意决策（理解素材、定中心思想、写脚本、分析反馈、战略规划）
- Python 负责：数据计算（策略决策、记录存储、洞察生成）

**北极星指标**：不是粉丝量，是**优质客户转化**——从视频到加微信到最终成交。

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

**语言风格**：朋友聊天式——像在跟朋友打电话，不是老师上课，不是中介推销。

**CTA铁律**：视频里只引导点赞/关注/收藏，绝不流露"找我买房"。转化在内容之外自然发生。

**核心价值观**：不催单 / 帮客户筛选而非推销 / 用真实数据说话 / 承认不完美 / 站在客户立场

**情感杠杆底线**（详见 `config/persona.json` emotional_lever_rules）：

- 允许：用具体数据解释变化、反驳观点给理由、揭示隐藏成本
- 禁止：预测房价走势断言、攻击同行人格、制造时间紧迫感

## 核心工作流

### ⛔ 审批关卡（最高优先级）

**素材提炼完毕后，必须等用户明确说"可以"/"继续"/"写吧"才能动手写脚本。** 用户可能在补充信息、可能想调整角度——没确认之前不动笔。这是铁律。

### Step 1 — 获取素材 + 跑引擎

```bash
python engine.py status    # 今日策略/支柱/格式推荐
```

用户给素材就直接用；没给素材先读 `memory/layer3-execution/material-source-guide.md` 按框架引导；引导失败读 `memory/layer3-execution/inspiration-topics.md` 从话题弹药库选题。抖音链接用 `python douyin_extractor.py <链接> --asr --comments` 提取，分析完技法写入 `memory/layer3-execution/competitor-learning-log.md`（不要直接改技能文件）。

### Step 2 — 素材提炼 + 准入检查

输出格式：

```text
## 素材提炼结果

**中心思想**：<一句话可争论的判断>
**目标观众**：资产配置型 / 改善自住型 / 首次入市型
**信息密度**：数字(有/无) / 冲突(有/无) / 决策点(有/无) / 反转(有/无)
**定位契合度**：高/中/低 — <理由>
**人设安全性**：有利 / 中性 / 不利 — <判断>
**画面可行性**：可实拍 / 可混剪 / 仅口播 — <理由>
**实物锚点**：<绑定的具体事物，无则标"无">
```

然后检查：钩子和中心思想是两回事——钩子是3秒开门，中心思想是整条视频论证的判断。

准入标准（五项至少满足四项）：可争论性、有具体信息、定位相关、可拍摄、有实物锚点。人设安全性"不利"则一票否决。

**→ 提交审批，等用户确认。**

### Step 3 — 写脚本

用户确认后，写 YAML frontmatter + 正文的 `.txt` 文件，保存到 `$env:USERPROFILE\Desktop\daily-script-YYYY-MM-DD.txt`。

结构：

```text
---
date: YYYY-MM-DD
format: talking_head | property_walk | mixed_montage
pillar: Market | Property | Story
strategy: 陪伴决策 | 专业分析 | 避坑指南 | 资源推荐
bgm: <风格描述>
scene: <拍摄场景>
shot: <机位描述>
word_count_target: <字数范围>
best_platform: <平台>
---

# 标题

## 开场（3秒钩子）
[画面:xxx] [语速:正常]

## 主体段落
每段只论证中心思想的一个侧面
[画面:xxx] [字幕叠加:xxx] [语速:xxx]

## 金句
从金句库选或即兴写
[画面:xxx] [语速:慢]

## 结尾
引导点赞/关注，不做成交暗示
[画面:xxx] [字幕叠加:关注引导]
```

每段必须标注 `[画面]` `[字幕叠加]` `[语速]`。字数按 `config/video_format_matrix.json` 中各格式建议。写前读 `memory/layer3-execution/copywriting-techniques.md` 自查清单。

### Step 4 — 验证 + 自查

```bash
python viral_validator.py <脚本路径>    # 9维爆款验证（27分制）
python pleasure_scorer.py <脚本路径>    # 爽点评分（12分制）
```

验证器是机械评分（字数含YAML标记，实际口播约减40-50%），18分以下若核心维度（钩子、中心思想）实际已到位可手动判断不盲目追分。

然后人设自查：违禁词扫一遍、语气是朋友聊天不、"smell test"（1000万预算客户读到每句话会觉得"帮我分析"还是"吓我"？）

### Step 5 — 记录到 history.json + 输出制作指南

通过 Python 调 `engine.record_generation(meta)` 记录（无 CLI 命令，需用 `python -c` 调用）。制作运营建议和拍摄清单参考 `memory/layer3-execution/production-playbook.md` 和 `solo-shooting-guide.md` 输出。

### Step 6 — 反馈录入

用户发布后更新 `data/history.json` 对应日期的 `performance` 字段。有客户通过视频来咨询 → 记录到 `memory/layer4-feedback/client-inquiry-log.md`。积累≥3条已发布数据后跑 `python engine.py analyze`。

## 常用命令

```bash
python engine.py status                                     # 今日策略/支柱/格式推荐
python engine.py analyze                                    # 分析已发布数据
python viral_validator.py <脚本路径>                         # 9维爆款验证
python pleasure_scorer.py <脚本路径>                         # 爽点评分
python douyin_extractor.py <链接> --asr --comments           # 提取抖音口播+评论
```

## 平台合规

- 敏感词替换：投资→资产配置，升值→保值，抄底→入手时机
- 绝对化用语软化：千万别买→建议谨慎考虑
- 引流话术：私信我/加微信→评论区交流（引导关注/点赞可以做，不属于引流敏感词）

## 文件结构（关键文件）

```text
├── CLAUDE.md                        # 本文件
├── engine.py                        # 策略引擎（status/record/analyze）
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
│   ├── layer3-execution/            # 文案技巧、钩子库、金句记录、拍摄指南、素材捕捉、制作运营
│   └── layer4-feedback/             # 客户咨询来源
└── .claude/skills/douyin-extract.md # 抖音提取技能
```

## 每周复盘

每5-7天跑 `python engine.py analyze`，汇报策略互动率、完播率、趋势、下周建议。每4周额外检查定位修正、客户来源质量、赛道变化、阶段切换判断，写入 `memory/layer2-strategy/phase-review.md`。
