"""Apply the 4 required filters to Insights+_v3 dashboard on CDP:9222.

Filters (per review-reporter SKILL Dashboard 1):
  1. Channel Function Detail = ASW_SAPEpicEsc
  2. Time LastTwelveMonths = (All)
  3. Time LastSixMonths = (All)
  4. Time Fiscal Year = FY 2027 only (clear + reselect if bookmark set FY26+FY27)

Then wait 2 minutes and re-extract KPIs.
"""
import asyncio
import sys
import io
from pathlib import Path
from playwright.async_api import async_playwright, TimeoutError as PWTimeout

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


async def try_click(fr, sels, timeout=3000, label=""):
    for s in sels:
        try:
            loc = fr.locator(s).first
            await loc.click(timeout=timeout)
            print(f"  [ok] clicked {label!r} via {s!r}")
            return True
        except Exception as e:
            print(f"  [.] tried {s!r} for {label!r}: {type(e).__name__}")
    return False


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        ctx = browser.contexts[0]
        target = None
        for pg in ctx.pages:
            if "81538463" in pg.url:
                target = pg
                break
        if not target:
            raise SystemExit("No dashboard tab on CDP:9222")
        try:
            await target.bring_to_front()
        except Exception:
            pass

        # find the PBI content frame — the one that has "篩選" or "Filters" pane text
        pbi = None
        for fr in target.frames:
            try:
                text = await fr.evaluate("() => document.body ? document.body.innerText : ''")
            except Exception:
                continue
            if text and ("篩選" in text or "Filters" in text or "Channel Function" in text):
                pbi = fr
                break
        if not pbi:
            pbi = target
        print("PBI frame url:", pbi.url[:120])

        # ---- Step 0: expand the filter pane on the right (button "展開 [篩選] 窗格" or "Expand filter pane")
        print("\n[Step 0] Expand filter pane")
        await try_click(pbi, [
            "button[aria-label='展開 [篩選] 窗格']",
            "button[aria-label='Expand filter pane']",
            "button[title*='篩選']",
            "[aria-label*='Expand filter pane']",
        ], label="expand filter pane")
        await pbi.wait_for_timeout(2500)

        # ---- List all filter card aria-labels for context
        cards = await pbi.evaluate("""
            () => {
                const els = document.querySelectorAll('[aria-label][role]');
                const out = [];
                for (const el of els) {
                    const a = el.getAttribute('aria-label') || '';
                    const r = el.getAttribute('role') || '';
                    if (a.includes('Channel Function') || a.includes('Time Fiscal') || a.includes('Time LastTwelve') || a.includes('Time LastSix') || a.includes('filter card')) {
                        out.push(r + ' | ' + a.slice(0, 180));
                    }
                }
                return out;
            }
        """)
        print("Filter cards found:")
        for c in cards[:30]:
            print("   ", c)

        # ---- Step 1: Channel Function Detail = ASW_SAPEpicEsc
        print("\n[Step 1] Channel Function Detail")
        # Expand the filter card first
        await try_click(pbi, [
            "button[aria-label='Channel Function Detail Expand or collapse filter card']",
            "button[aria-label*='Channel Function Detail'][aria-label*='Expand']",
            "[aria-label*='Channel Function Detail']",
        ], label="expand Channel Function Detail card")
        await pbi.wait_for_timeout(1500)
        # Search box inside the card for 'ASW_SAP'
        try:
            search = pbi.locator("input[aria-label*='Channel Function']").first
            await search.fill("ASW_SAP", timeout=3000)
            print("  [ok] typed ASW_SAP into Channel Function search")
        except Exception as e:
            print(f"  [.] no search box: {e}")
        await pbi.wait_for_timeout(1500)
        # Tick ASW_SAPEpicEsc checkbox
        await try_click(pbi, [
            "[role='checkbox'][aria-label*='ASW_SAPEpicEsc']",
            "label:has-text('ASW_SAPEpicEsc')",
            "text=ASW_SAPEpicEsc",
        ], label="tick ASW_SAPEpicEsc")
        await pbi.wait_for_timeout(1500)

        # ---- Step 2: Time LastTwelveMonths = (All) - Clear filter
        print("\n[Step 2] Time LastTwelveMonths -> (All)")
        try:
            twelve = pbi.locator("[aria-label*='Time LastTwelveMonths']").first
            # click nearest 'Clear filter' button under this card
            await twelve.locator("xpath=ancestor::*[contains(@aria-label,'filter card')]//button[@aria-label='Clear filter']").click(timeout=3000)
            print("  [ok] cleared LastTwelveMonths")
        except Exception as e:
            print(f"  [.] clear LastTwelveMonths: {e}")
        await pbi.wait_for_timeout(1000)

        # ---- Step 3: Time LastSixMonths = (All) - Clear filter
        print("\n[Step 3] Time LastSixMonths -> (All)")
        try:
            six = pbi.locator("[aria-label*='Time LastSixMonths']").first
            await six.locator("xpath=ancestor::*[contains(@aria-label,'filter card')]//button[@aria-label='Clear filter']").click(timeout=3000)
            print("  [ok] cleared LastSixMonths")
        except Exception as e:
            print(f"  [.] clear LastSixMonths: {e}")
        await pbi.wait_for_timeout(1000)

        # ---- Step 4: Time Fiscal Year = FY 2027 only
        print("\n[Step 4] Time Fiscal Year -> FY 2027 only")
        try:
            fy = pbi.locator("[aria-label*='Time Fiscal Year']").first
            await fy.locator("xpath=ancestor::*[contains(@aria-label,'filter card')]//button[@aria-label='Clear filter']").click(timeout=3000)
            print("  [ok] cleared Time Fiscal Year")
        except Exception as e:
            print(f"  [.] clear Time Fiscal Year: {e}")
        await pbi.wait_for_timeout(1500)
        await try_click(pbi, [
            "button[aria-label='Time Fiscal Year Expand or collapse filter card']",
            "[aria-label*='Time Fiscal Year'][aria-label*='Expand']",
        ], label="expand Time Fiscal Year card")
        await pbi.wait_for_timeout(1500)
        await try_click(pbi, [
            "[role='checkbox'][aria-label*='FY 2027']",
            "[role='checkbox'][aria-label*='FY2027']",
            "label:has-text('FY 2027')",
        ], label="tick FY 2027")
        await pbi.wait_for_timeout(2000)

        # ---- Screenshot filter state
        print("\n[Screenshot] saving to Output/_after_filters.png ...")
        await target.screenshot(path="Output/_after_filters.png", full_page=True)
        print("saved.")


asyncio.run(main())
