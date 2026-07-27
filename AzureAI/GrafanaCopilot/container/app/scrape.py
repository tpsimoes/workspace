#!/usr/bin/env python3
"""Headless-Chromium (Selenium) capture of every panel on a Grafana VM
Analyzer dashboard.

This is the container-friendly port of enumerate_all.py: instead of Playwright
with a persistent Edge profile it drives the system Chromium via Selenium, which
works reliably on Alpine/musl. It writes <out_dir>/panel-NN-<slug>.png plus
<out_dir>/manifest.json with {index, title, text, no_data, file} per panel.

Auth: Managed Grafana usually requires a signed-in session. Provide it by
setting GRAFANA_COOKIES to a JSON array of cookie objects
([{"name":..,"value":..,"domain":..,"path":"/"}]); they are injected before the
dashboard is loaded. Without a valid session the scrape still runs and captures
whatever renders (e.g. a login page), and the report notes the failure.
"""
import json
import os
import re
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

CHROME_BIN = os.environ.get("CHROME_BIN", "/usr/bin/chromium-browser")
CHROMEDRIVER = os.environ.get("CHROMEDRIVER", "/usr/bin/chromedriver")

# --- JavaScript helpers (mirrors enumerate_all.py, element passed as arguments[0]) ---

GROW_JS = r"""
const el = arguments[0];
if (!el.__expandSaved) el.__expandSaved = [];
const save = (n) => { el.__expandSaved.push([n, n.getAttribute('style')]); };
for (let pass = 0; pass < 4; pass++) {
    el.querySelectorAll('*').forEach((n) => {
        const sy = n.scrollHeight - n.clientHeight > 4;
        const sx = n.scrollWidth - n.clientWidth > 4;
        if (sy || sx) {
            save(n);
            n.style.overflow = 'visible';
            n.style.overflowX = 'visible';
            n.style.overflowY = 'visible';
            n.style.maxHeight = 'none';
            n.style.maxWidth = 'none';
            if (sy) n.style.height = n.scrollHeight + 'px';
            if (sx) n.style.width = n.scrollWidth + 'px';
        }
    });
}
save(el);
el.style.overflow = 'visible';
el.style.maxHeight = 'none';
el.style.height = el.scrollHeight + 'px';
el.querySelectorAll('*').forEach((n) => {
    const cs = getComputedStyle(n);
    if (cs.position === 'sticky') { save(n); n.style.position = 'static'; }
});
window.dispatchEvent(new Event('resize'));
"""

RESTORE_JS = r"""
const el = arguments[0];
(el.__expandSaved || []).slice().reverse().forEach(([n, s]) => {
    if (s === null) n.removeAttribute('style'); else n.setAttribute('style', s);
});
el.__expandSaved = [];
window.dispatchEvent(new Event('resize'));
"""

HIDE_CHROME_JS = r"""
window.__hidChrome = [];
const hideEl = (n, mode) => {
    if (n.closest('div.react-grid-item')) return;
    window.__hidChrome.push([n, n.style.visibility, n.style.display]);
    if (mode === 'display') n.style.display = 'none'; else n.style.visibility = 'hidden';
};
document.querySelectorAll('body *').forEach((n) => {
    const cs = getComputedStyle(n);
    if (cs.position === 'fixed' || cs.position === 'absolute') hideEl(n, 'display');
    else if (cs.position === 'sticky') hideEl(n, 'visibility');
});
document.querySelectorAll('header, nav, [role="banner"]').forEach((n) => hideEl(n, 'display'));
"""

RESTORE_CHROME_JS = r"""
(window.__hidChrome || []).forEach(([n, v, d]) => { n.style.visibility = v; n.style.display = d; });
window.__hidChrome = [];
"""

SCROLL_STEP_JS = ("const el=document.querySelector('[class*=\"scrollbar-view\"]')"
                  "||document.scrollingElement; el.scrollTop+=el.clientHeight*0.7;")
SCROLL_TOP_JS = ("const el=document.querySelector('[class*=\"scrollbar-view\"]')"
                 "||document.scrollingElement; el.scrollTop=0;")
LOADING_JS = r"""
const sels=['[data-testid="data-testid Panel loading bar"]','.panel-loading',
            'div[class*="LoadingBar"]','[aria-label="Panel loading bar"]'];
let t=0; sels.forEach(s=>t+=document.querySelectorAll(s).length); return t;
"""


def slug(t):
    return re.sub(r"[^a-zA-Z0-9]+", "-", t or "panel").strip("-").lower()[:50] or "panel"


def autocrop(path, thresh=24, pad=10):
    try:
        from PIL import Image
    except Exception:
        return
    try:
        im = Image.open(path).convert("RGB")
    except Exception:
        return
    mask = im.convert("L").point(lambda x: 255 if x > thresh else 0)
    bbox = mask.getbbox()
    if not bbox:
        return
    l, t, r, b = bbox
    l, t = max(0, l - pad), max(0, t - pad)
    r, b = min(im.width, r + pad), min(im.height, b + pad)
    if r - l < 20 or b - t < 20:
        return
    if (l, t, r, b) != (0, 0, im.width, im.height):
        im.crop((l, t, r, b)).save(path)


