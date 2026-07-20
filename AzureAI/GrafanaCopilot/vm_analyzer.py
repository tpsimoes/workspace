#!/usr/bin/env python3
"""
VM Analyzer - build and open the Azure Managed Grafana "Virtual Machine Analyzer"
dashboard for a given Azure VM (ARM ID or VM ID) over a start/end time range.

Usage examples:
  python vm_analyzer.py --id "/subscriptions/xxxx/resourceGroups/rg/providers/microsoft.compute/virtualmachines/myvm" \
      --from "2026-06-01T00:00:00Z" --to "2026-06-02T00:00:00Z"

  python vm_analyzer.py --id "myvm" --from "now-24h" --to "now"

  python vm_analyzer.py --id "..." --from 1782913111882 --to 1782999511882 --no-open
"""

import argparse
import sys
import urllib.parse
import webbrowser
from datetime import datetime, timezone

GRAFANA_BASE = "https://asw-main-c9d6bfgzgnbydnae.eus2.grafana.azure.com"
DASHBOARD_UID = "c3624fcf-e0e9-4514-9f82-8961539cfa3f"
DASHBOARD_SLUG = "virtual-machine-analyzer"
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

    # Grafana relative expressions are understood natively by the dashboard.
    if v == "now" or v.startswith("now-") or v.startswith("now+"):
        return v

    # Pure integer -> epoch seconds or milliseconds.
    if v.lstrip("-").isdigit():
        n = int(v)
        if len(v.lstrip("-")) >= 13:
            return str(n)
        return str(n * 1000)

    # Try ISO-8601 (allow trailing Z).
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
    """Normalize the VM identifier used for the `var-_id` template variable.

    Full Azure ARM resource IDs are conventionally lower-cased in this Grafana
    instance, so they are lower-cased here. Other identifiers pass through.
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


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Build and open the Grafana Virtual Machine Analyzer dashboard for an Azure VM.",
    )
    parser.add_argument(
        "--id",
        required=True,
        help="Azure VM ARM ID (/subscriptions/.../virtualMachines/name) or a VM identifier.",
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
        opened = webbrowser.open(url)
        if not opened:
            print("warning: could not launch a browser; open the URL above manually.",
                  file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
