"""
CX Observe semi-auto capture v2 — correct navigation using per-row buttons.

Flow (per customer):
  1. Navigate Home, search TPID, wait for the customer row to render.
  2. If TPID == 603819 (org-level exception):
       - Click the customer-name link (not the TPID number, which is target=_blank).
       - Wait for URL `/tpid:{tpid}/summary`. Screenshot 01_summary.png.
  3. Otherwise (workload-scoped):
       - Click the row's 'Related workloads View' button (aria-label match).
       - Wait for URL change / workload-picker render. Screenshot 02_workloads.png.
       - Enumerate workload rows for SAP / HANA / Epic name matches (case-insensitive).
       - If matched: click that row, wait for `/workload:` URL and Consumption tile,
         screenshot 03_workload_summary.png. Also record chosen workload name.
       - If NO SAP/HANA/Epic row: skip click, mark `chosen_workload=None`, ACR stays N/A.

Prereqs: External Edge on CDP:9222 signed into cxp.azure.com.
"""

from __future__ import annotations

import csv
import re
import sys
import time
from pathlib import Path

from playwright.sync_api import Page, sync_playwright  # type: ignore

OUT_ROOT = Path(__file__).parent.parent / "references" / "acr_capture_2026-07"
OUT_ROOT.mkdir(parents=True, exist_ok=True)
CSV_PATH = OUT_ROOT / "acr_capture_input.csv"

# ---------------------------------------------------------------------------
# Customer list — (tpid, safe_name, display_name_in_row, workload_hint)
# display_name_in_row = text to match in the row 'Customer' column (partial ok)
# workload_hint       = FOCUS `workload` field, drives SAP/HANA/Epic matching
# ---------------------------------------------------------------------------
CUSTOMERS: list[tuple[str, str, str, str]] = [
    # Section 2: SAP RISE / MC
    ("603819",   "SAP_SE_RISE1",     "SAP",             "RISE"),
    ("15902931", "SAP_RISE2",        "SAP",             "RISE"),
    ("2699441",  "SAP_RISE3",        "SAP",             "RISE"),
    ("636846",   "PepsiCo",          "PepsiCo",         "SAP"),
    ("1719071",  "Woolworths",       "Woolworths",      "SAP"),
    ("682354",   "Medline",          "Medline",         "SAP"),
    ("10545209", "Shell",            "Shell",           "SAP"),
    ("523595",   "Ferrero",          "Ferrero",         "SAP"),
    ("605015",   "Lego",             "LEGO",            "SAP"),
    ("1248703",  "Beiersdorf",       "Beiersdorf",      "SAP"),
    # Section 3
    ("640443",   "Nike",             "Nike",            "SAP"),
    ("520706",   "Bayer_AG",         "Bayer",           "SAP"),
    ("523272",   "BHP",              "BHP",             "SAP"),
    ("101552",   "Unilever",         "Unilever",        "SAP"),
    ("645076",   "McKesson",         "McKesson",        "SAP"),
    ("643195",   "Halliburton",      "Halliburton",     "SAP"),
    ("940486",   "Petrobras",        "Petrobras",       "SAP"),
    ("1283152",  "Mt_Sinai",         "Mount Sinai",     "EPIC"),
    ("639155",   "Walgreens",        "Walgreens",       "SAP"),
    # Section 4: EPIC
    ("18982817", "TJU",              "Thomas Jefferson","EPIC"),
    ("1833997",  "MichMed",          "University of Michigan","EPIC"),
    ("3841220",  "Ascension_Health", "Ascension",       "EPIC"),
]

# ---------------------------------------------------------------------------
# workload name matching — strict word-boundary, per workload_hint
# We match tokens against the FIRST DATA CELL (workload name), not the whole row,
# to avoid false positives like "erp" matching "Enterprise".
# ---------------------------------------------------------------------------
import re as _re

_SAP_PATTERN  = _re.compile(r"(?<![a-zA-Z0-9])(sap|hana|s/?4hana|s/?4|netweaver|bw)(?![a-zA-Z0-9])", _re.IGNORECASE)
_EPIC_PATTERN = _re.compile(r"(?<![a-zA-Z0-9])(epic)(?![a-zA-Z0-9])", _re.IGNORECASE)


