#!/usr/bin/env python3
"""Capture and validate Grafana evidence in one authenticated Edge session."""
import argparse
import json
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

from PIL import Image
from playwright.sync_api import Error as PlaywrightError, sync_playwright

PROFILE_DIR = Path(__file__).parent / ".pw-profile-msedge"
OUT_DIR = Path(__file__).parent / "captures" / "all2"
PANEL_HEADER = '[data-testid*="Panel header"]'


class CaptureError(RuntimeError):
    pass


def autocrop(path, thresh=24, pad=10):
    """Trim empty near-black margins from a panel screenshot so the image
    hugs the actual content (title + table/graph) instead of leaving large
    black regions with no data/graphs."""
    with Image.open(path) as source:
        im = source.convert("RGB")
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
        // Flex ancestors otherwise shrink back and clip the expanded grid.
        const grid = el.querySelector('[role="grid"], table');
        if (grid) {
            const width = Math.ceil(grid.scrollWidth);
            const height = Math.ceil(grid.scrollHeight);
            const gridRect = grid.getBoundingClientRect();
            const sizes = [];
            for (let n = grid; n && el.contains(n); n = n.parentElement) {
                const rect = n.getBoundingClientRect();
                sizes.push([n, width + Math.max(0, gridRect.left - rect.left) + 8,
                               height + Math.max(0, gridRect.top - rect.top) + 8]);
            }
            for (const [n, w, h] of sizes) {
                save(n);
                n.style.setProperty('width', Math.ceil(w) + 'px', 'important');
                n.style.setProperty('height', Math.ceil(h) + 'px', 'important');
                n.style.setProperty('min-height', height + 'px', 'important');
                n.style.setProperty('max-height', 'none', 'important');
                n.style.setProperty('overflow', 'visible', 'important');
                n.style.setProperty('flex', 'none', 'important');
            }
        }
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
    except PlaywrightError as exc:
        print(f"[warn] Could not restore panel layout: {exc}", file=sys.stderr)


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
    except PlaywrightError as exc:
        raise CaptureError(f"Could not hide dashboard chrome: {exc}") from exc


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
    except PlaywrightError as exc:
        print(f"[warn] Could not restore dashboard chrome: {exc}", file=sys.stderr)


def panel_snapshot(panel):
    return panel.evaluate("""el => {
        const visible = n => {
            const r = n.getBoundingClientRect(), s = getComputedStyle(n);
            return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none';
        };
        const root = el.getBoundingClientRect();
        const rows = [...el.querySelectorAll('[role="row"],tr')].map(row => {
            const cells = [...row.children].filter(visible);
            const boxes = cells.map(c => c.getBoundingClientRect());
            return {
                text: row.innerText.trim(),
                visible: boxes.length > 0,
                clipped: boxes.some(r => r.top < root.top - 1 || r.bottom > root.bottom + 1 ||
                                         r.left < root.left - 1 || r.right > root.right + 1)
            };
        });
        const loading = [...el.querySelectorAll('[data-testid*="Panel loading bar"],.panel-loading,[aria-label="Panel loading bar"]')].some(visible);
        const errors = [...el.querySelectorAll('[aria-label="Panel error"],[data-testid*="Panel status error"],[role="alert"]')]
            .filter(visible).map(n => n.innerText.trim() || n.getAttribute('title') || n.getAttribute('aria-label') || 'Panel error');
        return {
            text: el.innerText.trim(), rows, loading, errors,
            table: !!el.querySelector('[role="grid"],table'),
            expected_rows: Number(el.querySelector('[role="grid"]')?.getAttribute('aria-rowcount') || 0),
            chart: [...el.querySelectorAll('canvas,.uplot,svg')].some(visible)
        };
    }""")


def validate_snapshot(snapshot, title, expanded=False):
    text = snapshot["text"]
    body = text.removeprefix(title).strip()
    no_data = bool(re.search(r"(?im)^\s*no data\s*$", body))
    # Grafana can attach its generic status badge to an empty result.
    errors = [
        error for error in snapshot["errors"]
        if not (no_data and error.strip().casefold() in ("no data", "panel status"))
    ]
    if errors:
        raise CaptureError(f"{title}: {'; '.join(errors)}")
    if snapshot["loading"]:
        return None
    if no_data:
        return "no_data"
    if not body:
        return None
    if snapshot["table"]:
        rows = snapshot["rows"]
        if len(rows) < 2 or not all(row["visible"] and row["text"] for row in rows[1:]):
            return None
        if expanded and any(row["clipped"] for row in rows if row["visible"]):
            return None
        if expanded and snapshot["expected_rows"] > len(rows):
            return None
    elif not snapshot["chart"] and not re.search(r"(?m)^\s*\d+(?:\.\d+)?\s*$", body):
        return None
    return "data"


def evidence_signature(snapshot):
    if snapshot["table"]:
        return tuple(row["text"] for row in snapshot["rows"])
    return snapshot["text"]


def wait_ready(panel, title, deadline, expanded=False):
    previous = None
    while time.monotonic() < deadline:
        snapshot = panel_snapshot(panel)
        status = validate_snapshot(snapshot, title, expanded)
        signature = (evidence_signature(snapshot), status)
        if status and signature == previous:
            return snapshot, status
        previous = signature if status else None
        panel.page.wait_for_timeout(250)
    raise CaptureError(f"{title}: content did not settle or remained clipped before the capture deadline")


