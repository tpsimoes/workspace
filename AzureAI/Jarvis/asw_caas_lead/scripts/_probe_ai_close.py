from playwright.sync_api import sync_playwright
import time, json
with sync_playwright() as p:
    b = p.chromium.connect_over_cdp("http://localhost:9222")
    ctx = b.contexts[0]
    pg = None
    for x in ctx.pages:
        if "cxp.azure.com" in x.url:
            pg = x; break
    print("url:", pg.url[:120])
    # 1. Find AI Assistant toggle/close candidates
    print("\n=== AI Assistant candidates ===")
    cands = pg.evaluate("""() => {
        const out = [];
        for (const el of document.querySelectorAll('button, [role=\"button\"]')) {
            const t = (el.innerText || '').trim().slice(0, 40);
            const aria = el.getAttribute('aria-label') || '';
            if (/AI Assistant|close|dismiss/i.test(t + ' ' + aria)) {
                const r = el.getBoundingClientRect();
                out.push({tag: el.tagName, text: t, aria, visible: r.width>0 && r.height>0, x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width)});
            }
        }
        return out.slice(0, 25);
    }""")
    for c in cands:
        print(f"  {c}")
    # 2. Find Consumption / Consumption details link
    print("\n=== Consumption nav items ===")
    navs = pg.evaluate("""() => {
        const out = [];
        for (const el of document.querySelectorAll('[role=\"button\"], a, button, [role=\"treeitem\"], [role=\"menuitem\"]')) {
            const t = (el.innerText || '').trim();
            if (/^(Consumption|Consumption details|Revenue details|Customer summary|Compute|Storage)$/i.test(t)) {
                const r = el.getBoundingClientRect();
                out.push({tag: el.tagName, text: t.slice(0,40), role: el.getAttribute('role'), x: Math.round(r.x), y: Math.round(r.y), visible: r.width>0 && r.height>0});
            }
        }
        return out;
    }""")
    for n in navs:
        print(f"  {n}")
    # 3. Look at page body for consumption content
    print("\n=== body has (before Consumption details click) ===")
    body = pg.evaluate("() => document.body.innerText || ''")
    for token in ["Total consumption", "Consumption trend", "USD", "Last 6 Months", "Consumption in"]:
        print(f"  '{token}': count={body.count(token)}")
