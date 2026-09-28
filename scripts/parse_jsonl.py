#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Parse WeFlow jsonl into stats.json + messages.txt."""
from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

TZ = timezone(timedelta(hours=8))
TYPE_MAP = {0: "text", 7: "image", 25: "quote", 80: "other", 3: "voice", 34: "video", 4: "file"}


def load_jsonl(path: Path):
    header, members, msgs = {}, {}, []
    with path.open(encoding="utf-8") as f:
        for line in f:
            o = json.loads(line)
            t = o.get("_type")
            if t == "header":
                header = o
            elif t == "member":
                members[o.get("platformId")] = o
            elif t == "message":
                o["_dt"] = datetime.fromtimestamp(o["timestamp"], TZ)
                msgs.append(o)
    return header, members, msgs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jsonl", required=True)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()
    jsonl = Path(args.jsonl)
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    header, members, msgs = load_jsonl(jsonl)
    if not msgs:
        raise SystemExit("no messages")

    first, last = msgs[0]["_dt"], msgs[-1]["_dt"]
    span_h = (last - first).total_seconds() / 3600
    hours = max(1, math.ceil(span_h - 1e-9))

    spk, first_seen = Counter(), {}
    for m in msgs:
        n = m.get("accountName") or m.get("sender")
        spk[n] += 1
        first_seen.setdefault(n, m["_dt"].isoformat())

    rank = sorted(spk.items(), key=lambda x: (-x[1], first_seen[x[0]]))
    hourly = Counter(m["_dt"].strftime("%Y-%m-%d %H:00") for m in msgs)

    stats = {
        "group_name": (header.get("meta") or {}).get("name") or jsonl.stem,
        "first": first.strftime("%Y-%m-%d %H:%M"),
        "last": last.strftime("%Y-%m-%d %H:%M"),
        "messages": len(msgs),
        "speakers": len(spk),
        "hours": hours,
        "avg": round(len(msgs) / max(len(spk), 1), 1),
        "types": dict(Counter(m.get("type") for m in msgs)),
        "by_day": dict(Counter(m["_dt"].strftime("%Y-%m-%d") for m in msgs)),
        "hourly": dict(sorted(hourly.items())),
        "top_talkers": [
            {"name": n, "count": c, "first": first_seen[n]} for n, c in rank
        ],
        "source_jsonl": str(jsonl),
    }
    (out / "stats.json").write_text(
        json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    lines = []
    for i, m in enumerate(msgs, 1):
        nick = m.get("accountName") or m.get("sender")
        t = m["_dt"].strftime("%Y-%m-%d %H:%M:%S")
        typ = TYPE_MAP.get(m.get("type"), str(m.get("type")))
        c = m.get("content") or ""
        if isinstance(c, str):
            c = c.replace("\n", " | ").strip()
            if len(c) > 420:
                c = c[:420] + "…"
        lines.append(f"{i:03d} [{t}] {nick} ({typ}): {c}")
    (out / "messages.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("stats", out / "stats.json")
    print("messages", out / "messages.txt")
    print(
        f"{stats['group_name']} {stats['first']}–{stats['last']} "
        f"{stats['messages']} msgs / {stats['speakers']} speakers / {hours}h"
    )


if __name__ == "__main__":
    main()