def match_workload_name(workload_hint: str, workload_name: str) -> bool:
    if not workload_name:
        return False
    if workload_hint == "EPIC":
        return bool(_EPIC_PATTERN.search(workload_name))
    return bool(_SAP_PATTERN.search(workload_name))


# ---------------------------------------------------------------------------
def log(msg: str) -> None:
    print(f"[cap2] {msg}", flush=True)


_CDP_SESSIONS: dict[int, object] = {}


def _cdp(page: Page):
    key = id(page)
    if key not in _CDP_SESSIONS:
        _CDP_SESSIONS[key] = page.context.new_cdp_session(page)
    return _CDP_SESSIONS[key]


def safe_screenshot(page: Page, path: Path, label: str = "", clip_right_panel: bool = True) -> bool:
    # Primary path: CDP Page.captureScreenshot — bypasses Playwright's font wait
    try:
        import base64
        sess = _cdp(page)
        params: dict = {"format": "png", "captureBeyondViewport": False}
        if clip_right_panel:
            # Get viewport size and clip to left portion (exclude AI Assistant panel if open)
            try:
                dims = page.evaluate("() => ({w: window.innerWidth, h: window.innerHeight, dpr: window.devicePixelRatio})")
                ai_open = page.evaluate("() => {"
                                        "const el = document.querySelector('button[aria-label=\"Close\"]');"
                                        "if (!el) return false;"
                                        "const r = el.getBoundingClientRect();"
                                        "return (r.x > window.innerWidth * 0.6 && r.y < 200 && r.width > 0);"
                                        "}")
                w = int(dims["w"])
                h = int(dims["h"])
                if ai_open:
                    # AI panel typically occupies right ~30%; clip to left 68%
                    params["clip"] = {"x": 0, "y": 0, "width": int(w * 0.68), "height": h, "scale": 1}
                else:
                    params["clip"] = {"x": 0, "y": 0, "width": w, "height": h, "scale": 1}
            except Exception:
                pass
        res = sess.send("Page.captureScreenshot", params)
        data = base64.b64decode(res["data"])
        path.write_bytes(data)
        log(f"  {label}: {path.name} (cdp)")
        return True
    except Exception as e:
        log(f"  cdp screenshot fail ({label}): {type(e).__name__}: {str(e)[:80]}")
    # Fallback: Playwright screenshot
    try:
        page.screenshot(path=str(path), timeout=60000, animations="disabled", full_page=False)
        log(f"  {label}: {path.name} (pw)")
        return True
    except Exception as e:
        log(f"  screenshot fail ({label}): {type(e).__name__}: {str(e)[:80]}")
        return False


def do_home_and_search(page: Page, tpid: str) -> bool:
    page.goto("https://cxp.azure.com/cxobserve/home", wait_until="domcontentloaded", timeout=60000)
    time.sleep(3)
    try:
        sb = page.locator("input[placeholder*='Search' i]").first
        sb.wait_for(state="visible", timeout=15000)
        sb.click(); sb.fill(""); sb.type(tpid, delay=80); time.sleep(1.5); sb.press("Enter")
    except Exception as e:
        log(f"  search interaction failed: {e}")
        return False
    try:
        page.wait_for_url("**allcustomers**", timeout=20000)
    except Exception:
        pass
    try:
        page.wait_for_load_state("networkidle", timeout=30000)
    except Exception:
        pass
    # wait for the row grid to have this TPID (up to 60s — 'Loading...' can be slow)
    for i in range(60):
        try:
            ct = page.evaluate(
                "(t) => Array.from(document.querySelectorAll('[role=\"row\"]'))"
                ".filter(r => (r.innerText||'').includes(t)).length",
                tpid,
            )
        except Exception:
            ct = 0
        if ct:
            time.sleep(2)
            return True
        time.sleep(1)
    log(f"  TPID {tpid} row did not render within 60s")
    return False


def find_target_row(page: Page, tpid: str, display_hint: str):
    """Return the first row locator containing both the TPID text AND the display name hint."""
    rows = page.locator(f"[role='row']:has-text('{tpid}')").all()
    for r in rows:
        try:
            txt = r.inner_text() or ""
        except Exception:
            continue
        if display_hint.lower() in txt.lower():
            return r
    if rows:
        return rows[0]
    return None


