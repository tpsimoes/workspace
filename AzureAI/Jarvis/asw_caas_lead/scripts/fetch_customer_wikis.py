"""
fetch_customer_wikis.py — populate customer_wiki_summaries.json from Azure DevOps wiki
=====================================================================================

Reads the 27 FOCUS customer entries in
`Skills/asw_caas_lead/references/customer_wiki_summaries.json`, opens each
customer's Know-Me wiki subpage under the SAP (pageId 1720255) or Epic
(pageId 2849066) parent, extracts up to 5 support-profile highlights + the
last-updated timestamp, and writes the results back into the JSON.

STRICT NO-FABRICATION RULE
--------------------------
This script only captures what is literally on the wiki page.
- If a customer subpage does not exist  →  has_content=false, highlights=[]
- If the page exists but is empty/template  →  has_content=false, highlights=[]
- If the page has <3 substantive bullets  →  has_content=true, highlights=[...] (only real ones)
- Never invent, summarise, or paraphrase beyond what is on the page.

Prerequisites
-------------
1. Start Microsoft Edge with CDP debugging enabled, signed into your MS AAD account:

       Start-Process msedge -ArgumentList "--remote-debugging-port=9222",
           "https://supportability.visualstudio.com/AzureStrategicWorkloads/_wiki/wikis/AzureStrategicWorkloads"

   (Or reuse an existing Edge session — Edge must have been launched with the
   remote-debugging-port flag; a normal Edge instance won't accept CDP attach.)

2. Install Playwright once in the workspace venv:

       & c:/GitHubCopilot/IronMan/.venv/Scripts/python.exe -m pip install playwright
       & c:/GitHubCopilot/IronMan/.venv/Scripts/python.exe -m playwright install chromium

   (We attach to Edge over CDP, so the bundled chromium is only a fallback.)

3. Run:

       & c:/GitHubCopilot/IronMan/.venv/Scripts/python.exe Skills/asw_caas_lead/scripts/fetch_customer_wikis.py

   Options:
     --only <key>       Fetch a single customer (matches by TPID key or customer name substring)
     --refresh          Re-fetch even customers whose has_content is already set
     --dry-run          Do everything except write back to JSON
     --cdp-url <url>    Override CDP endpoint (default http://localhost:9222)

Design
------
- Attaches to running Edge via CDP.
- For each customer entry, navigates directly to the parent SfMC-Customers page.
- Expands the tree/TOC in the left rail and finds a link whose text matches the
  customer's name (with fuzzy fallback — Levenshtein-style prefix/token match).
- Clicks the link, waits for the article body to render, then extracts:
    * The first N=5 bullet points that look substantive (>=15 chars, not template
      placeholders like "TBD", "N/A", "add content here").
    * The "Last edited" timestamp (visible in the wiki header revision info).
- Records the final URL of the loaded page as `wiki_url_guess`.
- Writes results back to JSON incrementally (safe against interrupt).

Extraction heuristics — kept intentionally strict
--------------------------------------------------
Support-profile highlight scoring:
  base=1 for each `<li>` under the main article
  +1 if bullet is under a heading whose text matches any keyword in HL_HEADING_HINTS
  +1 if bullet contains any keyword in HL_KEYWORDS (SLA, migration, escalation, etc.)
  -5 if bullet matches TEMPLATE_STUBS (placeholder text)
Top 5 by score are kept; ties broken by DOM order.

If <3 bullets survive: highlights=[the surviving ones]; has_content set based
on whether *any* body content beyond the H1 exists.
"""

from __future__ import annotations
import argparse
import asyncio
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# ------------------------------------------------------------------- constants
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent  # Skills/asw_caas_lead/
WIKI_JSON = REPO_ROOT / "references" / "customer_wiki_summaries.json"

HL_HEADING_HINTS = (
    "support", "profile", "critical", "sensitivity", "escalation",
    "note", "key", "important", "migration", "upgrade", "sla",
    "workload", "environment", "landscape", "constraint", "risk",
)
HL_KEYWORDS = (
    "sla", "critsit", "critical", "migrat", "upgrad", "escalat",
    "senstiv", "sensitiv", "single point", "outage", "region",
    "s/4", "s4hana", "hana", "ecs", "netweaver", "azure vmware",
    "avs", "epic", "hyper-v", "storage", "network", "vnet",
    "compliance", "sox", "gxp", "gdpr", "hipaa",
    "renew", "expir", "contract", "mission critical",
    "tam", "csa", "csi", "cxp", "poc",
)
TEMPLATE_STUBS = re.compile(
    r"(^|\W)(tbd|n/?a|to be defined|add content here|placeholder|coming soon|todo)(\W|$)",
    re.IGNORECASE,
)
MIN_BULLET_LEN = 15
MAX_BULLET_LEN = 400  # very long bullets are usually mistakes


