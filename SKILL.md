---
name: qun-ribao-jijian
description: >
  把微信群聊天记录整理成「精简 | 极简版」日报并输出白底卡片长图 PNG。
  用户只给群名和时间时，先用本机 WeFlow HTTP API 导出 jsonl，再做图。
  触发：群聊日报、精简版、极简版、群日报 png、做成 png、WeFlow、jsonl、某段时间的日报、/qun-ribao-jijian。
---

# 群聊日报 · 精简 | 极简版

用户要某群、某段时间的日报时：**先导出，再出图**。不要等用户手工从 WeFlow 点导出。

最终产物是 PNG；HTML 放同目录。用 `assets/report_card.html` 白底卡片（750px），不要改用 `wechat-daily-report-skill` 的侧边栏剧情模板。

## 工作流

### 0. 拿到 jsonl

**已有导出目录或 `.jsonl`：** 直接用，跳到第 1 步。

**只给了群名（和时间）：** 调 WeFlow API。细节见 `references/weflow.md`。

```bash
python <this-skill>/scripts/export_weflow.py --group "<群名>" --start YYYY-MM-DD --end YYYY-MM-DD
```

stdout 里的 `jsonl` 路径交给下一步。时间没说就不要加 `--start/--end`（脚本默认今天）。重名群看 stdout 候选，需要时加 `--talker xxx@chatroom`。

连不上 API：告诉用户打开 WeFlow 并启动「API 服务」。不要假装已经从微信里拉到记录。

### 1. 解析记录

```bash
python <this-skill>/scripts/parse_jsonl.py --jsonl "<path>.jsonl" --out-dir "<export-dir>/report_assets"
```

得到 `stats.json` 和 `messages.txt`。先读这两份，不够再回 jsonl。消息 `_type` 为 `header` / `member` / `message`，`timestamp` 是 unix 秒，按东八区。

### 2. 写内容

严格遵守 `references/editorial.md`。写出 `content.json`（字段见 `assets/content.example.json`），放到 `<export-dir>/report_assets/content.json`。

`people[].name` 必须能在 jsonl 的 `accountName` / `groupNickname` 里对上。

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

`pip install jinja2 playwright`。本机已有 Chrome 即可。WeFlow 必须在跑且 API 已开。
