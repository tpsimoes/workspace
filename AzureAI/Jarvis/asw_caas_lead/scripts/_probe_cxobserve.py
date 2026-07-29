"""
CX Observe probe — attach to CDP:9222, navigate to PepsiCo TPID 636846,
dump the DOM structure of the Consumption tile and Related workloads picker.

Prereq:
- External Edge running with --remote-debugging-port=9222
- User signed in to https://cxp.azure.com/cxobserve/home
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright  # type: ignore

OUT_DIR = Path(__file__).parent.parent / "references" / "acr_probe_2026-07"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def log(msg: str) -> None:
    print(f"[probe] {msg}", flush=True)


def main() -> int:
    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp("http://localhost:9222")
        except Exception as e:
            log(f"CDP connect failed: {e}")
            log("Make sure Edge is running with --remote-debugging-port=9222")
            return 1

        contexts = browser.contexts
        log(f"contexts: {len(contexts)}")
        if not contexts:
            log("No browser contexts — is Edge open with at least one tab?")
            return 1

        ctx = contexts[0]
        log(f"pages in ctx[0]: {len(ctx.pages)}")
        for i, pg in enumerate(ctx.pages):
            log(f"  page[{i}]: {pg.url[:120]}")

        # find an existing cxobserve tab, or open a new one
        target = None
        for pg in ctx.pages:
            if "cxp.azure.com" in pg.url:
                target = pg
                break

        if not target:
            log("No cxobserve tab found — opening a new one")
            target = ctx.new_page()

        # Probe: PepsiCo TPID 636846
        tpid = "636846"
        url = f"https://cxp.azure.com/cxobserve/customersummary?tpid={tpid}"
        log(f"navigating to {url}")
        target.goto(url, wait_until="domcontentloaded", timeout=60000)

        # wait for content to settle
        try:
            target.wait_for_load_state("networkidle", timeout=45000)
        except Exception as e:
            log(f"networkidle timeout (continuing anyway): {e}")

        time.sleep(4)

        # dump landing HTML
        html = target.content()
        landing_html_path = OUT_DIR / f"landing_{tpid}.html"
        landing_html_path.write_text(html, encoding="utf-8")
        log(f"landing HTML saved: {landing_html_path} ({len(html)} bytes)")

        # screenshot
        landing_png = OUT_DIR / f"landing_{tpid}.png"
        target.screenshot(path=str(landing_png), full_page=True)
        log(f"landing screenshot: {landing_png}")

        # try to find Consumption tile — dump anything with text "Consumption"
        log("--- searching for 'Consumption' text ---")
        consumption_hits = target.locator("text=Consumption").all()
        log(f"Consumption text matches: {len(consumption_hits)}")
        for i, h in enumerate(consumption_hits[:5]):
            try:
                log(f"  [{i}] tag={h.evaluate('el => el.tagName')} txt={h.inner_text()[:80]!r}")
            except Exception:
                pass

        # try to find "Related workloads" link
        log("--- searching for 'Related workloads' ---")
        rw_hits = target.locator("text=Related workloads").all()
        log(f"Related workloads text matches: {len(rw_hits)}")
        for i, h in enumerate(rw_hits[:5]):
            try:
                log(f"  [{i}] tag={h.evaluate('el => el.tagName')} txt={h.inner_text()[:100]!r}")
            except Exception:
                pass

        # look for the View button near Related workloads
        log("--- searching for 'View' button ---")
        view_btns = target.locator("button:has-text('View'), a:has-text('View')").all()
        log(f"View button/link matches: {len(view_btns)}")

        log("--- probe complete ---")
        log(f"outputs in: {OUT_DIR}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
