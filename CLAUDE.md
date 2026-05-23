# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 系统定位

Claude Code 驱动的个人IP短视频生产系统。打造 **"佳佳 = 上海板块分析专家"**，主攻微信视频号 + 小红书。

- Claude 负责：创意决策（理解素材、定中心思想、写脚本、分析反馈、战略规划）
- Python 负责：数据计算（策略决策、记录存储、洞察生成）

**北极星指标**：不是粉丝量，是**优质客户转化**——从视频到加微信到最终成交。
**当前阶段策略**：先积累话语权。知识型内容建立"这个人比我还懂"的认知，转化在信任建立后自然发生。不急于在视频里转化，先用信息量和判断力把粉丝和权威做起来。

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

**知识型内容四条铁律**（V2 新增）：
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

**素材提炼完毕后，必须等用户明确说"可以"/"继续"/"写吧"才能动手写脚本。** 用户可能在补充信息、可能想调整角度——没确认之前不动笔。这是铁律。

### Step 1 — 获取素材 + 跑引擎

```bash
python engine.py status    # 今日策略/支柱/格式推荐
```

用户给素材就直接用；没给素材先读 `memory/layer3-execution/material-source-guide.md` 按框架引导；引导失败读 `memory/layer3-execution/inspiration-topics.md` 从话题弹药库选题。抖音链接用 `python douyin_extractor.py <链接> --asr --comments` 提取，分析完技法写入 `memory/layer3-execution/competitor-learning-log.md`（不要直接改技能文件）。

**V2 知识型内容优先**：如果有小区分析数据可用（来自 `03-shanghai-community-analysis` 项目或实地探盘），优先做小区深度分析，而非泛话题脚本。一个小区 = 一条视频，系列化输出。

### Step 1.5 — 战略对齐（每次生成前必做）

读 `memory/layer1-identity/positioning.md` 确认当前定位。
问自己：今天这条视频发布后，观众会记住"佳佳 = 上海板块分析专家"吗？
如果这条视频换个其他中介来念也没区别 → 定位没体现 → 换角度。

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

## 小区深度分析系列（V2 核心格式）

这是知识型转型后的主打内容格式。一个板块 = 一个系列，一个小区 = 一条视频。

### 系列规划

| 阶段 | 板块 | 目标小区数 | 优先级 |
|------|------|-----------|--------|
| 首发 | 长宁·天山 | 8-12个 | 最高 |
| 第二 | 长宁·古北 | 6-10个 | 高 |
| 第三 | 长宁·中山公园 | 5-8个 | 高 |
| 拓展 | 普陀/闵行/静安 | 每板块≥5个 | 中 |

### 单期结构模板

```
---
date: YYYY-MM-DD
format: property_walk | mixed_montage
pillar: Property
strategy: 专业分析
series: <板块名>小区系列
episode: <第X期>
bgm: <风格>
---
# 标题公式
"[板块名]的[小区名]，适合谁、不适合谁"
或 "[数字]个你可能不知道的[小区名]真相"

## 开场（3秒钩子）
用一组具体数字开门，不要用提问式
[画面:小区大门/航拍/标志性景观]

## 小区基本面（15-20s）
- 建成年份/房龄、总户数、容积率
- 主力户型面积段 + 当前挂牌均价
[画面:小区实拍/户型图] [字幕叠加:关键数字]

## 三个优点（20-25s）
每个优点配一个具体画面
[画面:对应的实拍画面] [字幕叠加:要点总结]

## 三个缺点（20-25s）
不回避，客观陈述
[画面:对应的实拍画面]

## 适合谁 + 不适合谁（10-15s）
- 适合：<人群画像 + 理由>
- 不适合：<人群画像 + 理由>
[字幕叠加:人群标签]

## 金句收尾（5-10s）
一句话判断，让观众记住这个小区
[画面:小区最佳角度] [语速:慢]

## 结尾
"下期想看哪个小区，评论区告诉我"
[字幕叠加:关注引导]
```

### 数据维度（每期至少覆盖5项）

| 维度 | 数据项 | 来源 |
|------|--------|------|
| 价格 | 挂牌均价、成交均价、近1年涨跌幅 | 链家/贝壳 |
| 产品 | 建成年份、容积率、主力户型面积段 | 链家/实地 |
| 交易 | 近90天成交量、平均成交周期 | 链家 |
| 客群 | 主要买家画像（首次/改善/投资占比） | 经验判断 |
| 配套 | 地铁距离、学区、商业 | 地图+实地 |
| 竞品 | 周边同价位替代小区 | 链家对比 |

### 知识型脚本的特殊要求

1. **数据可视化**：关键数字必须叠加字幕，不靠观众耳朵记
2. **对比出判断**：不孤立讲一个小区，要放在板块内对标（"天山X小区 vs 隔壁Y小区差在哪"）
3. **实地画面优先**：有实拍就不用网图，画面本身就是专业度的证明
4. **系列感**：每期结尾预告下一期，建立追更期待

### 自动剪辑（v3.0）

脚本和拍摄完成后，说"剪这条"触发 `video-editor` 技能（详见 `.claude/skills/video-editor.md`）。

**v3.0 核心变化**：知识型内容优先。自动识别内容类型，知识型走专属参数——舒缓钢琴BGM、黑体+宋体双字体、数据卡片叠加、极简音效、慢节奏金句留白。剪辑知识库在 `memory/layer3-execution/video-editing-knowledge/`，生成字幕时读 `subtitles.md`、选字体时读 `fonts.md`、选BGM时读 `bgm.md`、设计叠加布局时读 `layout.md`、加音效时读 `sound-effects.md`。

**分步审核流程**：
1. `python video_editor.py <素材> --transcribe-only` — 转录，校对数字和地名
2. `python video_editor.py <脚本> --plan-only` — 出剪辑计划，含数据卡片布局
3. 用户确认 → 全自动渲染 → 用户看片反馈 → 迭代修改

## 常用命令

```bash
python engine.py status                                     # 今日策略/支柱/格式推荐
python engine.py analyze                                    # 分析已发布数据
python viral_validator.py <脚本路径>                         # 9维爆款验证
python pleasure_scorer.py <脚本路径>                         # 爽点评分
python douyin_extractor.py <链接> --asr --comments           # 提取抖音口播+评论
python video_editor.py <脚本> <素材>                          # 全自动剪辑（对齐+渲染）
python video_editor.py <素材> --transcribe-only               # 只转录素材
python video_editor.py <脚本> --plan-only                    # 只出剪辑计划
python video_editor.py <脚本> <素材> --font <黑体.ttf> --bgm <BGM.mp3>  # 带字体+BGM
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
│   ├── layer2-strategy/             # 内容模式、复盘、竞品、CTA策略、准确度规则
│   ├── layer3-execution/            # 文案技巧、钩子库、金句记录、拍摄指南、素材捕捉、制作运营
│   │   └── video-editing-knowledge/ # ★ 剪辑知识库v3.0（BGM/字体/字幕/布局/音效）
│   └── layer4-feedback/             # 客户咨询来源
└── .claude/skills/
    ├── douyin-extract.md            # 抖音提取技能
    └── video-editor.md              # ★ 视频自动剪辑技能v3.0
```

## 每周复盘

每5-7天跑 `python engine.py analyze`，汇报策略互动率、完播率、趋势、下周建议。每4周额外检查定位修正、客户来源质量、赛道变化、阶段切换判断，写入 `memory/layer2-strategy/phase-review.md`。