def capture_panel(panel, title, index, out_dir, timeout=180):
    deadline = time.monotonic() + timeout
    error = None
    for attempt in range(2):
        attempt_deadline = min(deadline, time.monotonic() + timeout / 2)
        try:
            panel.scroll_into_view_if_needed(timeout=15000)
            snapshot, status = wait_ready(panel, title, attempt_deadline)
            if status == "no_data":
                return {"index": index, "title": title, "text": snapshot["text"],
                        "rows": [], "no_data": True, "status": status, "file": None}
            try:
                if snapshot["table"]:
                    expand_panel(panel)
                hide_chrome(panel.page)
                panel.evaluate("""el => {
                    document.querySelectorAll('div.react-grid-item').forEach(other => {
                        if (other === el) return;
                        window.__hidChrome.push([other,other.style.visibility,other.style.display]);
                        other.style.visibility = 'hidden';
                    });
                }""")
                snapshot, status = wait_ready(panel, title, attempt_deadline, expanded=True)
                if status != "data":
                    raise CaptureError(f"{title}: data changed during capture")
                filename = f"panel-{index:02d}-{slug(title)}.png"
                path = out_dir / filename
                panel.page.mouse.move(0, 0)
                panel.screenshot(path=str(path), timeout=20000, animations="disabled")
                # Screenshot scrolling can rerender table chrome without changing its data.
                after, status = wait_ready(panel, title, attempt_deadline, expanded=True)
                if status != "data" or evidence_signature(after) != evidence_signature(snapshot):
                    (out_dir / f"panel-{index:02d}-validation.json").write_text(
                        json.dumps({"title": title, "before": snapshot, "after": after}, indent=2),
                        encoding="utf-8",
                    )
                    raise CaptureError(f"{title}: content changed while taking screenshot")
                autocrop(path)
                with Image.open(path) as image:
                    image.verify()
                return {"index": index, "title": title, "text": after["text"],
                        "rows": [row["text"] for row in after["rows"]],
                        "no_data": False, "status": "data", "file": filename}
            finally:
                restore_chrome(panel.page)
                restore_panel(panel)
        except (CaptureError, PlaywrightError, OSError) as exc:
            error = str(exc)
            print(f"[warn] {title}: capture attempt {attempt + 1} failed: {exc}", file=sys.stderr)
            if panel.page.is_closed():
                raise CaptureError("Browser closed; stopping without relaunch or another sign-in") from exc
            if not panel.page.locator(f"div.react-grid-item {PANEL_HEADER}").count():
                raise CaptureError("Dashboard session lost; stopping without another sign-in") from exc
    return {"index": index, "title": title, "text": "", "rows": [],
            "no_data": False, "status": "error", "error": error, "file": None}


def capture_dashboard(page, out_dir):
    for _ in range(6):
        collapsed = page.locator(
            '.dashboard-row--collapsed [data-testid*="dashboard-row-title"], '
            '[aria-expanded="false"][data-testid*="dashboard-row"]'
        )
        if not collapsed.count():
            break
        for row in collapsed.all():
            row.click()
    # Bring every lazy-loaded panel into view before resolving titles.
    for panel in page.locator("div.react-grid-item").all():
        panel.scroll_into_view_if_needed(timeout=15000)
        page.wait_for_timeout(150)
    manifest = []
    titles = set()
    for index, panel in enumerate(page.locator("div.react-grid-item").all()):
        panel.scroll_into_view_if_needed(timeout=15000)
        header = panel.locator(PANEL_HEADER)
        if not header.count():
            if panel.locator('[data-testid*="dashboard-row"]').count():
                continue
            raise CaptureError(f"Grid item {index} has no loaded panel header")
        title = (header.first.get_attribute("data-testid") or "").replace(
            "data-testid Panel header", ""
        ).strip()
        if not title or title in titles:
            raise CaptureError(f"Missing or duplicate panel title: {title!r}")
        titles.add(title)
        record = capture_panel(panel, title, index, out_dir)
        manifest.append(record)
        (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        print(f"[{index:02d}] {title}: {record['status']}", flush=True)
    if not manifest:
        raise CaptureError("No dashboard panels were captured")
    errors = [record["title"] for record in manifest if record["status"] == "error"]
    if errors:
        raise CaptureError(f"Evidence validation failed: {', '.join(errors)}. Inspect manifest.json; do not relaunch automatically.")
    return manifest


def capture_in_context(context, url, out_dir):
    """Reuse a caller-owned context without launching or closing a browser."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    page = next((page for page in context.pages if page.url == url), None)
    if page is None:
        page = next((page for page in context.pages if page.url == "about:blank"), None)
    if page is None:
        page = context.new_page()
    if page.url != url:
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
    print("Using one Edge session. If sign-in is required, complete it in this tab; no alternative login will be opened.", flush=True)
    try:
        page.wait_for_selector(f"div.react-grid-item {PANEL_HEADER}", timeout=120000)
    except PlaywrightError as exc:
        raise CaptureError("Dashboard unavailable after waiting for sign-in; stopping without opening another session") from exc
    return capture_dashboard(page, out_dir)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url", help="Grafana dashboard URL")
    parser.add_argument("out_dir", nargs="?", type=Path, default=OUT_DIR)
    args = parser.parse_args(argv)
    parsed = urlparse(args.url)
    if parsed.scheme != "https" or not parsed.netloc:
        parser.error("Use an HTTPS Grafana dashboard URL")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    try:
        with sync_playwright() as playwright:
            context = playwright.chromium.launch_persistent_context(
                user_data_dir=str(PROFILE_DIR), headless=False, no_viewport=True, channel="msedge")
            try:
                manifest = capture_in_context(context, args.url, args.out_dir)
            finally:
                context.close()
    except (CaptureError, PlaywrightError, OSError) as exc:
        print(f"[error] {exc}\nNo browser relaunch or additional authentication was attempted.", file=sys.stderr)
        return 1
    print(f"Validated {len(manifest)} panels in {time.monotonic() - started:.1f}s. "
          f"Build the report offline from {args.out_dir / 'manifest.json'}.", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
