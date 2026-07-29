"""Probe: read ACU values from CX Observe consumption chart via hover tooltip.

Prereq: Edge on CDP:9222 with cxp.azure.com session logged in, and the browser
already on a customer's workload Consumption details page (or we'll drive to it).

Usage:
    python -u Skills/asw_caas_lead/scripts/_probe_chart_hover.py [tpid]

If [tpid] omitted, assumes the current tab is already on a Consumption details page.
Prints DOM discovery info + tooltip readings for the last 2 monthly data points.
"""
from __future__ import annotations
import re
import sys
import time
import json
from playwright.sync_api import sync_playwright, Page


def log(msg: str) -> None:
    print(f"[probe] {msg}", flush=True)


def find_chart_info(page: Page) -> dict:
    """Locate the Consumption line chart and its data points on the current page.
    Handles two structures:
      - static markers (many <circle> elements)
      - dynamic marker (single <circle>) with data encoded in the line <path> `d` attribute
    """
    js = r"""
    () => {
        function collectDocs(root) {
            const docs = [root];
            for (const f of root.querySelectorAll('iframe')) {
                try { const d = f.contentDocument; if (d) docs.push(d); }
                catch (e) {}
            }
            return docs;
        }
        function parsePathD(d) {
            // Extract coordinate pairs from an SVG d string. Handles M/L/C/S commands.
            // Returns array of {x, y} in the local SVG coordinate space.
            if (!d) return [];
            const pts = [];
            // Tokenize into commands + numbers
            const parts = d.match(/[a-zA-Z]|[-+]?[\d.]+(?:e[-+]?\d+)?/gi) || [];
            let cmd = null;
            let curX = 0, curY = 0;
            let i = 0;
            const nums = [];
            for (const p of parts) {
                if (/^[a-zA-Z]$/.test(p)) {
                    // flush
                    cmd = p;
                    nums.length = 0;
                    continue;
                }
                nums.push(parseFloat(p));
                // Consume when we have enough
                const relative = cmd === cmd.toLowerCase();
                const C = cmd.toUpperCase();
                let need = 0;
                if (C === 'M' || C === 'L' || C === 'T') need = 2;
                else if (C === 'H' || C === 'V') need = 1;
                else if (C === 'C') need = 6;
                else if (C === 'S' || C === 'Q') need = 4;
                else if (C === 'A') need = 7;
                else if (C === 'Z') need = 0;
                else need = 2;
                if (nums.length >= need) {
                    let x, y;
                    if (C === 'M' || C === 'L' || C === 'T') { x = nums[0]; y = nums[1]; }
                    else if (C === 'H') { x = nums[0]; y = curY; }
                    else if (C === 'V') { x = curX; y = nums[0]; }
                    else if (C === 'C') { x = nums[4]; y = nums[5]; }
                    else if (C === 'S' || C === 'Q') { x = nums[2]; y = nums[3]; }
                    else if (C === 'A') { x = nums[5]; y = nums[6]; }
                    else { x = nums[0]; y = nums[1]; }
                    if (relative) { x += curX; y += curY; }
                    // Record data-point endpoints (M/L/H/V/C/S/T all move to a real point)
                    if ('MLHVCST'.indexOf(C) >= 0) {
                        pts.push({ x, y, cmd: C });
                    }
                    curX = x; curY = y;
                    nums.length = 0;
                    // After M with extra pairs, subsequent implicit L
                    if (C === 'M') cmd = relative ? 'l' : 'L';
                }
            }
            return pts;
        }
        const results = { charts: [], iframes: 0 };
        const docs = collectDocs(document);
        results.iframes = docs.length - 1;
        for (let di = 0; di < docs.length; di++) {
            const doc = docs[di];
            const svgs = Array.from(doc.querySelectorAll('svg'));
            for (let i = 0; i < svgs.length; i++) {
                const svg = svgs[i];
                const rect = svg.getBoundingClientRect();
                if (rect.width < 200 || rect.height < 80) continue;
                // Compute SVG->screen transform via CTM of the first suitable inner element
                let pts = [];
                let kind = 'unknown';
                const circles = Array.from(svg.querySelectorAll('circle'));
                if (circles.length >= 2 && circles.length <= 80) {
                    pts = circles.map(c => {
                        const r = c.getBoundingClientRect();
                        return { x: r.x + r.width/2, y: r.y + r.height/2 };
                    });
                    kind = 'circles';
                } else {
                    // Parse line paths. Pick the path with the most data points and non-trivial length.
                    const paths = Array.from(svg.querySelectorAll('path'));
                    let bestPath = null, bestPts = [];
                    for (const p of paths) {
                        const d = p.getAttribute('d') || '';
                        const parsed = parsePathD(d);
                        // Data points = M/L/H/V/C endpoints (each control-point endpoint is a real point)
                        const dataPts = parsed.filter(pt => 'MLHVCST'.indexOf(pt.cmd) >= 0);
                        if (dataPts.length > bestPts.length && dataPts.length >= 2 && dataPts.length <= 80) {
                            bestPath = p;
                            bestPts = dataPts;
                        }
                    }
                    if (bestPath && bestPts.length >= 2) {
                        // Convert SVG coords to screen coords using the path's CTM
                        const ctm = bestPath.getScreenCTM();
                        if (ctm) {
                            pts = bestPts.map(pt => {
                                const svgPt = svg.createSVGPoint();
                                svgPt.x = pt.x; svgPt.y = pt.y;
                                const s = svgPt.matrixTransform(ctm);
                                return { x: s.x, y: s.y };
                            });
                            kind = 'path-line';
                        }
                    }
                }
                if (pts.length === 0) continue;
                let ctx = '';
                let node = svg.parentElement;
                let steps = 0;
                while (node && steps < 8) {
                    const txt = (node.innerText || '').slice(0, 400);
                    if (/Azure Consumption Units|Consumption Units|Usage per month|per month/i.test(txt)) {
                        ctx = txt.replace(/\s+/g, ' ').slice(0, 300);
                        break;
                    }
                    node = node.parentElement;
                    steps++;
                }
                pts.sort((a, b) => a.x - b.x);
                results.charts.push({
                    doc_idx: di,
                    idx: i,
                    width: Math.round(rect.width),
                    height: Math.round(rect.height),
                    x: Math.round(rect.x),
                    y: Math.round(rect.y),
                    points_count: pts.length,
                    kind,
                    ctx_snippet: ctx,
                    points: pts,
                });
            }
        }
        return results;
    }
    """
    return page.evaluate(js)


