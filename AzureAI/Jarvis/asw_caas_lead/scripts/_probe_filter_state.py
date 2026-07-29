"""Probe current filter state on the running PBI dashboard on CDP:9222."""
import asyncio
import sys
import io
from playwright.async_api import async_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


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
            raise SystemExit("No dashboard tab found.")
        try:
            await target.bring_to_front()
        except Exception:
            pass
        # Locate the PBI iframe (usually where filter pane lives)
        pbi = None
        for fr in target.frames:
            try:
                url = fr.url or ""
            except Exception:
                url = ""
            if "powerbi" in url or "app.powerbi" in url:
                pbi = fr
                break
        if not pbi:
            # try the frame with document text containing filter restatement
            for fr in target.frames:
                try:
                    text = await fr.evaluate("() => document.body ? document.body.innerText : ''")
                except Exception:
                    continue
                if "Filters" in text or "Channel Function" in text or "filters" in text or "篩選" in text:
                    pbi = fr
                    print(f"Using text-match frame url={fr.url[:120]}")
                    break
        print("PBI frame:", pbi.url[:200] if pbi else None)

        # Try to click the "篩選" (Filters) collapsed pane on the right
        if pbi:
            # Show open filter pane if collapsed
            try:
                await pbi.get_by_label("展開 [篩選] 窗格").click(timeout=3000)
                print("Expanded filter pane")
            except Exception:
                try:
                    await pbi.get_by_label("Expand filter pane").click(timeout=3000)
                    print("Expanded filter pane (EN)")
                except Exception as e:
                    print("Filter pane may already be open or selector different:", e)

            await pbi.wait_for_timeout(2000)

            # Read all filter card headers + restatement text
            try:
                cards = await pbi.evaluate("""
                    () => {
                        const cards = document.querySelectorAll('[class*="filterCard"], [class*="filter-card"], [aria-label*="filter"], [role="group"]');
                        return Array.from(cards).slice(0, 30).map(c => c.getAttribute('aria-label') || c.textContent?.slice(0, 200));
                    }
                """)
                print("Filter card labels:")
                for c in cards[:30]:
                    if c and any(k in c for k in ("Channel", "Time", "Fiscal", "篩選", "Twelve", "Six")):
                        print("  ", c[:200])
            except Exception as e:
                print("could not enum cards:", e)


asyncio.run(main())
