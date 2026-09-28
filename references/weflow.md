# WeFlow 导出

日报默认先走本机 WeFlow HTTP API，再写 jsonl。

## 前置

1. WeFlow 正在运行（本机 `D:\Program Files\WeFlow\WeFlow.exe`）
2. 设置 → API 服务 → 启动服务（默认 `http://127.0.0.1:5031`）
3. Token 写在 `%APPDATA%\weflow\WeFlow-config.json` 的 `httpApiToken`，脚本自动读。也可用环境变量 `WEFLOW_TOKEN` / `WEFLOW_BASE`。

不要把 Token 写进 skill 仓库。

## 命令

```bash
python scripts/export_weflow.py --group "天津分潭" --start 2026-09-27 --end 2026-09-28
```

- `--group`：群名片段或会话 ID
- `--talker`：重名时指定 `xxx@chatroom`
- `--start` / `--end`：`YYYY-MM-DD` 或 `YYYY-MM-DD HH:MM`；只有日期时 end 算到 23:59:59
- 都不传时间：导出**今天**（东八区）
- 默认写到 `E:\Downloads\texts\群聊_{群名}-{短id}\群聊_{群名}-{短id}.jsonl`

同名群取**最近一条消息最新**的会话，并在 stdout 列出候选。

## 失败时

| 现象 | 处理 |
|---|---|
| 连不上 5031 | 打开 WeFlow，打开 API 服务 |
| 401/403 | 核对 Token / `WEFLOW_TOKEN` |
| 匹配到多个会话 | 加 `--talker` |
| 0 条消息 | 核对时间段；该群需在 WeFlow 里能打开 |

用户已经给了现成 jsonl / 导出目录时，跳过本步。
