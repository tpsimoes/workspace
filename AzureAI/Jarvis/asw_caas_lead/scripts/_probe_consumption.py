from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.connect_over_cdp("http://localhost:9222")
    ctx = b.contexts[0]
    pg = None
    for x in ctx.pages:
        if "cxp.azure.com" in x.url and "tpid:603819" in x.url:
            pg = x; break
    if not pg:
        for x in ctx.pages:
            if "cxp.azure.com" in x.url:
                pg = x; break
    print("url:", pg.url[:150])
    # dump all buttons/links whose text contains 'Consumption'
    rows = pg.evaluate("""() => {
        const out = [];
        for (const el of document.querySelectorAll('button, a, [role="button"], [role="treeitem"]')) {
            const t = (el.innerText || '').slice(0, 80);
            if (/Consumption/i.test(t)) {
                const r = el.getBoundingClientRect();
                out.push({
                    tag: el.tagName,
                    role: el.getAttribute('role'),
                    text: JSON.stringify(t),
                    textLen: t.length,
                    aria: el.getAttribute('aria-label'),
                    x: Math.round(r.x), y: Math.round(r.y),
                    w: Math.round(r.width), h: Math.round(r.height),
                    visible: r.width > 0 && r.height > 0,
                });
            }
        }
        return out.slice(0, 30);
    }""")
    for r in rows:
        print("  ", r)
