#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Download WeChat avatars for names listed in content.json."""
from __future__ import annotations

import argparse
import hashlib
import json
import urllib.request
from pathlib import Path

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def collect_names(content: dict) -> list[str]:
    names = []
    for t in content.get("topics") or []:
        for p in t.get("people") or []:
            n = p.get("name")
            if n and n not in names:
                names.append(n)
    return names


def index_members(jsonl: Path) -> dict:
    by_name = {}
    with jsonl.open(encoding="utf-8") as f:
        for line in f:
            o = json.loads(line)
            if o.get("_type") != "member":
                continue
            for k in (o.get("accountName"), o.get("groupNickname")):
                if k and k not in by_name:
                    by_name[k] = o
    return by_name


def match_member(name: str, by_name: dict):
    if name in by_name:
        return by_name[name]
    for k, v in by_name.items():
        if name and k and (name in k or k in name):
            return v
    return None


def slug(name: str) -> str:
    return hashlib.md5(name.encode("utf-8")).hexdigest()[:10]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jsonl", required=True)
    ap.add_argument("--content", required=True)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    content = json.loads(Path(args.content).read_text(encoding="utf-8"))
    by_name = index_members(Path(args.jsonl))
    mapping = {}
    for name in collect_names(content):
        mem = match_member(name, by_name)
        url = (mem or {}).get("avatar") or ""
        if url.endswith("/0"):
            url = url[:-2] + "/132"
        dest = out / f"{slug(name)}.jpg"
        if not url:
            print("no avatar", name)
            continue
        req = urllib.request.Request(
            url, headers={"User-Agent": UA, "Referer": "https://wx.qq.com/"}
        )
        try:
            with urllib.request.urlopen(req, timeout=12) as r:
                dest.write_bytes(r.read())
            mapping[name] = dest.name
            print("ok", name, dest.name)
        except Exception as e:
            print("fail", name, e)

    (out / "mapping.json").write_text(
        json.dumps(mapping, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("mapping", out / "mapping.json")


if __name__ == "__main__":
    main()
