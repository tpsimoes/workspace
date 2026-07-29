"""
CX Observe auth helper — click through the Microsoft account picker
using the workplace account (jacobw@microsoft.com) with Windows SSO.
"""

from __future__ import annotations

import sys
import time

from playwright.sync_api import sync_playwright  # type: ignore


def main() -> int:
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://localhost:9222")
        ctx = browser.contexts[0]

        target = None
        for pg in ctx.pages:
            u = pg.url.lower()
            if "login.microsoftonline.com" in u or "cxp.azure.com" in u:
                target = pg
                break

        if not target:
            print("[auth] No login or cxobserve tab found")
            return 1

        print(f"[auth] active: {target.url[:120]}")

        # If we're on account picker: click the microsoft.com account tile
        if "login.microsoftonline.com" in target.url.lower():
            print("[auth] on Microsoft login — clicking jacobw@microsoft.com tile")
            try:
                # tile has data-test-id or text; try text selector first
                tile = target.locator("div[role='button']").filter(has_text="jacobw@microsoft.com").first
                tile.wait_for(state="visible", timeout=10000)
                tile.click()
            except Exception as e:
                print(f"[auth] first selector failed: {e}")
                try:
                    target.get_by_text("jacobw@microsoft.com").click()
                except Exception as e2:
                    print(f"[auth] second selector failed: {e2}")
                    return 2

            # Wait for redirect
            for _ in range(40):
                time.sleep(1)
                if "cxp.azure.com" in target.url.lower():
                    print(f"[auth] redirected to cxobserve: {target.url[:120]}")
                    break
                if "login.microsoftonline.com" not in target.url.lower():
                    print(f"[auth] moved off login: {target.url[:120]}")
                    break
            else:
                print(f"[auth] still on login after 40s: {target.url[:120]}")

        # Wait a bit for cxobserve to render
        try:
            target.wait_for_load_state("networkidle", timeout=45000)
        except Exception:
            pass
        time.sleep(3)
        print(f"[auth] final url: {target.url[:200]}")
        title = target.title()
        print(f"[auth] page title: {title!r}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