def click_customer_name(page: Page, row) -> bool:
    """Click the customer name link in the row (opens /summary in same tab)."""
    try:
        # Prefer the anchor with text = customer name (not TPID)
        anchors = row.locator("a[aria-label^='Link to detail for']").all()
        for a in anchors:
            try:
                target = a.get_attribute("target")
                if target == "_blank":
                    continue
                a.scroll_into_view_if_needed(timeout=5000)
                a.click(timeout=8000)
                return True
            except Exception:
                continue
    except Exception as e:
        log(f"  customer-name click err: {e}")
    return False


def click_related_workloads_view(page: Page, row) -> bool:
    """Click the 'Related workloads View' button inside the row."""
    try:
        btn = row.locator("button[aria-label='Related workloads View']").first
        btn.wait_for(state="visible", timeout=6000)
        btn.scroll_into_view_if_needed(timeout=5000)
        btn.click(timeout=8000)
        return True
    except Exception as e:
        log(f"  related-workloads-view click err: {e}")
        return False


def wait_url_contains(page: Page, needle: str, timeout: int = 25000) -> bool:
    end = time.time() + timeout / 1000.0
    while time.time() < end:
        if needle in page.url:
            return True
        time.sleep(0.5)
    return False


def enumerate_workload_rows(page: Page) -> list[dict]:
    """Enumerate ONLY the 'Related workloads' picker rows.

    Structure: role=row entries appear in two sections on the page:
      (a) the outer search-results grid (rows 0..N of customers)
      (b) the workload picker modal (with its own header row: 'Customer | Workload Type | ...')

    We identify the picker header row (contains 'Workload Type' in cell 2) and only
    return rows AFTER it.
    """
    try:
        for _ in range(15):
            ct = page.evaluate("() => document.querySelectorAll('[role=\"row\"]').length")
            if ct and ct > 3:
                break
            time.sleep(1)
        rows = page.evaluate("""() => {
            const out = [];
            const rs = Array.from(document.querySelectorAll('[role="row"]'));
            let header_idx = -1;
            for (let i = 0; i < rs.length; i++) {
                const r = rs[i];
                const cells = Array.from(r.querySelectorAll('[role="cell"], [role="gridcell"]'));
                const cellTexts = cells.map(c => (c.innerText || '').trim());
                const full = (r.innerText || '').trim();
                if (header_idx === -1 && /Workload Type/.test(full)) {
                    header_idx = i;
                }
                out.push({idx: i, header_idx_ref: header_idx, full: full, cells: cellTexts});
            }
            const picker_start = header_idx >= 0 ? header_idx + 1 : -1;
            return out.map(x => ({...x, is_picker_row: picker_start >= 0 && x.idx >= picker_start}));
        }""")
        return rows or []
    except Exception as e:
        log(f"  enumerate rows err: {e}")
        return []


def click_workload_row(page: Page, row_idx: int) -> bool:
    """Click a specific workload picker row by its role=row index."""
    try:
        clicked = page.evaluate("""(idx) => {
            const rs = Array.from(document.querySelectorAll('[role="row"]'));
            if (idx >= rs.length) return null;
            const r = rs[idx];
            // find the primary clickable inside (workload name link)
            const link = r.querySelector('a, button, [role="link"]');
            if (link) { link.click(); return 'link'; }
            r.click(); return 'row';
        }""", row_idx)
        if not clicked:
            return False
        return True
    except Exception as e:
        log(f"  click workload row err: {e}")
        return False


def close_ai_assistant(page: Page) -> None:
    """Close the CX Observe AI Assistant right-side panel if it is open.

    The panel has a header 'AI Assistant PREVIEW' with a close button whose
    aria-label is 'Close'. To disambiguate from other 'Close' buttons on the
    page, we filter by X position (right side of viewport).
    """
    try:
        clicked = page.evaluate("""() => {
            for (const b of document.querySelectorAll('button[aria-label="Close"]')) {
                const r = b.getBoundingClientRect();
                if (r.x > window.innerWidth * 0.6 && r.y < 200) { // right side, near top
                    b.click();
                    return {x: r.x, y: r.y};
                }
            }
            return null;
        }""")
        if clicked:
            log(f"  AI panel closed @({clicked['x']}, {clicked['y']})")
            time.sleep(1.5)
        else:
            # try clicking the toggle in top-nav (works as toggle)
            page.evaluate("""() => {
                for (const b of document.querySelectorAll('button[aria-label="AI Assistant"]')) {
                    b.click(); return true;
                }
                return false;
            }""")
            time.sleep(1.5)
    except Exception as e:
        log(f"  close AI panel err: {e}")


