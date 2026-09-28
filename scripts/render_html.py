#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Fill report_card.html from content.json."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

SKILL_DIR = Path(__file__).resolve().parent.parent


def attach_avatars(content: dict, avatars_dir: Path, html_dir: Path) -> dict:
    mapping = {}
    mp = avatars_dir / "mapping.json"
    if mp.is_file():
        mapping = json.loads(mp.read_text(encoding="utf-8"))
    for t in content.get("topics") or []:
        for p in t.get("people") or []:
            fname = mapping.get(p.get("name"))
            if not fname:
                p["avatar"] = ""
                continue
            abs_img = (avatars_dir / fname).resolve()
            try:
                p["avatar"] = abs_img.relative_to(html_dir.resolve()).as_posix()
            except ValueError:
                p["avatar"] = abs_img.as_uri()
    return content


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--content", required=True)
    ap.add_argument("--avatars", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--template", default=str(SKILL_DIR / "assets" / "report_card.html"))
    args = ap.parse_args()

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    content = json.loads(Path(args.content).read_text(encoding="utf-8"))
    content = attach_avatars(content, Path(args.avatars), out.parent)

    tpl_path = Path(args.template)
    env = Environment(
        loader=FileSystemLoader(str(tpl_path.parent)),
        autoescape=select_autoescape(["html"]),
    )
    html = env.get_template(tpl_path.name).render(**content)
    out.write_text(html, encoding="utf-8")
    print("html", out)


if __name__ == "__main__":
    main()
