#!/usr/bin/env python3
"""Orchestrates a single report generation: dashboard URL -> scrape -> HTML.

Kept import-light: the heavy Selenium/scrape modules are imported lazily inside
build() so the web server can be imported and unit-tested without a browser.
"""
import html
import tempfile
import time
import traceback
from pathlib import Path


def _error_html(url, err):
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"/>
<title>Report generation failed</title>
<style>body{{background:#0d1117;color:#e6edf3;font:15px/1.5 Segoe UI,Arial,sans-serif;
padding:40px;max-width:900px;margin:0 auto}}code{{background:#21262d;padding:2px 6px;border-radius:4px}}
pre{{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:14px;overflow:auto}}</style>
</head><body>
<h1>Report generation failed</h1>
<p>The dashboard could not be scraped and rendered.</p>
<p><b>Dashboard URL:</b> <code>{html.escape(url)}</code></p>
<p>The most common cause is a missing Grafana session &mdash; set the
<code>GRAFANA_COOKIES</code> environment variable to a valid signed-in cookie set.</p>
<pre>{html.escape(err)}</pre>
</body></html>"""


def build(url, out_path):
    """Scrape the dashboard and write the HTML report to out_path.

    Always writes *something* to out_path (an error page on failure) so the
    pre-announced download URL resolves either way.
    """
    out_path = Path(out_path)
    t0 = time.time()
    try:
        from scrape import capture
        from report import build_html
        workdir = Path(tempfile.mkdtemp(prefix="vmrca_"))
        cap_dir = workdir / "caps"
        manifest = capture(url, cap_dir)
        htmldoc = build_html(url, cap_dir, manifest)
        out_path.write_text(htmldoc, encoding="utf-8")
        print(f"[generate] wrote {out_path} ({out_path.stat().st_size // 1024} KB) "
              f"in {time.time() - t0:.0f}s", flush=True)
    except Exception as e:
        out_path.write_text(_error_html(url, traceback.format_exc()), encoding="utf-8")
        print(f"[generate] FAILED for {url}: {e}", flush=True)


if __name__ == "__main__":
    import sys
    build(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "report.html")