def _click_sub_nav(page: Page, sub_label: str, parent_label: str = "Consumption") -> bool:
    """Robustly click a left-nav sub-item.

    Strategy:
      1. Wait for the left nav to actually render (Consumption parent must be findable).
      2. If sub-item link is already in DOM → click.
      3. Otherwise, click parent to expand → wait → click sub-item.
    """
    # (1) wait for sidebar to render the parent
    for _ in range(15):
        ready = page.evaluate("""(label) => {
            const norm = s => (s||'').replace(/[\\ue000-\\uf8ff]/g, '').replace(/\\s+/g,' ').trim();
            for (const el of document.querySelectorAll('button, a, [role="button"], [role="treeitem"]')) {
                if (norm(el.innerText) === label) {
                    const r = el.getBoundingClientRect();
                    if (r.width > 0 && r.height > 0) return true;
                }
            }
            return false;
        }""", parent_label)
        if ready:
            break
        time.sleep(1)
    def find_and_click():
        return page.evaluate("""(label) => {
            const norm = s => (s||'').replace(/[\\ue000-\\uf8ff]/g, '').replace(/\\s+/g,' ').trim();
            const els = Array.from(document.querySelectorAll('a, button')).filter(e => norm(e.innerText) === label);
            for (const e of els) {
                const r = e.getBoundingClientRect();
                if (r.width > 0 && r.height > 0) { e.click(); return {clicked: true, x: r.x, y: r.y}; }
            }
            return {clicked: false};
        }""", sub_label)

    try:
        r1 = find_and_click()
        if r1["clicked"]:
            log(f"  clicked '{sub_label}' directly")
            time.sleep(6)
            return True
        # Expand parent
        expanded = page.evaluate("""(label) => {
            const norm = s => (s||'').replace(/[\\ue000-\\uf8ff]/g, '').replace(/\\s+/g,' ').trim();
            const els = Array.from(document.querySelectorAll('button, a')).filter(e => norm(e.innerText) === label);
            for (const e of els) {
                const r = e.getBoundingClientRect();
                if (r.width > 0 && r.height > 0) { e.click(); return {clicked: true}; }
            }
            return {clicked: false};
        }""", parent_label)
        if not expanded["clicked"]:
            log(f"  parent '{parent_label}' not found")
            return False
        time.sleep(1.5)
        r2 = find_and_click()
        if r2["clicked"]:
            log(f"  clicked '{sub_label}' after expanding parent")
            time.sleep(6)
            return True
        log(f"  '{sub_label}' still not found after expanding")
        return False
    except Exception as e:
        log(f"  _click_sub_nav('{sub_label}') err: {e}")
        return False


def open_consumption_details(page: Page) -> bool:
    return _click_sub_nav(page, "Consumption details", "Consumption")


def open_revenue_details(page: Page) -> bool:
    return _click_sub_nav(page, "Revenue details", "Consumption")


def wait_body_has(page: Page, tokens: list[str], timeout: int = 25) -> None:
    for _ in range(timeout):
        try:
            body = page.evaluate("() => document.body.innerText || ''")
        except Exception:
            body = ""
        if any(t in body for t in tokens):
            return
        time.sleep(1)


