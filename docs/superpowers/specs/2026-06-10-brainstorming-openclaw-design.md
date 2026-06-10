# Brainstorming 技能 OpenClaw 移植设计

## 目标

将 Claude Code 的 brainstorming 技能（`~/.claude/skills/brainstorming/SKILL.md`）以纯格式转换方式移植到 OpenClaw，通过 `/brainstorming` 斜杠命令触发。

## 目标平台

- **运行环境**：OpenClaw，通过 Telegram bot 交互
- **技能目录**：`D:/openclaw-skills/brainstorming/`
- **触发方式**：`/brainstorming` 斜杠命令 + 自然语言 "头脑风暴"

## 文件结构

```
D:/openclaw-skills/brainstorming/
  SKILL.md
```

纯对话技能，无脚本、无参考文件、无资源文件。

## Frontmatter 转换

**Claude Code 原版**：

```yaml
name: brainstorming
description: "You MUST use this before any creative work — creating features, building components, adding functionality, or modifying behavior. Explores user intent, requirements and design before implementation."
```

**OpenClaw 版**：

```yaml
name: brainstorming
description: "在开始任何创造性工作之前必须使用——通过自然对话探索用户意图、挖掘需求、呈现设计方案并获取批准。"
```

变化点：
- `name` 保持不变，自动注册为 `/brainstorming` 斜杠命令
- `description` 改为中文，控制在 160 字符以内
- `user-invocable` 默认 true，无需显式声明

## 主体内容改动（6 处）

| # | 原版内容 | 处理 | 原因 |
|---|---------|------|------|
| 1 | `<HARD-GATE>` XML 自定义标签 | 改为加粗文字 | OpenClaw 不解析 Claude Code 的 XML 标签 |
| 2 | dot 流程图（`digraph brainstorming {...}`） | 删除 | Telegram 纯文本无法渲染 |
| 3 | Visual Companion 整节 | 删除 | Telegram 无浏览器环境 |
| 4 | `TodoWrite` 创建任务 | 改为 "逐一完成以下步骤" | OpenClaw 工具名不同 |
| 5 | "invoke writing-plans skill" | 改为 "制定实施计划" | 跨技能引用不通用 |
| 6 | `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md` | 改为通用路径描述 | 不绑定 Claude Code 项目目录结构 |

## 保留内容（不变）

- 8 步工作流清单（探索上下文 → 提问 → 方案 → 设计 → spec → 自检 → 用户审阅 → 实施），去掉了视觉伴侣
- 一问一答节奏、多选优先原则
- 2-3 方案对比 + 推荐
- 分段呈现设计、逐段获取批准
- Spec 自检四问（占位符、一致性、范围、歧义）
- 用户审阅门（必须审阅 spec 后才能进入实施）
- YAGNI 原则
- 反模式警告（"这太简单不需要设计"）
- 设计隔离与清晰原则

## 安装与验证

1. 将 `SKILL.md` 放入 `D:/openclaw-skills/brainstorming/`
2. 执行 `/new` 或重启 OpenClaw Gateway
3. 输入 `/brainstorming` 验证斜杠命令可用
4. 输入 "帮我头脑风暴一下" 验证自然语言触发
