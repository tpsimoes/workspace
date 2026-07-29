"""
CX Observe probe v4 — continue from wherever the tab is, take a viewport
screenshot (no full_page) and drill into Related workloads → View.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright  # type: ignore

OUT_DIR = Path(__file__).parent.parent / "references" / "acr_probe_2026-07"


def log(msg: str) -> None:
    print(f"[probe4] {msg}", flush=True)


def main() -> int:
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://localhost:9222")
        ctx = browser.contexts[0]
        target = None
        for pg in ctx.pages:
            if "cxp.azure.com" in pg.url:
                target = pg
                break
        if not target:
            log("no cxobserve tab")
            return 1

        log(f"current url: {target.url}")

        # viewport screenshot (not full_page)
        try:
            target.screenshot(path=str(OUT_DIR / "30_current.png"))
            log("saved 30_current.png")
        except Exception as e:
            log(f"screenshot err: {e}")

        # Save HTML
        try:
            (OUT_DIR / "30_current.html").write_text(target.content(), encoding="utf-8")
            log("saved 30_current.html")
        except Exception as e:
            log(f"html err: {e}")

        # Enumerate the two Related workloads matches and check their parent containers
        log("--- Related workloads details ---")
        rw = target.locator("text=Related workloads").all()
        for i, h in enumerate(rw):
            try:
                info = h.evaluate("""el => {
                    const parent = el.closest('[class*=card],[class*=Card],[class*=tile],[class*=Tile],section,article');
                    return {
                        tag: el.tagName,
                        text: el.textContent?.slice(0, 100),
                        boundingBox: el.getBoundingClientRect(),
                        parentTag: parent?.tagName,
                        parentText: parent?.textContent?.slice(0, 300),
                    };
                }""")
                log(f"  [{i}] {info}")
            except Exception as e:
                log(f"  [{i}] eval err: {e}")

        # Look for View button/link near Related workloads
        log("--- View elements ---")
        views = target.locator("text=View").all()
        log(f"View text matches: {len(views)}")
        for i, v in enumerate(views[:20]):
            try:
                info = v.evaluate("""el => ({
                    tag: el.tagName,
                    text: el.textContent?.slice(0, 40),
                    role: el.getAttribute('role'),
                    href: el.getAttribute('href'),
                    onclick: el.hasAttribute('onclick'),
                    parentText: el.parentElement?.textContent?.slice(0, 100)
                })""")
                log(f"  [{i}] {info}")
            except Exception:
                pass

        # Look for Consumption anywhere
        log("--- Consumption search (all text) ---")
        # innerText search
        body_text = target.evaluate("() => document.body.innerText")
        idx = body_text.lower().find("consumption")
        log(f"body.innerText contains 'Consumption'? {idx != -1}")
        if idx != -1:
            log(f"  first 200 chars around: {body_text[max(0, idx-50):idx+200]!r}")

        # look for any month-like text (Jun 2026, May 2026)
        for m in ["Jun 2026", "May 2026", "$M", "Usage", "USD"]:
            found = m.lower() in body_text.lower()
            log(f"'{m}' present: {found}")

        # dump all iframes
        log("--- iframes ---")
        frames = target.frames
        for f in frames:
            log(f"  frame: {f.url[:120]}")

        return 0


if __name__ == "__main__":
    sys.exit(main())