# ------------------------------------------------------------------- helpers
def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_json() -> dict:
    return json.loads(WIKI_JSON.read_text(encoding="utf-8"))


def save_json(data: dict) -> None:
    WIKI_JSON.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def score_bullet(text: str, heading_text: str) -> int:
    """Score a bullet for likely usefulness as a support-profile highlight."""
    t = text.strip()
    if not (MIN_BULLET_LEN <= len(t) <= MAX_BULLET_LEN):
        return -100
    if TEMPLATE_STUBS.search(t):
        return -100
    score = 1
    h = (heading_text or "").lower()
    if any(k in h for k in HL_HEADING_HINTS):
        score += 1
    tl = t.lower()
    if any(k in tl for k in HL_KEYWORDS):
        score += 1
    return score


# ------------------------------------------------------------------- playwright
async def attach_edge(cdp_url: str):
    from playwright.async_api import async_playwright  # local import
    p = await async_playwright().start()
    browser = await p.chromium.connect_over_cdp(cdp_url)
    # Use the first (default) context — this shares the authenticated Edge session
    ctxs = browser.contexts
    if not ctxs:
        raise RuntimeError("No browser contexts found on CDP endpoint.")
    ctx = ctxs[0]
    return p, browser, ctx


async def find_child_page_link(page, customer_name: str) -> tuple[str | None, str | None]:
    """Under the currently-loaded parent SfMC-Customers page, find the link to
    the child page whose title matches customer_name. Returns (href, matched_title).
    """
    # Expand any collapsed tree nodes (best-effort)
    try:
        toggles = await page.query_selector_all('[aria-expanded="false"]')
        for t in toggles[:20]:  # cap to avoid runaway
            try:
                await t.click(timeout=800)
            except Exception:
                pass
    except Exception:
        pass

    # Gather candidate links from the left navigation tree
    links = await page.evaluate(
        """() => Array.from(document.querySelectorAll('a[href*="pagePath"], a[href*="/_wiki/wikis/"]'))
            .map(a => ({href: a.href, text: (a.textContent||'').trim()}))
            .filter(x => x.text.length > 0)"""
    )
    # Fuzzy match: exact first, then prefix, then any-token contain
    name_l = customer_name.lower()
    # Drop punctuation for comparison
    def norm(s: str) -> str:
        return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()

    n = norm(customer_name)
    tokens = [t for t in n.split() if len(t) >= 3]
    # 1) exact
    for lk in links:
        if norm(lk["text"]) == n:
            return lk["href"], lk["text"]
    # 2) exact-first-token match (helps "Bayer AG" → "Bayer")
    for lk in links:
        if tokens and norm(lk["text"]).startswith(tokens[0]):
            return lk["href"], lk["text"]
    # 3) all tokens present
    for lk in links:
        lt = norm(lk["text"])
        if tokens and all(t in lt for t in tokens):
            return lk["href"], lk["text"]
    return None, None


async def extract_page(page) -> dict:
    """Extract highlights + last-updated from the currently-loaded wiki page."""
    # Wait for main content
    try:
        await page.wait_for_selector('div.wiki-page-content, .repos-wiki-content, article', timeout=8000)
    except Exception:
        pass

    # Collect all <li> along with nearest previous heading text
    items = await page.evaluate(
        """() => {
            const article = document.querySelector('div.wiki-page-content')
                || document.querySelector('.repos-wiki-content')
                || document.querySelector('article')
                || document.body;
            const out = [];
            let curHeading = '';
            const walker = document.createTreeWalker(article, NodeFilter.SHOW_ELEMENT, null);
            let node = walker.currentNode;
            while (node) {
                if (/^H[1-6]$/.test(node.tagName)) {
                    curHeading = (node.textContent||'').trim();
                } else if (node.tagName === 'LI') {
                    const txt = (node.textContent||'').trim().replace(/\\s+/g,' ');
                    if (txt) out.push({heading: curHeading, text: txt});
                }
                node = walker.nextNode();
            }
            return out;
        }"""
    )

    # Score and pick top 5
    scored = [(score_bullet(it["text"], it["heading"]), it["text"]) for it in items]
    scored = [(s, t) for s, t in scored if s > 0]
    # Deduplicate preserving order
    seen = set()
    unique = []
    for s, t in scored:
        if t not in seen:
            seen.add(t)
            unique.append((s, t))
    unique.sort(key=lambda x: -x[0])
    top5 = [t for _, t in unique[:5]]

    # Last-updated: look for revision info
    last_updated = await page.evaluate(
        """() => {
            const cands = Array.from(document.querySelectorAll(
                '.repos-wiki-header-metadata, .wiki-page-metadata, .repos-wiki-header time, time'
            ));
            for (const c of cands) {
                const t = c.getAttribute('datetime') || (c.textContent||'').trim();
                if (t) return t;
            }
            return null;
        }"""
    )

    # Does the page have any body content beyond the H1?
    body_len = await page.evaluate(
        """() => {
            const article = document.querySelector('div.wiki-page-content')
                || document.querySelector('.repos-wiki-content')
                || document.querySelector('article');
            if (!article) return 0;
            return (article.innerText||'').trim().length;
        }"""
    )

    return {
        "highlights": top5,
        "last_updated": last_updated,
        "body_len": body_len,
        "raw_bullet_count": len(items),
    }


