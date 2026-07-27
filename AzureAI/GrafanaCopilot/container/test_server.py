"""Smoke test for the async POST->announce->GET flow.

Runs the real Handler over PLAIN http (no TLS, so no openssl needed locally) with
a stubbed generate.build that writes a tiny report after a short delay. Verifies:
 - POST returns 202 with the announced /reports/<token>.html URL
 - GET on that URL returns 202 while pending, then 200 with the html once ready
 - URL extraction from raw text, form and JSON bodies
 - bad requests are rejected
"""
import os
import sys
import tempfile
import threading
import time
import urllib.request
import urllib.error
from http.server import ThreadingHTTPServer

os.environ["REPORTS_DIR"] = tempfile.mkdtemp(prefix="rep_")
os.environ["PORT"] = "8899"
os.environ["PUBLIC_BASE_URL"] = "https://localhost:8899"
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "app"))

import generate  # noqa: E402
import server    # noqa: E402


def stub_build(url, out_path):
    time.sleep(1.5)  # simulate slow scrape
    from pathlib import Path
    Path(out_path).write_text(f"<html><body>REPORT FOR {url}</body></html>", encoding="utf-8")


generate.build = stub_build

httpd = ThreadingHTTPServer(("127.0.0.1", 8899), server.Handler)
threading.Thread(target=httpd.serve_forever, daemon=True).start()
base = "http://127.0.0.1:8899"
time.sleep(0.3)
failures = []


def post(body, ctype=None):
    req = urllib.request.Request(base + "/", data=body.encode(), method="POST")
    if ctype:
        req.add_header("Content-Type", ctype)
    try:
        r = urllib.request.urlopen(req)
        return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


def get(path):
    try:
        r = urllib.request.urlopen(base + path)
        return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name)
    if not cond:
        failures.append(name)


DASH = ("https://asw-main-x.eus2.grafana.azure.com/d/tictrm7/"
        "virtual-machine-reboot-analyzer?orgId=1&var-_id=%2Fsubscriptions%2Fx%2F"
        "virtualMachines%2Fazlsapkaqdb06")

# 1. raw text POST
code, txt = post(DASH)
check("POST raw -> 202", code == 202)
check("POST announces URL", "will soon be available at https://localhost:8899/reports/" in txt)
report_path = "/reports/" + txt.split("/reports/")[1].strip()

# 2. immediate GET -> pending 202
code, _ = get(report_path)
check("GET while pending -> 202", code == 202)

# 3. wait, GET -> 200 with report
time.sleep(2.0)
code, body = get(report_path)
check("GET after ready -> 200", code == 200)
check("report body correct", "REPORT FOR" in body and "azlsapkaqdb06" in body)

# 4. JSON body
code, txt = post('{"url": "%s"}' % DASH, "application/json")
check("POST json -> 202", code == 202 and "/reports/" in txt)

# 5. form body
code, txt = post("url=" + DASH, "application/x-www-form-urlencoded")
check("POST form -> 202", code == 202 and "/reports/" in txt)

# 6. no url -> 400
code, _ = post("hello world no link here")
check("POST without url -> 400", code == 400)

# 7. unknown report -> 404
code, _ = get("/reports/deadbeefdeadbeef.html")
check("GET unknown -> 404", code == 404)

# 8. health
code, txt = get("/health")
check("health -> 200 ok", code == 200 and txt == "ok")

httpd.shutdown()
print("\n" + ("ALL PASSED" if not failures else f"FAILURES: {failures}"))
sys.exit(1 if failures else 0)
