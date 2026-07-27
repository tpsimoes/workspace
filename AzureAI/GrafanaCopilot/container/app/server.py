#!/usr/bin/env python3
"""Lightweight HTTPS server for on-demand VM Reboot Analyzer reports.

Flow
----
POST /            body = a Grafana dashboard URL (raw text, form field `url`,
                  or JSON {"url": ...}). The server immediately:
                    1. generates a random report filename,
                    2. builds the eventual download URL,
                    3. replies 202 with "Your report will soon be available at <url>",
                    4. scrapes + renders the report in a background thread.
GET  /reports/<file>   downloads the report once ready (202 "still generating"
                       while the worker runs, 404 if unknown).
GET  /                 tiny usage/health page.

Everything is stdlib except the report pipeline. Reports live in ephemeral
storage (REPORTS_DIR, default /reports).

Env
---
PORT              listen port (default 443)
REPORTS_DIR       where reports are written (default /reports)
PUBLIC_BASE_URL   base for the announced URL, e.g. https://vmrca.example.com
                  (default: derived from the request Host header)
TLS_CERT/TLS_KEY  cert + key paths (default /certs/server.crt, /certs/server.key)
MAX_CONCURRENCY   max simultaneous report generations (default 2)
"""
import json
import os
import ssl
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import generate

PORT = int(os.environ.get("PORT", "443"))
REPORTS_DIR = Path(os.environ.get("REPORTS_DIR", "/reports"))
PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", "").rstrip("/")
TLS_CERT = os.environ.get("TLS_CERT", "/certs/server.crt")
TLS_KEY = os.environ.get("TLS_KEY", "/certs/server.key")
MAX_CONCURRENCY = int(os.environ.get("MAX_CONCURRENCY", "2"))

REPORTS_DIR.mkdir(parents=True, exist_ok=True)
_sem = threading.BoundedSemaphore(MAX_CONCURRENCY)
_status = {}                      # token -> "pending" | "ready" | "error"
_status_lock = threading.Lock()
_URL_RE = __import__("re").compile(r"https?://[^\s\"'<>]+")

USAGE = b"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>VM Reboot Analyzer service</title>
<style>body{background:#0d1117;color:#e6edf3;font:15px/1.5 Segoe UI,Arial,sans-serif;padding:40px;max-width:820px;margin:0 auto}code,pre{background:#161b22;border:1px solid #30363d;border-radius:6px}code{padding:2px 6px}pre{padding:14px;overflow:auto}</style>
</head><body><h1>VM Reboot Analyzer report service</h1>
<p>POST a Grafana dashboard URL to <code>/</code> and you'll get back a link to the report that will
be generated shortly.</p>
<pre>curl -sk -X POST https://HOST/ -d 'https://.../d/tictrm7/virtual-machine-reboot-analyzer?...var-_id=...'</pre>
<p>or JSON:</p>
<pre>curl -sk -X POST https://HOST/ -H 'Content-Type: application/json' -d '{"url":"https://.../d/..."}'</pre>
</body></html>"""


def _set(token, state):
    with _status_lock:
        _status[token] = state


def _get(token):
    with _status_lock:
        return _status.get(token)


def _base_url(handler):
    if PUBLIC_BASE_URL:
        return PUBLIC_BASE_URL
    host = handler.headers.get("Host") or f"localhost:{PORT}"
    return f"https://{host}"


def _extract_url(body, ctype):
    body = (body or "").strip()
    if not body:
        return None
    if "application/json" in ctype:
        try:
            data = json.loads(body)
            for k in ("url", "dashboard", "dashboardUrl", "dashboard_url"):
                if isinstance(data, dict) and data.get(k):
                    body = str(data[k]).strip()
                    break
        except Exception:
            pass
    elif "application/x-www-form-urlencoded" in ctype:
        qs = parse_qs(body)
        for k in ("url", "dashboard", "dashboardUrl"):
            if qs.get(k):
                body = qs[k][0].strip()
                break
    m = _URL_RE.search(body)
    return m.group(0) if m else None


def _worker(token, url, out_path):
    with _sem:
        try:
            generate.build(url, out_path)
            _set(token, "ready")
        except Exception:
            _set(token, "error")


class Handler(BaseHTTPRequestHandler):
    server_version = "VMRCA/1.0"

    def log_message(self, fmt, *args):
        print("[http] " + (fmt % args), flush=True)

    def _send(self, code, body, ctype="text/plain; charset=utf-8", extra=None):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        if path in ("/", "/health"):
            if path == "/health":
                return self._send(200, "ok")
            return self._send(200, USAGE, "text/html; charset=utf-8")
        if path.startswith("/reports/"):
            name = os.path.basename(path)
            if not name.endswith(".html") or "/" in name.replace("/reports/", ""):
                return self._send(400, "Bad report name")
            fpath = REPORTS_DIR / name
            token = name[:-5]
            if fpath.exists():
                data = fpath.read_bytes()
                return self._send(200, data, "text/html; charset=utf-8",
                                  {"Content-Disposition": f'attachment; filename="{name}"'})
            state = _get(token)
            if state == "pending":
                return self._send(202, "Your report is still being generated. "
                                        "Please retry this URL shortly.")
            return self._send(404, "Report not found.")
        return self._send(404, "Not found")

    def do_HEAD(self):
        self.do_GET()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0") or "0")
        body = self.rfile.read(length).decode("utf-8", "replace") if length else ""
        url = _extract_url(body, self.headers.get("Content-Type", ""))
        if not url:
            return self._send(400, "No dashboard URL found in the request body. Send the URL as "
                                   "raw text, form field 'url', or JSON {\"url\": ...}.")
        token = uuid.uuid4().hex[:20]
        name = f"{token}.html"
        report_url = f"{_base_url(self)}/reports/{name}"
        out_path = REPORTS_DIR / name
        _set(token, "pending")
        threading.Thread(target=_worker, args=(token, url, out_path), daemon=True).start()
        self._send(202, f"Your report will soon be available at {report_url}",
                   extra={"Location": report_url})


def main():
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(certfile=TLS_CERT, keyfile=TLS_KEY)
    httpd = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    httpd.socket = ctx.wrap_socket(httpd.socket, server_side=True)
    print(f"[server] HTTPS listening on :{PORT}  reports_dir={REPORTS_DIR}  "
          f"public_base={PUBLIC_BASE_URL or '(from Host header)'}", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()


if __name__ == "__main__":
    main()
