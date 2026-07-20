#!/usr/bin/env python3
"""Enumerate and capture EVERY panel on the Grafana VM Analyzer dashboard.

Writes captures/all/panel-NN-<slug>.png plus captures/all/manifest.json with
{index, title, text, no_data, file} for each panel, for downstream relevance
classification.
"""
import json
import re
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

PROFILE_DIR = Path(__file__).parent / ".pw-profile-msedge"
OUT_DIR = Path(__file__).parent / "captures" / "all2"


def autocrop(path, thresh=24, pad=10):
    """Trim empty near-black margins from a panel screenshot so the image
    hugs the actual content (title + table/graph) instead of leaving large
    black regions with no data/graphs."""
    try:
        from PIL import Image
    except Exception:
        return
    try:
        im = Image.open(path).convert("RGB")
    except Exception:
        return
    gray = im.convert("L")
    mask = gray.point(lambda x: 255 if x > thresh else 0)
    bbox = mask.getbbox()
    if not bbox:
        return
    l, t, r, b = bbox
    # Keep a small padding and never crop below a sane minimum size.
    l = max(0, l - pad)
    t = max(0, t - pad)
    r = min(im.width, r + pad)
    b = min(im.height, b + pad)
    if r - l < 20 or b - t < 20:
        return
    if (l, t, r, b) != (0, 0, im.width, im.height):
        im.crop((l, t, r, b)).save(path)


def slug(t):
    return re.sub(r"[^a-zA-Z0-9]+", "-", t or "panel").strip("-").lower()[:50] or "panel"


def expand_panel(panel):
    """Grow a panel and its internal scroll containers so a full-element
    screenshot captures every row/column (Grafana tables are virtualized and
    horizontally/vertically scrollable inside a fixed-height panel).

    Uses explicit pixel heights only (never height:auto, which collapses the
    absolutely-positioned .react-grid-item to 0), saves original inline styles,
    and can be reverted via restore_panel()."""
    grow_js = """(el) => {
        if (!el.__expandSaved) el.__expandSaved = [];
        const save = (n) => { el.__expandSaved.push([n, n.getAttribute('style')]); };
        // Run several bottom-up passes: expanding an inner scroller makes its
        // ancestors clip, so re-detect and expand them too.
        for (let pass = 0; pass < 4; pass++) {
            el.querySelectorAll('*').forEach((n) => {
                const sy = n.scrollHeight - n.clientHeight > 4;
                const sx = n.scrollWidth - n.clientWidth > 4;
                if (sy || sx) {
                    save(n);
                    n.style.overflow = 'visible';
                    n.style.overflowX = 'visible';
                    n.style.overflowY = 'visible';
                    n.style.maxHeight = 'none';
                    n.style.maxWidth = 'none';
                    if (sy) n.style.height = n.scrollHeight + 'px';
                    if (sx) n.style.width = n.scrollWidth + 'px';
                }
            });
        }
        // Finally size the grid item itself to fit its (now expanded) content.
        save(el);
        el.style.overflow = 'visible';
        el.style.maxHeight = 'none';
        el.style.height = el.scrollHeight + 'px';
        // De-stick table headers: when the scroll container is expanded, a
        // position:sticky header resolves against the page and drifts (behind
        // the top toolbar, or to the very bottom). Force it into normal flow so
        // it renders at the top of the table and is captured with its columns.
        el.querySelectorAll('*').forEach((n) => {
            const cs = getComputedStyle(n);
            if (cs.position === 'sticky') {
                save(n);
                n.style.position = 'static';
            }
        });
        window.dispatchEvent(new Event('resize'));
    }"""
    panel.evaluate(grow_js)
    # Let virtualized tables (react-window / AutoSizer) render newly visible
    # rows after the height grew, then expand again to fit them.
    panel.page.wait_for_timeout(700)
    panel.evaluate(grow_js)


def restore_panel(panel):
    """Revert the inline styles changed by expand_panel so expanded panels do
    not visually overlap subsequently captured panels."""
    try:
        panel.evaluate(
            """(el) => {
                (el.__expandSaved || []).slice().reverse().forEach(([n, s]) => {
                    if (s === null) n.removeAttribute('style');
                    else n.setAttribute('style', s);
                });
                el.__expandSaved = [];
                window.dispatchEvent(new Event('resize'));
            }"""
        )
    except Exception:
        pass


def hide_chrome(page):
    """Hide fixed/sticky page chrome (Grafana top nav, toolbar, time picker)
    that would otherwise bleed into the top of a tall panel's element
    screenshot. Only elements OUTSIDE any panel are hidden; panel content is
    left untouched. Reverted by restore_chrome()."""
    try:
        page.evaluate(
            """() => {
                window.__hidChrome = [];
                const hideEl = (n, mode) => {
                    if (n.closest('div.react-grid-item')) return;
                    window.__hidChrome.push([n, n.style.visibility, n.style.display]);
                    if (mode === 'display') n.style.display = 'none';
                    else n.style.visibility = 'hidden';
                };
                // Out-of-flow page chrome (Grafana top nav / dashboard toolbar /
                // time picker) that would composite into a tall panel's element
                // screenshot. fixed/absolute -> display:none (out of flow, no
                // layout shift); sticky -> visibility:hidden (keep flow intact).
                document.querySelectorAll('body *').forEach((n) => {
                    const cs = getComputedStyle(n);
                    if (cs.position === 'fixed' || cs.position === 'absolute') hideEl(n, 'display');
                    else if (cs.position === 'sticky') hideEl(n, 'visibility');
                });
                // Belt-and-suspenders: hide the top chrome landmarks by tag even
                // if their computed position shifts on scroll during capture.
                document.querySelectorAll('header, nav, [role="banner"]').forEach((n) => hideEl(n, 'display'));
            }"""
        )
    except Exception:
        pass