def process_customer(page: Page, tpid: str, safe_name: str, display_hint: str, workload_hint: str) -> dict:
    log(f"===== {tpid} / {safe_name} (hint={workload_hint}) =====")
    cust_dir = OUT_ROOT / f"{tpid}_{safe_name}"
    cust_dir.mkdir(parents=True, exist_ok=True)

    r = {
        "tpid": tpid, "customer": safe_name, "workload_hint": workload_hint,
        "scope": "org-level" if tpid == "603819" else "workload",
        "acu_ok": False, "usd_ok": False,
        "workload_picker_ok": False, "workload_acu_ok": False, "workload_usd_ok": False,
        "chosen_workload": None, "workload_names_dump": "",
        "notes": "",
    }

    if not do_home_and_search(page, tpid):
        r["notes"] = "search failed"
        return r

    row = find_target_row(page, tpid, display_hint)
    if not row:
        r["notes"] = "row not found"
        return r

    # Branch A: TPID 603819 → org-level (click customer name → customer detail page)
    if tpid == "603819":
        if not click_customer_name(page, row):
            r["notes"] = "customer-name click failed"
            return r
        if not wait_url_contains(page, f"tpid:{tpid}", timeout=30000):
            r["notes"] = f"customer URL did not appear (current: {page.url})"
            return r
        log(f"  landed: {page.url[:120]}")
        # ACU only (USD Revenue tab is blocked for this account)
        open_consumption_details(page)
        close_ai_assistant(page)
        wait_body_has(page, ["Azure Consumption Units", "Consumption Units"])
        time.sleep(3)
        r["acu_ok"] = safe_screenshot(page, cust_dir / "01a_acu.png", "acu")
        return r

    # Branch B: workload-scoped — click 'Related workloads View' in the row
    if not click_related_workloads_view(page, row):
        r["notes"] = "Related workloads View button not clickable"
        return r
    # picker opens as a modal / detail panel; poll for rows to render (up to 45s).
    # 'Loading...' can take 20-40s for large tenants (BHP, Walgreens).
    picker_rows = []
    rows = []
    poll_deadline = time.time() + 45
    while time.time() < poll_deadline:
        time.sleep(3)
        rows = enumerate_workload_rows(page)
        picker_rows = [x for x in rows if x.get("is_picker_row")]
        if picker_rows:
            break
    r["workload_picker_ok"] = safe_screenshot(page, cust_dir / "02_workloads.png", "workload_picker")
    (cust_dir / "workload_rows.txt").write_text(
        "\n".join(f"[{x['idx']}] picker={x.get('is_picker_row')} | {x['full'][:200]}" for x in rows),
        encoding="utf-8"
    )
    r["workload_names_dump"] = f"workload_rows.txt ({len(picker_rows)} picker rows / {len(rows)} total)"

    # find first picker row whose Customer-column text matches SAP/HANA/S4/Epic.
    # Structure per row.innerText:
    #   line 0: avatar letter ('W' / 'WG')
    #   line 1: Customer column (workload name, e.g. 'Woolworths - SAP S4 HANA Database resources')
    #   line 2: Workload Type (engagement program, e.g. 'Proactive Resilience')
    #   line 3+: #Subscriptions, EOU, Programs boilerplate
    # We match against the Customer column (line 1). Word-boundary regex ensures
    # program tokens ('Proactive Resilience', 'Azure ACE / AED', etc.) never match.
    # Collect ALL matches — some customers (e.g. BHP) have UAT + PROD SAP workloads
    # that must both be captured.
    matches: list[tuple[int, str]] = []  # (row_idx, workload_name)
    for x in picker_rows:
        lines = [ln.strip() for ln in x["full"].splitlines() if ln.strip()]
        name_candidate = ""
        if lines:
            if len(lines[0]) <= 3 and lines[0].isupper() and len(lines) >= 2:
                name_candidate = lines[1]
            else:
                name_candidate = lines[0]
        cells = x.get("cells") or []
        cell_candidates = [c.split("\n", 1)[0].strip() for c in cells if c and c.strip()]
        candidates = [name_candidate] + cell_candidates
        seen = set()
        candidates = [c for c in candidates if c and not (c in seen or seen.add(c))]
        for cand in candidates:
            if match_workload_name(workload_hint, cand):
                matches.append((x["idx"], cand[:120]))
                break  # per-row: only first candidate

    if not matches:
        r["notes"] = f"no {workload_hint}/SAP/Epic workload row found → ACR = N/A"
        log(f"  no matching workload row for hint '{workload_hint}' — leaving as N/A ({len(picker_rows)} rows scanned)")
        return r

    r["chosen_workload"] = "; ".join(n for _, n in matches)
    log(f"  found {len(matches)} matching workload(s): {r['chosen_workload']!r}")

    letters = "abcdefghij"
    captured_any = False
    for i, (m_idx, m_name) in enumerate(matches):
        letter = letters[i]
        log(f"  [{i+1}/{len(matches)}] capturing idx={m_idx} name={m_name!r}")

        # For subsequent matches, reopen the workload picker
        if i > 0:
            if not do_home_and_search(page, tpid):
                log(f"  [{letter}] re-search failed, skipping")
                continue
            row = find_target_row(page, tpid, display_hint)
            if not row:
                log(f"  [{letter}] re-find row failed, skipping")
                continue
            if not click_related_workloads_view(page, row):
                log(f"  [{letter}] re-open picker failed, skipping")
                continue
            # poll for picker rows (same logic as first capture)
            poll_deadline = time.time() + 45
            while time.time() < poll_deadline:
                time.sleep(3)
                rrows = enumerate_workload_rows(page)
                if [xx for xx in rrows if xx.get("is_picker_row")]:
                    break

        if not click_workload_row(page, m_idx):
            log(f"  [{letter}] workload row click failed, skipping")
            continue
        time.sleep(6)
        open_consumption_details(page)
        close_ai_assistant(page)
        wait_body_has(page, ["Azure Consumption Units", "Consumption Units"])
        time.sleep(3)
        ok = safe_screenshot(page, cust_dir / f"03{letter}_workload_acu.png", f"wl_acu[{letter}]")
        captured_any = captured_any or ok

    r["workload_acu_ok"] = captured_any
    return r


