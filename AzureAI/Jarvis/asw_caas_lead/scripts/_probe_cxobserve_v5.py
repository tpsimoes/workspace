"""
Probe v5 — figure out the correct click target on a customer row.
The TPID link (636846) is target=_blank; clicking it opens a new tab.
Instead we need to click on the row itself (customer name) or find the
per-row 'View' button that opens the customer summary panel.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright  # type: ignore

OUT_DIR = Path(__file__).parent.parent / "references" / "acr_probe_2026-07"


def main() -> int:
    tpid = "636846"
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://localhost:9222")
        ctx = browser.contexts[0]
        target = None
        for pg in ctx.pages:
            if "cxp.azure.com" in pg.url:
                target = pg
                break
        if not target:
            print("no cxobserve tab"); return 1
        target.set_default_timeout(30000)

        # search
        target.goto("https://cxp.azure.com/cxobserve/home", wait_until="domcontentloaded", timeout=45000)
        time.sleep(3)
        sb = target.locator("input[placeholder*='Search' i]").first
        sb.click(); sb.fill(""); sb.type(tpid, delay=80); time.sleep(1.5); sb.press("Enter")
        target.wait_for_url("**allcustomers**", timeout=20000)
        try:
            target.wait_for_load_state("networkidle", timeout=30000)
        except Exception:
            pass
        time.sleep(4)

        # inspect anchor properties
        anchors = target.evaluate("""(tpid) => {
            const all = Array.from(document.querySelectorAll('a'));
            return all
              .filter(a => (a.innerText || '').trim() === tpid)
              .map(a => ({
                  text: a.innerText.trim(),
                  href: a.href,
                  target: a.target,
                  rect: {x: Math.round(a.getBoundingClientRect().left), y: Math.round(a.getBoundingClientRect().top)},
                  ariaLabel: a.getAttribute('aria-label')
              }));
        }""", tpid)
        print(f"anchors matching '{tpid}':")
        for a in anchors:
            print(f"  {a}")

        # find rows containing 636846 and dump their structure
        row_info = target.evaluate("""(tpid) => {
            const rows = Array.from(document.querySelectorAll('[role="row"]'));
            const hits = [];
            for (const r of rows) {
                if ((r.innerText || '').includes(tpid)) {
                    // enumerate children
                    const cells = Array.from(r.querySelectorAll('[role="cell"], [role="gridcell"], td'));
                    hits.push({
                        rowRect: r.getBoundingClientRect(),
                        rowIndex: r.getAttribute('aria-rowindex') || null,
                        cellCount: cells.length,
                        cellTexts: cells.map(c => (c.innerText||'').trim().slice(0, 60)),
                    });
                }
            }
            return hits;
        }""", tpid)
        print(f"grid rows containing '{tpid}':")
        for r in row_info:
            print(f"  {r}")

        # look for a "View" per-row button on hover — first hover the row containing PepsiCo, then screenshot
        try:
            pepsi_row = target.locator("[role='row']:has-text('PepsiCo')").first
            pepsi_row.hover()
            time.sleep(2)
            # after hover, dump all buttons in that row
            btns = pepsi_row.evaluate("""el => {
                const bs = Array.from(el.querySelectorAll('button, a, [role="button"], [role="link"]'));
                return bs.map(b => ({
                    tag: b.tagName,
                    text: (b.innerText || '').trim().slice(0, 60),
                    aria: b.getAttribute('aria-label'),
                    href: b.getAttribute('href'),
                    target: b.getAttribute('target'),
                    role: b.getAttribute('role'),
                }));
            }""")
            print(f"buttons/links inside PepsiCo row (after hover):")
            for b in btns:
                print(f"  {b}")
        except Exception as e:
            print(f"row hover err: {e}")

        # try: click the row body (Not the TPID anchor)
        try:
            row = target.locator("[role='row']:has-text('PepsiCo')").first
            box = row.bounding_box()
            print(f"pepsi row box: {box}")
            if box:
                # click on customer initial avatar area (leftmost)
                target.mouse.click(box["x"] + 30, box["y"] + box["height"] / 2)
                time.sleep(4)
                target.screenshot(path=str(OUT_DIR / "40_after_row_click.png"), timeout=20000, animations="disabled")
                print(f"screenshot after row click: url={target.url[:120]}")
                # search for PepsiCo header text
                pep = target.evaluate("() => document.body.innerText.includes('PepsiCo')")
                print(f"body contains 'PepsiCo': {pep}")
        except Exception as e:
            print(f"row click err: {e}")

        return 0


if __name__ == "__main__":
    sys.exit(main())