def _make_driver():
    opts = Options()
    opts.binary_location = CHROME_BIN
    for a in ("--headless=new", "--no-sandbox", "--disable-dev-shm-usage",
              "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1",
              "--window-size=1920,3200", "--disable-extensions"):
        opts.add_argument(a)
    driver = webdriver.Chrome(service=Service(CHROMEDRIVER), options=opts)
    driver.set_page_load_timeout(90)
    driver.set_window_size(1920, 3200)
    return driver


def _inject_cookies(driver, url):
    raw = os.environ.get("GRAFANA_COOKIES", "").strip()
    if not raw:
        return
    try:
        cookies = json.loads(raw)
    except Exception:
        return
    m = re.match(r"(https?://[^/]+)", url)
    if not m:
        return
    driver.get(m.group(1) + "/robots.txt")
    for c in cookies:
        ck = {k: v for k, v in c.items()
              if k in ("name", "value", "domain", "path", "secure", "httpOnly", "expiry")}
        try:
            driver.add_cookie(ck)
        except Exception:
            pass


def _loading(driver):
    try:
        return int(driver.execute_script(LOADING_JS))
    except Exception:
        return 0


def _wait_loaded(driver, timeout=90, settle=2.5):
    end = time.time() + timeout
    stable = 0
    while time.time() < end:
        if _loading(driver) == 0:
            stable += 1
            if stable >= 3:
                break
        else:
            stable = 0
        time.sleep(0.7)
    time.sleep(settle)


def capture(url, out_dir):
    """Scrape every panel; return the manifest list."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    driver = _make_driver()
    manifest = []
    try:
        _inject_cookies(driver, url)
        driver.get(url)
        WebDriverWait(driver, 120).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div.react-grid-item')))
        time.sleep(4)

        # Expand any collapsed dashboard rows.
        for _ in range(6):
            rows = driver.find_elements(
                By.CSS_SELECTOR, '[data-testid*="dashboard-row-title"][aria-expanded="false"]')
            if not rows:
                break
            for r in rows:
                try:
                    r.click()
                    time.sleep(0.4)
                except Exception:
                    pass

        # Full scroll passes so lazy panels load.
        for _pass in range(3):
            for _ in range(30):
                driver.execute_script(SCROLL_STEP_JS)
                time.sleep(0.45)
                if _loading(driver) > 0:
                    time.sleep(0.6)
            driver.execute_script(SCROLL_TOP_JS)
            _wait_loaded(driver)
        time.sleep(1.5)

        panels = driver.find_elements(By.CSS_SELECTOR, 'div.react-grid-item')
        total = len(panels)
        print(f"[scrape] found {total} panels", flush=True)
        for i, panel in enumerate(panels):
            title = ""
            hdr = panel.find_elements(By.CSS_SELECTOR, '[data-testid^="data-testid Panel header"]')
            if hdr:
                dt = hdr[0].get_attribute("data-testid") or ""
                title = dt.replace("data-testid Panel header", "").strip()
            try:
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", panel)
            except Exception:
                pass
            for _ in range(20):
                try:
                    lb = panel.find_elements(
                        By.CSS_SELECTOR, '[data-testid="data-testid Panel loading bar"], '
                        '.panel-loading, div[class*="LoadingBar"]')
                    if not lb:
                        break
                except Exception:
                    break
                time.sleep(0.5)
            time.sleep(1.0)
            try:
                text = panel.text
            except Exception as e:
                text = f"[text failed: {e}]"
            no_data = "No data" in text and len(text.strip()) < len(title) + 40
            fname = f"panel-{i:02d}-{slug(title)}.png"
            try:
                driver.execute_script(GROW_JS, panel)
                time.sleep(0.7)
                driver.execute_script(GROW_JS, panel)
                time.sleep(0.9)
            except Exception:
                pass
            try:
                driver.execute_script(HIDE_CHROME_JS)
                panel.screenshot(str(out_dir / fname))
                autocrop(out_dir / fname)
            except Exception as e:
                print(f"[scrape] shot {i} failed: {e}", flush=True)
                fname = None
            finally:
                try:
                    driver.execute_script(RESTORE_CHROME_JS)
                except Exception:
                    pass
                try:
                    driver.execute_script(RESTORE_JS, panel)
                except Exception:
                    pass
            manifest.append({"index": i, "title": title, "no_data": no_data,
                             "text": text.strip(), "file": fname})
            print(f"[scrape] [{i:02d}] {title!r} no_data={no_data} chars={len(text.strip())}",
                  flush=True)

        (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        return manifest
    finally:
        try:
            driver.quit()
        except Exception:
            pass


if __name__ == "__main__":
    import sys
    capture(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "caps")
