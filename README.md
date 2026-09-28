# qun-ribao-jijian

Grok / Agent Skill：把 WeFlow 导出的微信群 jsonl 整理成「精简 | 极简版」日报，并截成可发群的白底卡片长图 PNG。

## 安装

复制整个目录到：

- Grok：`~/.grok/skills/qun-ribao-jijian`
- Claude Code：`~/.claude/skills/qun-ribao-jijian`

依赖：`pip install jinja2 playwright`，本机有 Chrome 即可。

## 用法

说「帮我做某某群 9/27–9/28 的日报」或运行 `/qun-ribao-jijian`。Agent 会先调本机 WeFlow API 导出 jsonl，再出 PNG。

也可以直接丢现成的 WeFlow 导出目录。WeFlow 需在运行，并开启设置里的 API 服务（`127.0.0.1:5031`）。

工作流见 `SKILL.md`，编辑规则见 `references/editorial.md`，导出见 `references/weflow.md`。
