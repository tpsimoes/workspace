#!/usr/bin/env python3
"""
Capture Grafana panels as screenshots for analysis.

Opens the given Grafana dashboard URL in a headed, persistent-profile browser so
the user can sign in interactively (Azure AD). Waits for the dashboard to render,
scrolls to trigger lazy-loaded panels, then captures:
  - a full-page screenshot
  - one screenshot per requested panel title (best-effort)

Usage:
  python capture_panels.py "<dashboard_url>" --panel "Scheduled Events" --panel "RCA Helper: Node Events and Errors"
"""

import argparse
import re
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

PROFILE_DIR = Path(__file__).parent / ".pw-profile"
OUT_DIR = Path(__file__).parent / "captures"


def slug(text: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()


def scroll_dashboard(page, steps: int = 12, pause: float = 0.6):
    """Scroll the Grafana dashboard scroll-container to force lazy panel loads."""
    js = """
    () => {
      const el = document.querySelector('[class*="scrollbar-view"]')
             || document.scrollingElement || document.body;
      const before = el.scrollTop;
      el.scrollTop = el.scrollTop + el.clientHeight * 0.9;
      return {top: el.scrollTop, height: el.scrollHeight, client: el.clientHeight, before};
    }
    """
    last = -1
    for _ in range(steps):
        info = page.evaluate(js)
        page.wait_for_timeout(int(pause * 1000))
        if info["top"] == last:
            break
        last = info["top"]
    # back to top for the full-page capture
    page.evaluate("""() => {
        const el = document.querySelector('[class*="scrollbar-view"]')
               || document.scrollingElement || document.body;
        el.scrollTop = 0;
    }""")
    page.wait_for_timeout(800)


def capture_panel(page, title: str, out_dir: Path):
    """Best-effort screenshot of a single Grafana panel by its title text."""
    out = out_dir / f"panel-{slug(title)}.png"
    # Grafana renders panel headers with a data-testid of "Panel header <title>".
    candidates = [
        f'[data-testid="data-testid Panel header {title}"]',
        f'[data-testid="Panel header {title}"]',
    ]
    header = None
    for sel in candidates:
        loc = page.locator(sel)
        if loc.count() > 0:
            header = loc.first
            break
    if header is None:
        # Fallback: match the visible title text.
        loc = page.get_by_text(title, exact=False)
        if loc.count() > 0:
            header = loc.first
    if header is None:
        print(f"  [miss] panel not found: {title!r}", file=sys.stderr)
        return None

    header.scroll_into_view_if_needed(timeout=10000)
    page.wait_for_timeout(1200)
    # Climb to the panel container for a full-panel shot.
    panel = header.locator(
        'xpath=ancestor-or-self::*[contains(@class,"react-grid-item") '
        'or contains(@data-testid,"data-testid panel content") '
        'or contains(@class,"panel-container")][1]'
    )
    target = panel.first if panel.count() > 0 else header
    try:
        target.screenshot(path=str(out))
    except Exception as exc:
        print(f"  [warn] container shot failed for {title!r} ({exc}); header only", file=sys.stderr)
        header.screenshot(path=str(out))
    print(f"  [ok] {out}")
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Screenshot Grafana panels for analysis.")
    ap.add_argument("url", help="Full Grafana dashboard URL.")
    ap.add_argument("--panel", action="append", default=[], help="Panel title to capture (repeatable).")
    ap.add_argument("--login-wait", type=int, default=240,
                    help="Max seconds to wait for the dashboard to render (allows interactive login).")
    ap.add_argument("--channel", default="msedge",
                    help="Browser channel: msedge (default, satisfies Conditional Access), chrome, or '' for bundled Chromium.")
    args = ap.parse_args(argv)

    OUT_DIR.mkdir(exist_ok=True)
    profile_dir = PROFILE_DIR.parent / (PROFILE_DIR.name + ("-" + args.channel if args.channel else ""))
    profile_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        launch_kwargs = dict(
            user_data_dir=str(profile_dir),
            headless=False,
            no_viewport=True,
        )
        if args.channel:
            launch_kwargs["channel"] = args.channel
        try:
            ctx = p.chromium.launch_persistent_context(**launch_kwargs)
        except Exception as exc:
            print(f"  [warn] could not launch channel {args.channel!r} ({exc}); using bundled Chromium",
                  file=sys.stderr)
            launch_kwargs.pop("channel", None)
            ctx = p.chromium.launch_persistent_context(**launch_kwargs)
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        print(f"Opening dashboard... sign in if prompted (waiting up to {args.login_wait}s).")
        try:
            page.goto(args.url, wait_until="domcontentloaded", timeout=60000)
        except Exception as exc:
            print(f"  [warn] initial navigation: {exc}", file=sys.stderr)

        def live_grafana_page():
            """Return an open page currently on the grafana host (login may swap tabs)."""
            for pg in ctx.pages:
                try:
                    if pg.is_closed():
                        continue
                    if "grafana.azure.com" in (pg.url or ""):
                        return pg
                except Exception:
                    continue
            # fall back to any open page
            for pg in ctx.pages:
                if not pg.is_closed():
                    return pg
            return None

        # Wait for a real panel grid item to appear (post-login, post-render).
        deadline = time.time() + args.login_wait
        loaded = False
        while time.time() < deadline:
            page = live_grafana_page()
            if page is None:
                print("Browser was closed before the dashboard loaded.", file=sys.stderr)
                try:
                    ctx.close()
                except Exception:
                    pass
                return 1
            try:
                if "grafana.azure.com" in (page.url or "") and \
                   page.locator('div.react-grid-item, [data-testid*="Panel header"]').count() > 0:
                    loaded = True
                    break
            except Exception:
                pass
            try:
                page.wait_for_timeout(1500)
            except Exception:
                time.sleep(1.5)
        if not loaded:
            print("Dashboard panels did not render in time.", file=sys.stderr)
            ctx.close()
            return 1

        page.wait_for_timeout(2500)
        print("Dashboard loaded. Scrolling to load all panels...")
        scroll_dashboard(page)

        full = OUT_DIR / "dashboard-full.png"
        try:
            page.screenshot(path=str(full), full_page=True)
            print(f"  [ok] {full}")
        except Exception as exc:
            print(f"  [warn] full-page shot failed: {exc}", file=sys.stderr)

        for title in args.panel:
            print(f"Capturing panel: {title}")
            capture_panel(page, title, OUT_DIR)

        ctx.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