def read_tooltip_text(page: Page, near_x: float | None = None, near_y: float | None = None) -> str:
    """Grab the currently-visible tooltip text near the given (x,y).
    Filters to elements whose text plausibly matches the chart tooltip pattern.
    """
    js = r"""
    (args) => {
        const nearX = args && args.nearX;
        const nearY = args && args.nearY;
        function collectDocs(root) {
            const docs = [root];
            for (const f of root.querySelectorAll('iframe')) {
                try { const d = f.contentDocument; if (d) docs.push(d); }
                catch (e) {}
            }
            return docs;
        }
        const sels = [
            '[role="tooltip"]',
            '.tooltipContent',
            '.tooltip-container',
            '[class*="tooltip" i]',
            '[class*="Tooltip" i]',
            '[data-testid*="tooltip" i]',
            'div[style*="pointer-events: none"]',
        ];
        const chartRe = /Usage|\d+\.?\d*\s*[KMB]|\d{1,2}\/\d{1,2}\/\d{2,4}/;
        const found = [];
        for (const doc of collectDocs(document)) {
            const seen = new Set();
            for (const s of sels) {
                for (const el of doc.querySelectorAll(s)) {
                    if (seen.has(el)) continue;
                    seen.add(el);
                    let style;
                    try { style = (el.ownerDocument.defaultView || window).getComputedStyle(el); }
                    catch (e) { continue; }
                    if (style.visibility === 'hidden' || style.display === 'none' || parseFloat(style.opacity) < 0.05) continue;
                    const r = el.getBoundingClientRect();
                    if (r.width < 20 || r.height < 10) continue;
                    if (r.width > 600) continue;   // real tooltips are small
                    if (r.height > 300) continue;
                    const t = (el.innerText || el.textContent || '').trim();
                    if (!t || t.length > 300) continue;
                    if (!chartRe.test(t)) continue;   // must look like a chart tooltip
                    // Compute distance to hover point
                    let dist = Infinity;
                    if (nearX !== null && nearY !== null) {
                        const cx = r.x + r.width/2, cy = r.y + r.height/2;
                        dist = Math.hypot(cx - nearX, cy - nearY);
                    }
                    found.push({ text: t, dist, x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) });
                }
            }
        }
        // Prefer the nearest match
        found.sort((a, b) => a.dist - b.dist);
        return found;
    }
    """
    result = page.evaluate(js, {"nearX": near_x, "nearY": near_y})
    if not result:
        return ""
    # Return the closest tooltip's text
    return result[0].get("text", "")


