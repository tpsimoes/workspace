"""
CX Observe semi-auto screenshot capture — for the 22 FOCUS customer TPIDs,
navigate via Home → search → click TPID, take screenshots of the customer
summary panel (Consumption tile visible), then click Related workloads View
and take a screenshot of the workload picker.

Output structure (per TPID):
  Skills/asw_caas_lead/references/acr_capture_2026-07/
    <TPID>_<customer>/
      01_summary.png       — customer summary panel with Consumption tile
      02_workloads.png     — workload picker (if applicable)
      03_workload_page.png — after selecting workload (best-effort)
  acr_capture_input.csv   — CSV template for user to fill values

Prereqs: Edge on CDP:9222, signed in to cxp.azure.com.
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
# Customer list — (tpid, safe_name, workload_hint, notes)
# Extracted from generate_dashboard_v1.py FOCUS list; only entries with TPIDs.
# workload_hint = what to look for in Related workloads picker column "Customer"
# ---------------------------------------------------------------------------
CUSTOMERS: list[tuple[str, str, str, str]] = [
    # ── Section 2: SAP RISE (MC / MC Pipeline) ──────────────────────────────
    ("603819",   "SAP_SE_RISE1",           "org-level",              "SAP RISE tenant 1 — capture LANDING page Consumption (org-level, exception)"),
    ("15902931", "SAP_RISE2",              "RISE workload",          "SAP RISE tenant 2 — try workload picker; if none, capture landing"),
    ("2699441",  "SAP_RISE3",              "RISE workload",          "SAP RISE tenant 3 — try workload picker; if none, capture landing"),
    ("636846",   "PepsiCo",                "SAP or HANA",            "workload-scoped"),
    ("1719071",  "Woolworths",             "SAP or HANA",            "workload-scoped"),
    ("682354",   "Medline",                "SAP or HANA",            "workload-scoped"),
    ("10545209", "Shell",                  "Shell plc - SAP S/4 CFIN", "workload-scoped (specific workload name)"),
    ("523595",   "Ferrero",                "SAP or HANA",            "workload-scoped"),
    ("605015",   "Lego",                   "SAP or HANA",            "workload-scoped"),
    ("1248703",  "Beiersdorf",             "SAP or HANA",            "workload-scoped"),
    # ── Section 3: SAP Native / Epic Potential MC ──────────────────────────
    ("640443",   "Nike",                   "SAP or HANA",            "workload-scoped"),
    ("520706",   "Bayer_AG",               "SAP or HANA",            "workload-scoped"),
    ("523272",   "BHP",                    "SAP or HANA",            "workload-scoped"),
    ("101552",   "Unilever",               "SAP or HANA",            "workload-scoped"),
    ("645076",   "McKesson",               "SAP or HANA",            "workload-scoped"),
    ("643195",   "Halliburton",            "SAP or HANA",            "workload-scoped"),
    ("940486",   "Petrobras",              "SAP or HANA",            "workload-scoped"),
    ("1283152",  "Mt_Sinai",               "Epic",                   "workload-scoped (EPIC)"),
    ("639155",   "Walgreens",              "SAP or HANA",            "workload-scoped"),
    # ── Section 4: EPIC Mission Critical ────────────────────────────────────
    ("18982817", "TJU",                    "Epic",                   "workload-scoped (EPIC)"),
    ("1833997",  "MichMed",                "Epic",                   "workload-scoped (EPIC)"),
    ("3841220",  "Ascension_Health",       "Epic",                   "workload-scoped (EPIC)"),
]


def log(msg: str) -> None:
    print(f"[capture] {msg}", flush=True)


def safe_screenshot(page: Page, path: Path, label: str = "") -> bool:
    """Take a viewport screenshot with tolerant timeout and animations disabled."""
    try:
        page.screenshot(path=str(path), timeout=20000, animations="disabled", full_page=False)
        log(f"  saved {label}: {path.name}")
        return True
    except Exception as e:
        log(f"  screenshot fail ({label}): {type(e).__name__}: {str(e)[:80]}")
        return False


def wait_networkidle(page: Page, timeout: int = 30000) -> None:
    try:
        page.wait_for_load_state("networkidle", timeout=timeout)
    except Exception:
        pass


def do_home_and_search(page: Page, tpid: str) -> bool:
    """Navigate home, type TPID, press Enter, wait for allcustomers."""
    page.goto("https://cxp.azure.com/cxobserve/home", wait_until="domcontentloaded", timeout=45000)
    time.sleep(3)
    try:
        search = page.locator("input[placeholder*='Search' i]").first
        search.wait_for(state="visible", timeout=15000)
        search.click()
        search.fill("")
        search.type(tpid, delay=80)
        time.sleep(1.5)
        search.press("Enter")
    except Exception as e:
        log(f"  search-box interaction failed: {e}")
        return False
    try:
        page.wait_for_url("**allcustomers**", timeout=20000)
    except Exception:
        pass
    wait_networkidle(page, 30000)

    # wait for the TPID text to appear in results
    for _ in range(15):
        body = page.evaluate("() => document.body.innerText || ''")
        if tpid in body:
            time.sleep(2)
            return True
        time.sleep(1)
    log(f"  TPID {tpid} did not appear in results within 15s")
    return False


def click_tpid_link(page: Page, tpid: str) -> bool:
    """Click the TPID link in search results to open the customer summary panel."""
    # ensure results are actually loaded — search for grid rows with TPID
    for attempt in range(6):
        try:
            row_ct = page.evaluate(
                "(tpid) => Array.from(document.querySelectorAll('a,button,[role=\"link\"],[role=\"cell\"],td,span')).filter(e => (e.innerText||'').trim() === tpid).length",
                tpid,
            )
        except Exception:
            row_ct = 0
        if row_ct:
            log(f"  found {row_ct} exact-match nodes for '{tpid}' at attempt {attempt+1}")
            break
        time.sleep(2)
    else:
        log(f"  no exact-match nodes for '{tpid}' after 12s wait")

    link = None
    # Prefer exact-text match (avoid matching substrings)
    for sel in [
        f"a:text-is('{tpid}')",
        f"[role='link']:has-text('{tpid}')",
        f"a:has-text('{tpid}')",
        f"button:has-text('{tpid}')",
    ]:
        try:
            cand = page.locator(sel).first
            cand.wait_for(state="visible", timeout=5000)
            link = cand
            log(f"  matched via {sel!r}")
            break
        except Exception:
            continue

    if not link:
        # last-resort: any node whose exact innerText is the TPID
        try:
            handle = page.evaluate_handle(
                "(tpid) => Array.from(document.querySelectorAll('a,button,[role=\"link\"],span,td'))"
                ".find(e => (e.innerText||'').trim() === tpid && e.getBoundingClientRect().width > 0)",
                tpid,
            )
            el = handle.as_element()
            if el:
                log("  matched via evaluate_handle fallback")
                el.scroll_into_view_if_needed(timeout=5000)
                el.click(timeout=5000)
                time.sleep(3)
                wait_networkidle(page, 25000)
                time.sleep(2)
                return True
        except Exception as e:
            log(f"  evaluate_handle fallback failed: {e}")
        log(f"  no clickable element found for TPID {tpid}")
        return False

    try:
        link.scroll_into_view_if_needed(timeout=5000)
        link.click(timeout=8000)
        time.sleep(3)
        wait_networkidle(page, 25000)
        time.sleep(2)
        return True
    except Exception as e:
        log(f"  click TPID link failed: {e}")
        return False


def scroll_summary_panel(page: Page) -> None:
    """Scroll the customer summary panel to reveal all tiles (Consumption may be lower)."""
    try:
        page.evaluate("""() => {
            const scroll_all = () => {
                for (const el of document.querySelectorAll('*')) {
                    if (el.scrollHeight > el.clientHeight && el.clientHeight > 100) {
                        el.scrollTop = 0;
                    }
                }
            };
            scroll_all();
        }""")
    except Exception:
        pass


def process_customer(page: Page, tpid: str, safe_name: str, notes: str) -> dict:
    """Full flow for one customer. Returns a status dict."""
    log(f"===== {tpid} / {safe_name} =====")
    result = {"tpid": tpid, "customer": safe_name, "notes": notes,
              "summary_ok": False, "workload_picker_ok": False, "workload_page_ok": False,
              "workload_names": []}

    cust_dir = OUT_ROOT / f"{tpid}_{safe_name}"
    cust_dir.mkdir(parents=True, exist_ok=True)

    if not do_home_and_search(page, tpid):
        return result

    if not click_tpid_link(page, tpid):
        return result

    # scroll panel to top, screenshot summary
    scroll_summary_panel(page)
    time.sleep(2)
    result["summary_ok"] = safe_screenshot(page, cust_dir / "01_summary.png", "summary")

    # For TPID 603819 — org-level exception, we stop here (landing IS the source)
    if tpid == "603819":
        log("  TPID 603819 → org-level exception; skipping workload picker")
        return result

    # Try to open Related workloads picker
    log("  looking for Related workloads View button")
    # Strategy: find text 'Related workloads' → walk up to card → find button 'View'
    view_btn = None
    try:
        # get all Related workloads text nodes, pick the visible one with a nearby View button
        rw_nodes = page.locator("text=Related workloads").all()
        for rw in rw_nodes:
            try:
                bb = rw.bounding_box()
                if not bb or bb["width"] == 0:
                    continue
                # find nearest ancestor that contains a View button
                view_in_card = rw.locator("xpath=ancestor::*[.//button[contains(., 'View')]][1]//button[contains(., 'View')]").first
                view_in_card.wait_for(state="visible", timeout=3000)
                view_btn = view_in_card
                break
            except Exception:
                continue
        if not view_btn:
            # fallback: pick the button whose ancestor contains 'Related workloads'
            candidates = page.locator("button:has-text('View')").all()
            for c in candidates:
                try:
                    parent_txt = c.evaluate("el => (el.closest('div,section,article,li') || el.parentElement)?.innerText || ''")
                    if "Related workloads" in parent_txt or "Related Workloads" in parent_txt:
                        view_btn = c
                        break
                except Exception:
                    continue
    except Exception as e:
        log(f"  View button search error: {e}")

    if not view_btn:
        log("  Related workloads View button not found; skipping picker")
        # still try workload_page screenshot as fallback (probably empty)
        return result

    try:
        view_btn.click()
        time.sleep(3)
        wait_networkidle(page, 20000)
        time.sleep(2)
    except Exception as e:
        log(f"  click View failed: {e}")
        return result

    # capture workload picker
    result["workload_picker_ok"] = safe_screenshot(page, cust_dir / "02_workloads.png", "workload_picker")

    # try to extract workload row names for user reference
    try:
        rows_text = page.evaluate("""() => {
            const out = [];
            const rows = document.querySelectorAll('[role="row"]');
            for (const r of rows) {
                const t = (r.innerText || '').trim();
                if (t) out.push(t.split('\\n').slice(0, 3).join(' | '));
            }
            return out.slice(0, 40);
        }""")
        result["workload_names"] = rows_text
        (cust_dir / "workload_rows.txt").write_text("\n".join(rows_text), encoding="utf-8")
        log(f"  workload row count: {len(rows_text)}")
    except Exception as e:
        log(f"  workload row read err: {e}")

    return result


def main() -> int:
    log(f"output dir: {OUT_ROOT}")

    results: list[dict] = []

    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp("http://localhost:9222")
        except Exception as e:
            log(f"CDP connect failed: {e}")
            return 1

        ctx = browser.contexts[0]
        # find or create cxobserve tab
        target = None
        for pg in ctx.pages:
            if "cxp.azure.com" in pg.url:
                target = pg
                break
        if not target:
            target = ctx.new_page()

        target.set_default_timeout(30000)

        # Optional: process one TPID at a time; if user wants to stop midway, they Ctrl+C
        arg_start = 0
        arg_limit = len(CUSTOMERS)
        if len(sys.argv) >= 2:
            arg_start = int(sys.argv[1])
        if len(sys.argv) >= 3:
            arg_limit = int(sys.argv[2])
        subset = CUSTOMERS[arg_start:arg_start + arg_limit]
        log(f"processing {len(subset)} customers (start={arg_start})")

        for tpid, safe_name, wl_hint, notes in subset:
            try:
                r = process_customer(target, tpid, safe_name, notes)
                r["workload_hint"] = wl_hint
                results.append(r)
            except Exception as e:
                log(f"  ! unexpected error for {tpid}: {e}")
                results.append({"tpid": tpid, "customer": safe_name, "error": str(e), "workload_hint": wl_hint, "notes": notes})

    # Write CSV template
    with CSV_PATH.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "tpid", "customer", "workload_hint",
            "screenshot_summary", "screenshot_workload_picker",
            "scope", "chosen_workload_name",
            "cur_month_usd_M", "prev_month_usd_M",
            "notes",
        ])
        for r in results:
            cust_dir_name = f"{r['tpid']}_{r['customer']}"
            summary_p = f"{cust_dir_name}/01_summary.png" if r.get("summary_ok") else ""
            workload_p = f"{cust_dir_name}/02_workloads.png" if r.get("workload_picker_ok") else ""
            scope = "org-level" if r["tpid"] == "603819" else "workload"
            w.writerow([
                r["tpid"], r["customer"], r.get("workload_hint", ""),
                summary_p, workload_p,
                scope, "",
                "", "",
                r.get("notes", ""),
            ])
    log(f"CSV template: {CSV_PATH}")
    log("done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