def restore_chrome(page):
    try:
        page.evaluate(
            """() => {
                (window.__hidChrome || []).forEach(([n, v, d]) => {
                    n.style.visibility = v; n.style.display = d;
                });
                window.__hidChrome = [];
            }"""
        )
    except Exception:
        pass


def main():
    url = sys.argv[1]
    out_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else OUT_DIR
    if out_dir.exists():
        for f in out_dir.glob("*"):
            f.unlink()
    out_dir.mkdir(parents=True, exist_ok=True)
    globals()["OUT_DIR"] = out_dir

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR), headless=False, no_viewport=True, channel="msedge")
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_selector('div.react-grid-item, [data-testid*="Panel header"]', timeout=120000)
        page.wait_for_timeout(4000)

        # Expand collapsed rows (repeat until none left).
        for _ in range(6):
            collapsed = page.locator('.dashboard-row--collapsed [data-testid*="dashboard-row-title"], '
                                     '[aria-expanded="false"][data-testid*="dashboard-row"]')
            n = collapsed.count()
            if n == 0:
                break
            for i in range(n):
                try:
                    collapsed.nth(i).click()
                    page.wait_for_timeout(400)
                except Exception:
                    pass

        # Also click any row title that looks collapsed (fallback).
        titles = page.locator('[data-testid*="dashboard-row-title"]')
        for i in range(titles.count()):
            try:
                el = titles.nth(i)
                if el.get_attribute("aria-expanded") == "false":
                    el.click(); page.wait_for_timeout(400)
            except Exception:
                pass

        def loading_count():
            sels = ('[data-testid="data-testid Panel loading bar"]',
                    '.panel-loading', 'div[class*="LoadingBar"]',
                    '[aria-label="Panel loading bar"]')
            total = 0
            for s in sels:
                try:
                    total += page.locator(s).count()
                except Exception:
                    pass
            return total

        def wait_loaded(label="", settle=2500, timeout=90000):
            import time as _t
            end = _t.time() + timeout / 1000
            stable = 0
            while _t.time() < end:
                lc = loading_count()
                if lc == 0:
                    stable += 1
                    if stable >= 3:
                        break
                else:
                    stable = 0
                page.wait_for_timeout(700)
            page.wait_for_timeout(settle)

        # Multiple full scroll passes so every panel enters the viewport and lazy-loads,
        # waiting for loading bars to clear after each pass.
        for _pass in range(3):
            for _ in range(30):
                page.evaluate("""() => {const el=document.querySelector('[class*=\"scrollbar-view\"]')||document.scrollingElement;el.scrollTop+=el.clientHeight*0.7;}""")
                page.wait_for_timeout(450)
                if loading_count() > 0:
                    page.wait_for_timeout(600)
            page.evaluate("""() => {const el=document.querySelector('[class*=\"scrollbar-view\"]')||document.scrollingElement;el.scrollTop=0;}""")
            wait_loaded(f"pass{_pass}")
        page.wait_for_timeout(1500)

        panels = page.locator('div.react-grid-item')
        total = panels.count()
        print(f"Found {total} panels")
        manifest = []
        for i in range(total):
            panel = panels.nth(i)
            # Title from panel header testid.
            title = ""
            hdr = panel.locator('[data-testid^="data-testid Panel header"]')
            if hdr.count() > 0:
                dt = hdr.first.get_attribute("data-testid") or ""
                title = dt.replace("data-testid Panel header", "").strip()
            if not title:
                h = panel.locator('h2, h6, [class*="panel-title"]')
                if h.count() > 0:
                    try:
                        title = h.first.inner_text(timeout=1500).strip()
                    except Exception:
                        pass
            try:
                panel.scroll_into_view_if_needed(timeout=6000)
            except Exception:
                pass
            # Wait for this panel's own loading bar to clear.
            for _ in range(20):
                try:
                    lb = panel.locator('[data-testid="data-testid Panel loading bar"], '
                                       '.panel-loading, div[class*="LoadingBar"]')
                    if lb.count() == 0:
                        break
                except Exception:
                    break
                page.wait_for_timeout(500)
            page.wait_for_timeout(1200)
            try:
                text = panel.inner_text(timeout=4000)
            except Exception as e:
                text = f"[inner_text failed: {e}]"
            no_data = "No data" in text and len(text.strip()) < len(title) + 40
            fname = f"panel-{i:02d}-{slug(title)}.png"
            # Expand internal scroll containers (tables) so the screenshot shows
            # ALL rows/columns instead of just the clipped, scrollable viewport.
            try:
                expand_panel(panel)
                page.wait_for_timeout(900)
            except Exception:
                pass
            try:
                hide_chrome(page)
                panel.screenshot(path=str(OUT_DIR / fname), timeout=15000)
                autocrop(OUT_DIR / fname)
            except Exception as e:
                print(f"  [warn] shot {i} failed: {e}")
                fname = None
            finally:
                restore_chrome(page)
            restore_panel(panel)
            manifest.append({
                "index": i, "title": title, "no_data": no_data,
                "text": text.strip(), "file": fname,
            })
            print(f"  [{i:02d}] {title!r} no_data={no_data} chars={len(text.strip())}")

        (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        print(f"Wrote manifest with {len(manifest)} panels")
        ctx.close()


if __name__ == "__main__":
    main()
