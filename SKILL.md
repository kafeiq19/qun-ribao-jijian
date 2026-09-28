---
name: qun-ribao-jijian
description: >
  把微信群 WeFlow jsonl 聊天记录整理成「精简 | 极简版」日报，并输出可发群的白底卡片长图 PNG。
  触发：群聊日报、精简版、极简版、群日报 png、做成 png、WeFlow、jsonl 群记录、/qun-ribao-jijian。
---

# 群聊日报 · 精简 | 极简版

用户给出 WeFlow 导出目录或 `.jsonl` 时：先按 `references/editorial.md` 写内容，再套 `assets/report_card.html` 截成长图。最终产物是 PNG；HTML 放在同目录便于改。

本 skill 产出白底卡片长图（750px 宽）。不要改用仓库里 `wechat-daily-report-skill` 的侧边栏剧情模板。

## 工作流

### 1. 定位记录

导出目录里通常有 `{群名}-{id}.jsonl`，消息 `_type` 为 `header` / `member` / `message`。`message.timestamp` 是 unix 秒，按东八区换算。

```bash
python <this-skill>/scripts/parse_jsonl.py --jsonl "<path>.jsonl" --out-dir "<export-dir>/report_assets"
```

得到 `stats.json` 和 `messages.txt`。先读这两份，不够再回 jsonl。

### 2. 写内容

严格遵守 `references/editorial.md`。根据 `stats.json` + `messages.txt` 写出 `content.json`（字段见 `assets/content.example.json`），放到导出目录的 `report_assets/content.json`。

`people[].name` 必须能在 jsonl 的 `accountName` / `groupNickname` 里对上，后面下头像靠这个匹配。

### 3. 头像、HTML、PNG

```bash
python <this-skill>/scripts/download_avatars.py --jsonl "<path>.jsonl" --content "<export-dir>/report_assets/content.json" --out-dir "<export-dir>/report_assets/avatars"
python <this-skill>/scripts/render_html.py --content "<export-dir>/report_assets/content.json" --avatars "<export-dir>/report_assets/avatars" --output "<export-dir>/{群名}_日报_{日期}.html"
python <this-skill>/scripts/render_png.py --html "<export-dir>/{群名}_日报_{日期}.html" --png "<export-dir>/{群名}_日报_{日期}.png"
```

`<this-skill>` = 本 SKILL.md 所在目录。截图用本机 Chrome（`channel=chrome`），宽 750、device scale 2、整页。

### 4. 回用户

只给 PNG 的绝对路径。同目录 HTML 可顺口提一句。

## 缺依赖时

`pip install jinja2 playwright`。本机已有 Chrome 即可，不必再 `playwright install`。
