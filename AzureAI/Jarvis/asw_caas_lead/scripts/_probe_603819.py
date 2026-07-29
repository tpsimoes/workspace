from playwright.sync_api import sync_playwright
import time
with sync_playwright() as p:
    b = p.chromium.connect_over_cdp("http://localhost:9222")
    ctx = b.contexts[0]
    pg = None
    for x in ctx.pages:
        if "cxp.azure.com" in x.url:
            pg = x; break
    if not pg:
        print("no cxobserve tab"); raise SystemExit
    print("url:", pg.url[:200])
    body = pg.evaluate("() => document.body.innerText || ''")
    print("has 603819:", "603819" in body)
    print("has SAP SE:", "SAP SE" in body)
    print("row count:", pg.evaluate("() => document.querySelectorAll('[role=\"row\"]').length"))
    print("snippet head:", body[:600].replace("\n"," | "))
    # try searching again with fresh navigation
    print("--- forcing re-search ---")
    pg.goto("https://cxp.azure.com/cxobserve/home", wait_until="domcontentloaded", timeout=60000)
    time.sleep(3)
    sb = pg.locator("input[placeholder*='Search' i]").first
    sb.click(); sb.fill(""); sb.type("603819", delay=80); time.sleep(2); sb.press("Enter")
    time.sleep(8)
    print("after url:", pg.url[:200])
    print("after row count:", pg.evaluate("() => document.querySelectorAll('[role=\"row\"]').length"))
    body2 = pg.evaluate("() => document.body.innerText || ''")
    print("has 603819:", "603819" in body2)
    print("has SAP SE:", "SAP SE" in body2)
    print("has No result:", "No result" in body2)
    # save snippet around 603819 or SAP SE
    for needle in ["603819", "SAP SE", "SAP"]:
        i = body2.find(needle)
        if i >= 0:
            print(f"snippet@{needle}:", body2[max(0,i-100):i+200].replace("\n"," | "))
            break
    pg.screenshot(path="Skills/asw_caas_lead/references/acr_capture_2026-07/_probe_603819.png", full_page=False, timeout=45000, animations="disabled")
    print("screenshot saved")
