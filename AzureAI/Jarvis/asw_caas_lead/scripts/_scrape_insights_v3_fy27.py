"""Extract Insights+_v3 FY27 KPIs from the running Edge on CDP :9222.
Assumes the dashboard tab is already open at the ASW_SAPEpicEsc/FY2027 view.
Dumps full frame texts to a UTF-8 file for offline inspection.
"""
import asyncio
import sys
import io
from pathlib import Path
from playwright.async_api import async_playwright

# Force UTF-8 stdout
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

OUT = Path("Output/_insights_v3_fy27_frames.txt")


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
            raise SystemExit("No dashboard tab found on CDP:9222 - open URL manually first.")
        try:
            await target.bring_to_front()
        except Exception:
            pass

        # Wait for PBI to hydrate
        await target.wait_for_timeout(15000)

        buf = []
        for i, fr in enumerate(target.frames):
            try:
                text = await fr.evaluate("() => document.body ? document.body.innerText : ''")
            except Exception as e:
                text = f"<eval failed: {e}>"
            buf.append(f"\n\n===== FRAME [{i}] name={fr.name!r} url={fr.url[:200]} =====\n{text}")

        OUT.write_text("".join(buf), encoding="utf-8")
        size = OUT.stat().st_size
        print(f"Wrote {size} bytes to {OUT}")

        # Also print a filtered summary to stdout
        for chunk in buf:
            head = chunk.split("=====\n", 1)[0]
            body = chunk.split("=====\n", 1)[1] if "=====\n" in chunk else ""
            interesting = [ln.strip() for ln in body.splitlines()
                           if any(k in ln for k in (
                               "FY2027", "FY 2027", "FY2026", "FY 2026",
                               "Created Cases", "Closed Cases", "CSAT",
                               "IR Met", "Avg DTC", "CritSit", "Backlog",
                               "Response Rate", "% SR", "ASW_SAPEpicEsc",
                               "Channel Function", "Time Fiscal"))]
            if interesting:
                print(head + "=====")
                for ln in interesting:
                    print("   ", ln[:250])


asyncio.run(main())
