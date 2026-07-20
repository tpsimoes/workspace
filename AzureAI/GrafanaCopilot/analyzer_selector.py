#!/usr/bin/env python3
"""
Analyzer Selector - build and open the Azure Managed Grafana "Analyzer Selector"
dashboard for a given Azure VM (ARM ID or VM ID) over a start/end time range.

This is the entry-point dashboard that links to the per-VM analyzers
(Virtual Machine Analyzer, Virtual Machine Reboot Analyzer, ...). Provide a VM
ARM ID or VM ID and it fills the `var-_id` template variable, then opens the
page in Microsoft Edge (required by the tenant Conditional Access policy).

Usage examples:
  python analyzer_selector.py --id "/subscriptions/xxxx/resourceGroups/rg/providers/microsoft.compute/virtualmachines/myvm"

  python analyzer_selector.py --id "6e965a4d-9d96-49ea-bb97-d866f1247659" --from now-2d --to now

  python analyzer_selector.py --id "..." --from "2026-06-26T00:00:00Z" --to "2026-06-28T23:59:59Z" --no-open
"""

import argparse
import shutil
import subprocess
import sys
import urllib.parse
import webbrowser
from datetime import datetime, timezone

GRAFANA_BASE = "https://asw-main-c9d6bfgzgnbydnae.eus2.grafana.azure.com"
DASHBOARD_UID = "ddiavrf61i1a8a"
DASHBOARD_SLUG = "analyzer-selector"
ORG_ID = "1"


def parse_time(value: str) -> str:
    """Convert a user-supplied time into a Grafana `from`/`to` value.

    Accepts:
      - Grafana relative strings ("now", "now-24h", "now-7d") -> passed through
      - Epoch milliseconds (13+ digits) -> passed through
      - Epoch seconds (<=12 digits) -> converted to milliseconds
      - ISO-8601 datetimes ("2026-06-01", "2026-06-01T12:00:00Z") -> epoch ms
    """
    if value is None:
        raise ValueError("time value is required")
    v = value.strip()

    if v == "now" or v.startswith("now-") or v.startswith("now+"):
        return v

    if v.lstrip("-").isdigit():
        n = int(v)
        if len(v.lstrip("-")) >= 13:
            return str(n)
        return str(n * 1000)

    iso = v.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(iso)
    except ValueError:
        raise ValueError(
            f"Unrecognized time '{value}'. Use ISO-8601 (2026-06-01T00:00:00Z), "
            f"epoch ms, or a Grafana relative like now-24h."
        )
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return str(int(dt.timestamp() * 1000))


def normalize_id(vm_id: str) -> str:
    """Normalize the identifier used for the `var-_id` template variable.

    Full Azure ARM resource IDs are conventionally lower-cased in this Grafana
    instance, so they are lower-cased here. VM ID GUIDs pass through unchanged.
    """
    vid = vm_id.strip()
    if vid.lower().startswith("/subscriptions/"):
        return vid.lower()
    return vid


def build_url(vm_id: str, time_from: str, time_to: str, timezone_str: str = "utc") -> str:
    params = {
        "orgId": ORG_ID,
        "from": time_from,
        "to": time_to,
        "timezone": timezone_str,
        "var-_id": normalize_id(vm_id),
    }
    query = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    return f"{GRAFANA_BASE}/d/{DASHBOARD_UID}/{DASHBOARD_SLUG}?{query}"


def open_in_edge(url: str) -> bool:
    """Open the URL in Microsoft Edge (satisfies device Conditional Access).

    Falls back to the default browser if Edge cannot be located.
    """
    edge = shutil.which("msedge")
    if not edge:
        for candidate in (
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        ):
            import os
            if os.path.exists(candidate):
                edge = candidate
                break
    if edge:
        try:
            subprocess.Popen([edge, url])
            return True
        except Exception:
            pass
    return webbrowser.open(url)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Build and open the Grafana Analyzer Selector dashboard for an Azure VM.",
    )
    parser.add_argument(
        "--id",
        required=True,
        help="Azure VM ARM ID (/subscriptions/.../virtualMachines/name) or VM ID (GUID).",
    )
    parser.add_argument(
        "--from",
        dest="time_from",
        default="now-24h",
        help="Start time: ISO-8601, epoch ms/s, or Grafana relative (default: now-24h).",
    )
    parser.add_argument(
        "--to",
        dest="time_to",
        default="now",
        help="End time: ISO-8601, epoch ms/s, or Grafana relative (default: now).",
    )
    parser.add_argument(
        "--timezone",
        default="utc",
        help="Dashboard timezone (default: utc).",
    )
    parser.add_argument(
        "--no-open",
        action="store_true",
        help="Only print the URL; do not launch the browser.",
    )
    args = parser.parse_args(argv)

    try:
        time_from = parse_time(args.time_from)
        time_to = parse_time(args.time_to)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    url = build_url(args.id, time_from, time_to, args.timezone)
    print(url)

    if not args.no_open:
        if not open_in_edge(url):
            print("warning: could not launch a browser; open the URL above manually.",
                  file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