def main() -> int:
    log(f"output dir: {OUT_ROOT}")
    results: list[dict] = []

    arg_start = 0
    arg_limit = len(CUSTOMERS)
    if len(sys.argv) >= 2:
        arg_start = int(sys.argv[1])
    if len(sys.argv) >= 3:
        arg_limit = int(sys.argv[2])
    subset = CUSTOMERS[arg_start:arg_start + arg_limit]
    log(f"processing {len(subset)} customers (start={arg_start})")

    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp("http://localhost:9222")
        except Exception as e:
            log(f"CDP connect failed: {e}")
            return 1
        ctx = browser.contexts[0]
        target = None
        for pg in ctx.pages:
            if "cxp.azure.com" in pg.url:
                target = pg
                break
        if not target:
            target = ctx.new_page()
        target.set_default_timeout(30000)

        for tpid, safe_name, disp, wl in subset:
            try:
                results.append(process_customer(target, tpid, safe_name, disp, wl))
            except Exception as e:
                log(f"  ! unexpected error {tpid}: {e}")
                results.append({
                    "tpid": tpid, "customer": safe_name, "workload_hint": wl,
                    "scope": "org-level" if tpid == "603819" else "workload",
                    "error": str(e),
                })

    # append or write CSV
    write_header = not CSV_PATH.exists() or arg_start == 0
    mode = "a" if not write_header else "w"
    with CSV_PATH.open(mode, encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        if write_header:
            w.writerow([
                "tpid", "customer", "workload_hint", "scope",
                "chosen_workload",
                "screenshot_acu", "screenshot_usd",
                "screenshot_workload_picker",
                "screenshot_workload_acu", "screenshot_workload_usd",
                "cur_month_val", "prev_month_val",
                "notes",
            ])
        for r in results:
            d = f"{r['tpid']}_{r['customer']}"
            w.writerow([
                r.get("tpid", ""), r.get("customer", ""), r.get("workload_hint", ""), r.get("scope", ""),
                r.get("chosen_workload") or "",
                f"{d}/01a_acu.png" if r.get("acu_ok") else "",
                f"{d}/01b_usd.png" if r.get("usd_ok") else "",
                f"{d}/02_workloads.png" if r.get("workload_picker_ok") else "",
                f"{d}/03a_workload_acu.png" if r.get("workload_acu_ok") else "",
                f"{d}/03b_workload_usd.png" if r.get("workload_usd_ok") else "",
                "", "",
                r.get("notes") or r.get("error", ""),
            ])
    log(f"CSV: {CSV_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