async def fetch_one(page, entry: dict, key: str) -> dict:
    """Fetch one customer's wiki summary. Returns updated entry."""
    parent_url = entry["wiki_parent_url"]
    customer = entry["customer"]
    print(f"\n[{key}] {customer}  ({entry['workload']}, parent={entry['wiki_parent']})")

    # 1) Navigate to parent
    try:
        await page.goto(parent_url, wait_until="domcontentloaded", timeout=20000)
        await page.wait_for_timeout(1500)  # let React settle
    except Exception as e:
        print(f"  ! parent navigation failed: {e}")
        entry.update({
            "has_content": False, "highlights": [], "last_updated": None,
            "fetched_at": now_iso(), "notes": f"parent navigation error: {e}",
        })
        return entry

    # 2) Find child link
    href, matched = await find_child_page_link(page, customer)
    if not href:
        print(f"  · no child page link matched")
        entry.update({
            "has_content": False, "highlights": [], "last_updated": None,
            "wiki_url_guess": None, "fetched_at": now_iso(),
            "notes": "no matching child page found under SfMC-Customers parent",
        })
        return entry
    print(f"  → matched link: {matched!r}  →  {href}")

    # 3) Load child
    try:
        await page.goto(href, wait_until="domcontentloaded", timeout=20000)
        await page.wait_for_timeout(1500)
    except Exception as e:
        print(f"  ! child navigation failed: {e}")
        entry.update({
            "has_content": False, "highlights": [], "last_updated": None,
            "wiki_url_guess": href, "fetched_at": now_iso(),
            "notes": f"child navigation error: {e}",
        })
        return entry

    # 4) Extract
    result = await extract_page(page)
    has_body = result["body_len"] > 200  # arbitrary threshold; empty templates are usually smaller

    entry.update({
        "has_content": bool(result["highlights"]) or has_body,
        "highlights": result["highlights"],
        "last_updated": result["last_updated"],
        "wiki_url_guess": href,
        "fetched_at": now_iso(),
        "notes": (
            None
            if result["highlights"]
            else ("empty template" if not has_body else "page exists but no highlight-scoring bullets extracted")
        ),
    })
    print(f"  ✓ body={result['body_len']}ch  bullets_raw={result['raw_bullet_count']}  highlights={len(result['highlights'])}  last_updated={result['last_updated']}")
    return entry


# ------------------------------------------------------------------- main
async def run(args) -> int:
    data = load_json()
    entries = data["by_key"]

    # Filter targets
    keys = list(entries.keys())
    if args.only:
        q = args.only.lower()
        keys = [k for k in keys if q in k.lower() or q in entries[k]["customer"].lower()]
        if not keys:
            print(f"No match for --only {args.only!r}", file=sys.stderr)
            return 2
    if not args.refresh:
        keys = [k for k in keys if entries[k].get("has_content") is None]

    if not keys:
        print("Nothing to do (all customers already fetched; use --refresh to redo).")
        return 0

    print(f"Fetching {len(keys)} customer(s) from Azure DevOps wiki via CDP {args.cdp_url}")

    p, browser, ctx = await attach_edge(args.cdp_url)
    page = await ctx.new_page()
    try:
        for k in keys:
            entries[k] = await fetch_one(page, entries[k], k)
            data["meta"]["last_fetch_run"] = now_iso()
            if not args.dry_run:
                save_json(data)
    finally:
        await page.close()
        # Don't close the browser — we attached to a user session.
        await p.stop()

    print(f"\nDone. JSON updated: {WIKI_JSON}")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--only", help="Fetch only customers whose key or name matches this substring")
    ap.add_argument("--refresh", action="store_true", help="Re-fetch even customers with existing content")
    ap.add_argument("--dry-run", action="store_true", help="Do not write back to JSON")
    ap.add_argument("--cdp-url", default="http://localhost:9222", help="CDP endpoint of the running Edge")
    args = ap.parse_args()
    try:
        rc = asyncio.run(run(args))
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        rc = 130
    sys.exit(rc)


if __name__ == "__main__":
    main()
