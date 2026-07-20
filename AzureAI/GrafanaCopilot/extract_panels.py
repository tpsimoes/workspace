#!/usr/bin/env python3
"""Extract text + screenshots for specific Grafana panels (reuses logged-in Edge profile)."""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

PROFILE_DIR = Path(__file__).parent / ".pw-profile-msedge"
OUT_DIR = Path(__file__).parent / "captures"

PANELS = [
    "Node and TOR Placement",
    "Node and TOR Placement (Last 2 Days)",
]

def slug(t):
    import re
    return re.sub(r"[^a-zA-Z0-9]+", "-", t).strip("-").lower()[:60]

def main():
    url = sys.argv[1]
    OUT_DIR.mkdir(exist_ok=True)
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR), headless=False, no_viewport=True, channel="msedge")
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_selector('div.react-grid-item, [data-testid*="Panel header"]', timeout=120000)
        page.wait_for_timeout(4000)

        # Expand any collapsed rows.
        rows = page.locator('[data-testid*="dashboard-row-title"], .dashboard-row--collapsed')
        for i in range(rows.count()):
            try:
                rows.nth(i).click()
                page.wait_for_timeout(500)
            except Exception:
                pass

        # Scroll through to lazy-load everything.
        for _ in range(16):
            page.evaluate("""() => {const el=document.querySelector('[class*=\"scrollbar-view\"]')||document.scrollingElement;el.scrollTop+=el.clientHeight*0.85;}""")
            page.wait_for_timeout(700)
        page.evaluate("""() => {const el=document.querySelector('[class*=\"scrollbar-view\"]')||document.scrollingElement;el.scrollTop=0;}""")
        page.wait_for_timeout(1500)

        for title in PANELS:
            loc = page.locator(f'[data-testid="data-testid Panel header {title}"]')
            if loc.count() == 0:
                loc = page.get_by_text(title, exact=False)
            if loc.count() == 0:
                print(f"\n===== {title} =====\n[NOT FOUND]")
                continue
            header = loc.first
            try:
                header.scroll_into_view_if_needed(timeout=8000)
            except Exception:
                pass
            page.wait_for_timeout(1500)
            container = header.locator('xpath=ancestor::div[contains(@class,"react-grid-item")][1]')
            target = container.first if container.count() else header
            try:
                txt = target.inner_text(timeout=5000)
            except Exception as e:
                txt = f"[inner_text failed: {e}]"
            print(f"\n===== {title} =====\n{txt}")
            try:
                target.screenshot(path=str(OUT_DIR / f"x-{slug(title)}.png"))
            except Exception:
                pass
        ctx.close()

if __name__ == "__main__":
    main()
