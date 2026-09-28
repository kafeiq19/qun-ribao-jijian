# qun-ribao-jijian

Grok / Agent Skill：把 WeFlow 导出的微信群 jsonl 整理成「精简 | 极简版」日报，并截成可发群的白底卡片长图 PNG。

## 安装

复制整个目录到：

- Grok：`~/.grok/skills/qun-ribao-jijian`
- Claude Code：`~/.claude/skills/qun-ribao-jijian`

依赖：`pip install jinja2 playwright`，本机有 Chrome 即可。

## 用法

把 WeFlow 导出目录或 `.jsonl` 丢给 Agent，说「做成精简版日报 png」或运行 `/qun-ribao-jijian`。

工作流见 `SKILL.md`，编辑规则见 `references/editorial.md`。
