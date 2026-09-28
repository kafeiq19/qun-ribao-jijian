#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Screenshot the report HTML to a WeChat-share long PNG."""
from __future__ import annotations

import argparse
from pathlib import Path

from playwright.sync_api import sync_playwright


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--html", required=True)
    ap.add_argument("--png", required=True)
    ap.add_argument("--width", type=int, default=750)
    ap.add_argument("--scale", type=float, default=2)
    args = ap.parse_args()
    html_path = Path(args.html).resolve()
    png_path = Path(args.png)
    png_path.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(channel="chrome")
        except Exception:
            browser = p.chromium.launch()
        page = browser.new_page(
            viewport={"width": args.width, "height": 1400},
            device_scale_factor=args.scale,
        )
        page.goto(html_path.as_uri(), wait_until="networkidle")
        page.wait_for_timeout(400)
        try:
            page.wait_for_function(
                "() => Array.from(document.images).every(img => img.complete)",
                timeout=8000,
            )
        except Exception:
            pass
        page.screenshot(path=str(png_path), full_page=True)
        browser.close()
    print("png", png_path, "size", png_path.stat().st_size)


if __name__ == "__main__":
    main()
