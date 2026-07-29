"""
CX Observe probe v2 — go through the Home → Customer Search flow to
resolve the correct customer-summary URL and inspect Consumption tile DOM.

Prereq: Edge on CDP:9222, signed in to cxp.azure.com.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright  # type: ignore

OUT_DIR = Path(__file__).parent.parent / "references" / "acr_probe_2026-07"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def log(msg: str) -> None:
    print(f"[probe2] {msg}", flush=True)


def dump(page, tag: str) -> None:
    html_path = OUT_DIR / f"{tag}.html"
    png_path = OUT_DIR / f"{tag}.png"
    try:
        html_path.write_text(page.content(), encoding="utf-8")
        page.screenshot(path=str(png_path), full_page=True)
        log(f"saved: {tag}.html + {tag}.png (url={page.url[:100]})")
    except Exception as e:
        log(f"dump failed for {tag}: {e}")


def main() -> int:
    tpid = "636846"  # PepsiCo

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://localhost:9222")
        ctx = browser.contexts[0]

        # find cxobserve tab, or use first
        target = None
        for pg in ctx.pages:
            if "cxp.azure.com" in pg.url:
                target = pg
                break
        if not target:
            target = ctx.pages[0]

        log(f"start url: {target.url[:120]}")

        # Step 1: navigate to home
        target.goto("https://cxp.azure.com/cxobserve/home", wait_until="domcontentloaded", timeout=60000)
        try:
            target.wait_for_load_state("networkidle", timeout=30000)
        except Exception:
            pass
        time.sleep(3)
        dump(target, "01_home")

        # Step 2: locate a search input
        log("--- inspecting inputs ---")
        inputs = target.locator("input").all()
        log(f"input count: {len(inputs)}")
        for i, inp in enumerate(inputs[:15]):
            try:
                attrs = inp.evaluate(
                    "el => ({placeholder: el.placeholder, aria: el.getAttribute('aria-label'), id: el.id, name: el.name, type: el.type})"
                )
                log(f"  [{i}] {attrs}")
            except Exception:
                pass

        # Step 3: try to find the customer search box by common labels
        search_box = None
        for sel in [
            "input[placeholder*='Search' i]",
            "input[aria-label*='Search' i]",
            "input[placeholder*='Customer' i]",
            "input[aria-label*='Customer' i]",
            "input[type='search']",
        ]:
            candidates = target.locator(sel).all()
            if candidates:
                log(f"found via {sel!r}: {len(candidates)} → using first")
                search_box = candidates[0]
                break

        if not search_box:
            log("no search box found; dumping raw first input")
            if inputs:
                search_box = inputs[0]

        if search_box:
            log(f"typing TPID {tpid}")
            search_box.click()
            time.sleep(0.5)
            search_box.fill("")
            search_box.type(tpid, delay=100)
            time.sleep(3)
            dump(target, "02_after_type")

            # try press enter
            search_box.press("Enter")
            time.sleep(4)
            dump(target, "03_after_enter")

        log(f"final url: {target.url[:200]}")

        # Also inspect page routes discoverable via localStorage / window
        try:
            routes = target.evaluate("() => { try { return Object.keys(window).filter(k => k.toLowerCase().includes('route')).slice(0, 20); } catch(e) { return String(e); } }")
            log(f"route-related window keys: {routes}")
        except Exception as e:
            log(f"eval err: {e}")

        return 0


if __name__ == "__main__":
    sys.exit(main())