def read_chart_header(page: Page) -> dict:
    """Read the static ACU header shown above the chart, e.g.
    "907.6K Azure Consumption Units" + delta "-95.16K (-9.49%) vs previous..."
    """
    js = r"""
    () => {
        function collectDocs(root) {
            const docs = [root];
            for (const f of root.querySelectorAll('iframe')) {
                try { const d = f.contentDocument; if (d) docs.push(d); }
                catch (e) {}
            }
            return docs;
        }
        const docs = collectDocs(document);
        let headline = null, delta = null, size = 0;
        // Headline: text that starts with a number, ends with 'Azure Consumption Units'
        const headRe = /^\s*[\d,]+\.?\d*\s*[KMB]?\s+Azure Consumption Units\s*$/i;
        const deltaRe = /vs previous/i;
        for (const doc of docs) {
            const walker = doc.createTreeWalker(doc.body || doc, NodeFilter.SHOW_TEXT);
            let node;
            while ((node = walker.nextNode())) {
                const t = (node.nodeValue || '').trim();
                if (!t) continue;
                if (!headline && headRe.test(t)) {
                    // Prefer the largest font-size occurrence
                    try {
                        const parent = node.parentElement;
                        const fs = parent ? parseFloat(window.getComputedStyle(parent).fontSize) || 0 : 0;
                        if (fs > size) { headline = t; size = fs; }
                    } catch (e) { headline = headline || t; }
                }
                if (!delta && deltaRe.test(t) && t.length < 400) {
                    delta = t;
                }
                if (headline && delta) break;
            }
            if (headline && delta) break;
        }
        return { headline, delta, headline_font_size: size };
    }
    """
    return page.evaluate(js)


VALUE_RE = re.compile(r"([\d,]+\.?\d*)\s*([KMB]?)", re.IGNORECASE)
DATE_RE  = re.compile(r"(\d{1,2}/\d{1,2}/\d{2,4})")


def parse_value(s: str) -> float | None:
    """Parse '907.603644K' -> 907603.644 ; '1.2M' -> 1200000."""
    m = VALUE_RE.search(s or "")
    if not m:
        return None
    try:
        v = float(m.group(1).replace(",", ""))
        unit = (m.group(2) or "").upper()
        mult = {"K": 1_000, "M": 1_000_000, "B": 1_000_000_000, "": 1}[unit]
        return v * mult
    except Exception:
        return None


def hover_and_read(page: Page, x: float, y: float, dwell_ms: int = 900,
                   svg_selector_hint: str | None = None) -> str:
    """Hover at (x,y), wait for tooltip, return tooltip text.
    Uses both mouse.move AND JS dispatchEvent(mousemove) for React-based charts.
    Scrolls chart into view first.
    """
    try:
        # Scroll chart region into view
        page.evaluate(
            """(pt) => window.scrollTo({ top: window.scrollY + pt.y - window.innerHeight/2, behavior: 'instant' })""",
            {"x": x, "y": y},
        )
        time.sleep(0.3)
    except Exception:
        pass
    # Recompute screen coords after scroll (viewport-relative)
    y_view = None
    try:
        y_view = page.evaluate("(pt) => pt.y - window.scrollY + document.documentElement.getBoundingClientRect().top", {"y": y})
    except Exception:
        pass
    # Actually simplest: chart data-point x/y from find_chart_info already used getBoundingClientRect
    # which is viewport-relative. After scroll, that value stales. Re-fetch chart info would be needed,
    # so we use a different tactic: dispatch mousemove at document coords via JS.
    try:
        page.mouse.move(5, 5)
        time.sleep(0.15)
        page.mouse.move(x, y, steps=5)
        # Additionally dispatch synthetic MouseEvent to elementFromPoint
        page.evaluate(r"""
            (pt) => {
                const el = document.elementFromPoint(pt.x, pt.y);
                if (!el) return null;
                for (const type of ['mouseover','mouseenter','mousemove']) {
                    el.dispatchEvent(new MouseEvent(type, {
                        bubbles: true, cancelable: true,
                        clientX: pt.x, clientY: pt.y, view: window,
                    }));
                }
                return el.tagName + '.' + (el.className || '').toString().slice(0, 40);
            }
        """, {"x": x, "y": y})
        time.sleep(dwell_ms / 1000)
    except Exception as e:
        log(f"  hover err: {e}")
    return read_tooltip_text(page, near_x=x, near_y=y)


