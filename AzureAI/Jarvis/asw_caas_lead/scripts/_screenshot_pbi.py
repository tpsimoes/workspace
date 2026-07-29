"""Screenshot the running PBI dashboard on CDP:9222 to a PNG file."""
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

OUT = Path("Output/_insights_v3_current_state.png")


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
        await target.wait_for_timeout(3000)
        # Get viewport size and take full page screenshot
        await target.screenshot(path=str(OUT), full_page=True)
        print(f"Saved {OUT} ({OUT.stat().st_size} bytes)")


asyncio.run(main())
