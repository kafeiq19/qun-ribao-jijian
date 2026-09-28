#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Pull a WeFlow session into ChatLab jsonl for the daily-report pipeline."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

TZ = timezone(timedelta(hours=8))
DEFAULT_BASE = "http://127.0.0.1:5031"
PAGE = 5000


def die(msg: str, code: int = 1) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def load_weflow_config() -> dict:
    raw = os.environ.get("WEFLOW_CONFIG")
    path = Path(raw) if raw else Path(os.environ.get("APPDATA", "")) / "weflow" / "WeFlow-config.json"
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def resolve_api(args) -> tuple[str, str]:
    cfg = load_weflow_config()
    host = args.host or cfg.get("httpApiHost") or "127.0.0.1"
    port = args.port or cfg.get("httpApiPort") or 5031
    base = (args.base or os.environ.get("WEFLOW_BASE") or f"http://{host}:{port}").rstrip("/")
    token = args.token or os.environ.get("WEFLOW_TOKEN") or cfg.get("httpApiToken") or ""
    return base, token


def http_json(base: str, path: str, token: str, params: dict | None = None, timeout: int = 60) -> dict:
    q = urllib.parse.urlencode({k: v for k, v in (params or {}).items() if v not in (None, "")})
    url = f"{base}{path}"
    if q:
        url = f"{url}?{q}"
    headers = {"User-Agent": "qun-ribao-jijian/1.0"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:400]
        if e.code in (401, 403):
            die("WeFlow API 鉴权失败。检查设置里的 API Token，或设环境变量 WEFLOW_TOKEN。")
        die(f"WeFlow HTTP {e.code} {path}: {body}")
    except urllib.error.URLError as e:
        die(
            "连不上 WeFlow API（默认 http://127.0.0.1:5031）。"
            "请先打开 WeFlow，设置 → API 服务 → 启动服务。"
        )


def parse_when(text: str | None, end_of_day: bool) -> int | None:
    if not text:
        return None
    text = text.strip()
    if re.fullmatch(r"\d{10}", text):
        return int(text)
    if re.fullmatch(r"\d{13}", text):
        return int(text) // 1000
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d", "%Y%m%d"):
        try:
            dt = datetime.strptime(text, fmt)
            break
        except ValueError:
            dt = None
    if dt is None:
        die(f"无法解析时间: {text}（用 YYYY-MM-DD 或 YYYY-MM-DD HH:MM）")
    if fmt in ("%Y-%m-%d", "%Y%m%d") and end_of_day:
        dt = dt.replace(hour=23, minute=59, second=59)
    return int(dt.replace(tzinfo=TZ).timestamp())


def safe_name(name: str) -> str:
    name = re.sub(r'[\\/:*?"<>|]', "_", name).strip() or "group"
    return name[:40]


def short_id(talker: str) -> str:
    return hashlib.md5(talker.encode("utf-8")).hexdigest()[:10]


def list_sessions(base: str, token: str, keyword: str) -> list[dict]:
    data = http_json(base, "/api/v1/sessions", token, {"format": "chatlab", "keyword": keyword, "limit": 200})
    sessions = data.get("sessions") or []
    out = []
    for s in sessions:
        out.append(
            {
                "id": s.get("id") or s.get("username"),
                "name": s.get("name") or s.get("displayName") or "",
                "type": s.get("type"),
                "lastMessageAt": s.get("lastMessageAt") or s.get("lastTimestamp") or 0,
            }
        )
    return [s for s in out if s.get("id")]


def pick_session(sessions: list[dict], query: str, talker: str | None) -> dict:
    if talker:
        for s in sessions:
            if s["id"] == talker:
                return s
        die(f"未找到会话 ID: {talker}")
    q = query.strip()
    exact = [s for s in sessions if s["name"] == q or s["id"] == q]
    cand = exact or [s for s in sessions if q.lower() in (s["name"] or "").lower() or q in s["id"]]
    if not cand:
        die(f"WeFlow 里没有匹配「{query}」的会话。换个群名，或先在 WeFlow 里打开过该群。")
    cand.sort(key=lambda s: s.get("lastMessageAt") or 0, reverse=True)
    if len(cand) > 1:
        print("匹配到多个会话，使用最近活跃的一条；要用别的请加 --talker：")
        for s in cand[:8]:
            ts = s.get("lastMessageAt") or 0
            when = datetime.fromtimestamp(ts, TZ).strftime("%Y-%m-%d %H:%M") if ts else "-"
            print(f"  {s['id']}  {s['name']}  最后消息 {when}")
    return cand[0]


