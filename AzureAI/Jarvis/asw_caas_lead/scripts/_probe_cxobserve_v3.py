"""
CX Observe probe v3 — full navigation drill on PepsiCo TPID 636846.
Search → click TPID link → customer summary → dump DOM for Consumption tile
and Related workloads elements.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright  # type: ignore

OUT_DIR = Path(__file__).parent.parent / "references" / "acr_probe_2026-07"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def log(msg: str) -> None:
    print(f"[probe3] {msg}", flush=True)


def dump(page, tag: str) -> None:
    try:
        (OUT_DIR / f"{tag}.html").write_text(page.content(), encoding="utf-8")
        page.screenshot(path=str(OUT_DIR / f"{tag}.png"), full_page=True)
        log(f"  saved {tag}.html + png (url={page.url[:120]})")
    except Exception as e:
        log(f"  dump {tag} failed: {e}")


def main() -> int:
    tpid = "636846"  # PepsiCo

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://localhost:9222")
        ctx = browser.contexts[0]

        target = None
        for pg in ctx.pages:
            if "cxp.azure.com" in pg.url:
                target = pg
                break
        if not target:
            target = ctx.pages[0]

        # --- Step 1: home → search TPID ---
        log("[1] navigating to home + typing TPID")
        target.goto("https://cxp.azure.com/cxobserve/home", wait_until="domcontentloaded", timeout=60000)
        time.sleep(4)

        search = target.locator("input[placeholder*='Search' i]").first
        search.click()
        search.fill("")
        search.type(tpid, delay=90)
        time.sleep(2)
        search.press("Enter")

        # --- Step 2: wait for search results table to have rows ---
        log("[2] waiting for search results row containing TPID text")
        target.wait_for_url("**allcustomers**", timeout=30000)
        # let grid load
        target.wait_for_load_state("networkidle", timeout=60000)
        # some tables render slowly; loop until we see the TPID appear in text
        for i in range(20):
            body_txt = target.evaluate("() => document.body.innerText")
            if tpid in body_txt and "Loading" not in body_txt.split(tpid, 1)[0][-40:]:
                log(f"  TPID visible in DOM at iteration {i}")
                break
            time.sleep(1)
        time.sleep(3)
        dump(target, "10_results")

        # --- Step 3: find and click the TPID link ---
        log("[3] looking for TPID link")
        # links / cells that contain just the TPID
        # try anchor first
        link = target.locator(f"a:has-text('{tpid}')").first
        try:
            link.wait_for(state="visible", timeout=8000)
            log("  found <a> with TPID text")
        except Exception:
            log("  no <a>; trying any element with TPID text and clickable role")
            link = target.locator(f"text={tpid}").first
            link.wait_for(state="visible", timeout=8000)

        pre_url = target.url
        link.click()
        # wait for URL to change
        for _ in range(20):
            time.sleep(1)
            if target.url != pre_url:
                break
        try:
            target.wait_for_load_state("networkidle", timeout=45000)
        except Exception:
            pass
        time.sleep(4)
        log(f"  after click url: {target.url[:160]}")
        dump(target, "20_customer_summary")

        # --- Step 4: inspect Consumption tile & Related workloads on summary page ---
        log("[4] inspecting summary content")
        for kw in ["Consumption", "Related workloads", "Top KPIs", "Insights at a glance", "Related Workloads"]:
            hits = target.locator(f"text={kw}").all()
            log(f"  '{kw}' matches: {len(hits)}")
            for i, h in enumerate(hits[:3]):
                try:
                    txt = h.inner_text().strip()[:120]
                    log(f"    [{i}] {txt!r}")
                except Exception:
                    pass

        # any tile-like elements
        log("[4b] looking for h3 / h4 headings")
        for hd in target.locator("h1, h2, h3, h4").all()[:30]:
            try:
                log(f"  <{hd.evaluate('el => el.tagName')}> {hd.inner_text().strip()[:80]!r}")
            except Exception:
                pass

        log("done")
        return 0


if __name__ == "__main__":
    sys.exit(main())