def main() -> int:
    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp("http://localhost:9222")
        except Exception as e:
            log(f"CDP connect failed: {e}")
            return 1
        # Prefer a tab that looks like a customer detail page (has 'customers/ch:'
        # or 'workload:' in URL). Fall back to the first cxp.azure.com tab.
        ctx = browser.contexts[0]
        page = None
        # First pass: customer detail / workload page
        for pg in ctx.pages:
            u = pg.url or ""
            if "cxp.azure.com" in u and ("customers/ch:" in u or "workload:" in u):
                page = pg
                break
        if page is None:
            for pg in ctx.pages:
                if "cxp.azure.com" in (pg.url or ""):
                    page = pg
                    break
        if page is None:
            log("No cxp.azure.com tab found. Open a workload Consumption page first.")
            return 2
        page.bring_to_front()
        log(f"URL: {page.url[:180]}")

        # 1. Static header text
        header = read_chart_header(page)
        log(f"headline: {header.get('headline')!r}")
        log(f"delta:    {header.get('delta')!r}")

        # 2. Find chart and data points
        info = find_chart_info(page)
        charts = info.get("charts", [])
        log(f"found {len(charts)} candidate chart(s) (iframes={info.get('iframes')})")
        for i, ch in enumerate(charts):
            log(f"  [{i}] doc={ch['doc_idx']} svg #{ch['idx']} {ch['width']}x{ch['height']} "
                f"@({ch['x']},{ch['y']}) pts={ch['points_count']} kind={ch['kind']} "
                f"ctx={ch['ctx_snippet'][:80]!r}")

        # Diagnostics: dump all svg / canvas elements (even small ones) if no chart found
        if not charts:
            diag = page.evaluate(r"""
            () => {
                const out = { svgs: [], canvases: [], shadowRoots: 0 };
                function walk(root) {
                    for (const el of root.querySelectorAll('*')) {
                        if (el.shadowRoot) { out.shadowRoots++; walk(el.shadowRoot); }
                    }
                    for (const s of root.querySelectorAll('svg')) {
                        const r = s.getBoundingClientRect();
                        out.svgs.push({ w: Math.round(r.width), h: Math.round(r.height),
                                        circles: s.querySelectorAll('circle').length,
                                        paths: s.querySelectorAll('path').length,
                                        cls: (s.getAttribute('class')||'').slice(0,60) });
                    }
                    for (const c of root.querySelectorAll('canvas')) {
                        const r = c.getBoundingClientRect();
                        out.canvases.push({ w: Math.round(r.width), h: Math.round(r.height),
                                            cls: (c.getAttribute('class')||'').slice(0,60),
                                            id: (c.id||'').slice(0,60) });
                    }
                }
                walk(document);
                return out;
            }
            """)
            log(f"DIAG: svgs={len(diag['svgs'])}, canvases={len(diag['canvases'])}, shadowRoots={diag['shadowRoots']}")
            for s in diag['svgs'][:30]:
                log(f"  svg {s['w']}x{s['h']} c={s['circles']} p={s['paths']} cls={s['cls']!r}")
            for c in diag['canvases'][:30]:
                log(f"  canvas {c['w']}x{c['h']} id={c['id']!r} cls={c['cls']!r}")

        # Pick the first chart whose ctx mentions "Azure Consumption Units"
        target = None
        for ch in charts:
            if "Azure Consumption Units" in (ch.get("ctx_snippet") or ""):
                target = ch
                break
        if target is None and charts:
            target = charts[0]
        if target is None:
            log("No chart found — is the page on Consumption details?")
            return 3

        pts = target["points"]
        log(f"target chart has {len(pts)} data points")
        # Hover over last 2 points
        for i, pt in enumerate(pts[-3:], start=len(pts) - 3):
            log(f"\n--- hover point idx={i} at ({pt['x']:.0f},{pt['y']:.0f}) ---")
            txt = hover_and_read(page, pt["x"], pt["y"], dwell_ms=1100)
            log(f"tooltip text ({len(txt)} chars):\n{txt}")
            m_val = VALUE_RE.search(txt or "")
            m_date = DATE_RE.search(txt or "")
            log(f"parsed date={m_date.group(1) if m_date else None} "
                f"value_raw={m_val.group(0) if m_val else None} "
                f"value_units={parse_value(txt) if m_val else None}")
        # Move mouse away
        try:
            page.mouse.move(5, 5)
        except Exception:
            pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