def fetch_chatlab(base: str, token: str, talker: str, start: int | None, end: int | None) -> dict:
    all_msgs = []
    members = {}
    meta = {}
    chatlab = {}
    offset = 0
    while True:
        params = {
            "talker": talker,
            "limit": PAGE,
            "offset": offset,
            "format": "chatlab",
        }
        if start:
            params["start"] = str(start)
        if end:
            params["end"] = str(end)
        data = http_json(base, "/api/v1/messages", token, params, timeout=120)
        meta = data.get("meta") or meta
        chatlab = data.get("chatlab") or chatlab
        for m in data.get("members") or []:
            pid = m.get("platformId")
            if pid:
                members[pid] = m
        batch = data.get("messages") or []
        all_msgs.extend(batch)
        if len(batch) < PAGE:
            break
        offset += len(batch)
        if offset > 200000:
            die("消息超过 20 万条，缩小时间范围后再导。")
    all_msgs.sort(key=lambda m: m.get("timestamp") or 0)
    return {"chatlab": chatlab, "meta": meta, "members": list(members.values()), "messages": all_msgs}


def write_jsonl(payload: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    header = {"_type": "header", "chatlab": payload.get("chatlab") or {}, "meta": payload.get("meta") or {}}
    lines.append(json.dumps(header, ensure_ascii=False))
    for m in payload.get("members") or []:
        row = dict(m)
        row["_type"] = "member"
        lines.append(json.dumps(row, ensure_ascii=False))
    for m in payload.get("messages") or []:
        row = dict(m)
        row["_type"] = "message"
        lines.append(json.dumps(row, ensure_ascii=False))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description="Export a WeFlow group to ChatLab jsonl")
    ap.add_argument("--group", required=True, help="群名或会话 ID 片段")
    ap.add_argument("--talker", help="精确会话 ID，如 xxx@chatroom")
    ap.add_argument("--start", help="开始时间 YYYY-MM-DD 或 YYYY-MM-DD HH:MM")
    ap.add_argument("--end", help="结束时间，日期会算到当天 23:59:59")
    ap.add_argument("--out-dir", help="导出目录，默认 E:\\Downloads\\texts\\群聊_{名}-{id}")
    ap.add_argument("--base")
    ap.add_argument("--host")
    ap.add_argument("--port", type=int)
    ap.add_argument("--token")
    args = ap.parse_args()

    base, token = resolve_api(args)
    health = http_json(base, "/health", "")
    if health.get("status") != "ok":
        die("WeFlow /health 不是 ok。")

    sessions = list_sessions(base, token, args.group)
    sess = pick_session(sessions, args.group, args.talker)
    talker = sess["id"]
    name = sess["name"] or args.group

    start_ts = parse_when(args.start, False)
    end_ts = parse_when(args.end, True)
    if not start_ts and not end_ts:
        today = datetime.now(TZ).strftime("%Y-%m-%d")
        start_ts = parse_when(today, False)
        end_ts = parse_when(today, True)
        print(f"未指定时间，默认今天 {today} 00:00–23:59")

    payload = fetch_chatlab(base, token, talker, start_ts, end_ts)
    n = len(payload.get("messages") or [])
    if n == 0:
        die("该时间段没有消息。核对群名和起止时间。", 2)

    sid = short_id(talker)
    folder = Path(args.out_dir) if args.out_dir else Path(r"E:\Downloads\texts") / f"群聊_{safe_name(name)}-{sid}"
    jsonl = folder / f"群聊_{safe_name(name)}-{sid}.jsonl"
    write_jsonl(payload, jsonl)
    print("group", name)
    print("talker", talker)
    print("messages", n)
    print("jsonl", jsonl)


if __name__ == "__main__":
    main()
