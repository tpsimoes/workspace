"""Kusto-based ACR / Azure Consumption collector for the 22 ASW focus customers.

Replaces the CX Observe DOM scraping / hover-tooltip approach with a direct
Kusto query against `customerdomrptwus3prod.westus3.kusto.windows.net /
customerdomdata`, which is the same underlying data source that powers the
CX Observe UI's "Azure Consumption Units" tile.

Two data sources are available:

1. `WorkloadSearchSummarized` (default, used here)
   - Per-workload TTM/annualized Consumption in ACU
   - One row per (workload × program) — the same workload may appear multiple
     times when it belongs to more than one program (Proactive Resilience,
     S500, Azure Priority 0, etc.). We de-duplicate by (EntityId, EntityName)
     and keep the highest-consumption row.

2. `ACR_Prod_Staging` (per-TPID monthly, for reference)
   - `AzureConsumedRevenue` decimal per `BillingMonth`
   - As of 2026-07 the max BillingMonth in staging is 2025-07 → NOT current

Usage:
    # Run inside Copilot (uses mcp_fabric-rti-mc_kusto_query tool) — this
    # module only holds the query text + processing helpers.
    # For a stand-alone run you need `azure-kusto-data`.

    python _fetch_acr_kusto.py --input raw.json --out snapshot.json
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Focus customer roster (mirrors _scrape_cxobserve_acr_v2.py CUSTOMERS)
# ---------------------------------------------------------------------------
CUSTOMERS: list[tuple[str, str, str, str]] = [
    ("603819",   "SAP_SE_RISE1",     "SAP SE",                    "RISE"),
    ("15902931", "SAP_RISE2",        "SAP",                       "RISE"),
    ("2699441",  "SAP_RISE3",        "SAP RISE tenant 3",         "RISE"),
    ("636846",   "PepsiCo",          "PepsiCo",                   "SAP"),
    ("1719071",  "Woolworths",       "Woolworths Group",          "SAP"),
    ("682354",   "Medline",          "Medline Industries",        "SAP"),
    ("10545209", "Shell",            "Shell",                     "SAP"),
    ("523595",   "Ferrero",          "Ferrero SpA",               "SAP"),
    ("605015",   "Lego",             "LEGO Group",                "SAP"),
    ("1248703",  "Beiersdorf",       "Beiersdorf AG",             "SAP"),
    ("640443",   "Nike",             "Nike",                      "SAP"),
    ("520706",   "Bayer_AG",         "Bayer AG",                  "SAP"),
    ("523272",   "BHP",              "BHP",                       "SAP"),
    ("101552",   "Unilever",         "Unilever",                  "SAP"),
    ("645076",   "McKesson",         "McKesson",                  "SAP"),
    ("643195",   "Halliburton",      "Halliburton",               "SAP"),
    ("940486",   "Petrobras",        "Petrobras",                 "SAP"),
    ("1283152",  "Mt_Sinai",         "Mount Sinai",               "EPIC"),
    ("639155",   "Walgreens",        "Walgreens",                 "SAP"),
    ("18982817", "TJU",              "Thomas Jefferson University","EPIC"),
    ("1833997",  "MichMed",          "University of Michigan",    "EPIC"),
    ("3841220",  "Ascension_Health", "Ascension Health",          "EPIC"),
]

TPID_LIST = [tpid for tpid, *_ in CUSTOMERS]

# ---------------------------------------------------------------------------
# The KQL query — paste into any Kusto client, or run via
# `mcp_fabric-rti-mc_kusto_query` MCP tool.
# ---------------------------------------------------------------------------
KUSTO_CLUSTER = "https://customerdomrptwus3prod.westus3.kusto.windows.net"
KUSTO_DATABASE = "customerdomdata"

KQL_QUERY_ALL_TPIDS = f"""
let TPIDs = dynamic({json.dumps(TPID_LIST)});
WorkloadSearchSummarized
| where TPIDS in (TPIDs)
| project EntityId, EntityName, EntityType, TPIDS,
          SubscriptionsCount, Consumption,
          IndustryName, VerticalName, RegionName
| order by TPIDS asc, Consumption desc
""".strip()

# Optional: monthly ACR per TPID (staging table — currently trails by ~12mo)
KQL_QUERY_MONTHLY_ACR = f"""
ACR_Prod_Staging
| where tpid in ({",".join(TPID_LIST)})
| summarize AzureConsumedRevenue = sum(todouble(AzureConsumedRevenue))
        by tpid, BillingMonth
| order by tpid asc, BillingMonth desc
""".strip()

# ---------------------------------------------------------------------------
# Workload-name matching (word-boundary, same rules as v2 scraper)
# ---------------------------------------------------------------------------
_SAP_PATTERN = re.compile(
    r"(?<![a-zA-Z0-9])(sap|hana|s/?4hana|s/?4|netweaver|bw)(?![a-zA-Z0-9])",
    re.IGNORECASE,
)
_EPIC_PATTERN = re.compile(
    r"(?<![a-zA-Z0-9])(epic)(?![a-zA-Z0-9])",
    re.IGNORECASE,
)


def match_workload(hint: str, name: str) -> bool:
    if not name:
        return False
    if hint == "EPIC":
        return bool(_EPIC_PATTERN.search(name))
    if hint in ("SAP", "RISE"):
        # RISE = whole tenant is SAP — every workload counts; still require SAP
        # tokens to avoid picking up unrelated stuff. RISE totals should be
        # taken at org-level (ACR_Prod_Staging or Consumption sum).
        return bool(_SAP_PATTERN.search(name))
    return False


# ---------------------------------------------------------------------------
# Processing: raw Kusto JSON → per-customer snapshot
# ---------------------------------------------------------------------------
def dedup_workloads(rows: list[dict]) -> list[dict]:
    """Same workload appears in multiple programs → keep max Consumption."""
    best: dict[tuple[str, str], dict] = {}
    for r in rows:
        key = (r["EntityId"], r["EntityName"])
        cur = best.get(key)
        if cur is None or (r["Consumption"] or 0) > (cur["Consumption"] or 0):
            best[key] = r
    return sorted(best.values(), key=lambda r: -(r["Consumption"] or 0))


def process_raw(raw: dict) -> dict:
    cols = [c["ColumnName"] for c in raw["data"]["columns"]]
    idx = {name: i for i, name in enumerate(cols)}
    rows_by_tpid: dict[str, list[dict]] = {}
    for row in raw["data"]["rows"]:
        tpid = row[idx["TPIDS"]]
        d = {name: row[idx[name]] for name in cols}
        rows_by_tpid.setdefault(tpid, []).append(d)

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    customers_out = []
    for tpid, alias, display_name, hint in CUSTOMERS:
        workloads_raw = rows_by_tpid.get(tpid, [])
        workloads = dedup_workloads(workloads_raw)

        # Workloads matching the SAP/EPIC hint
        matches = [w for w in workloads if match_workload(hint, w["EntityName"])]

        # Org-level: pick the largest single row that includes the customer
        # short name / TPID → typically the ACE/AED or S500 org row
        org_candidates = [
            w for w in workloads
            if w["EntityType"] in ("Azure ACE / AED", "S500", "QCC",
                                    "QCC ME Footprint", "Majors")
        ]
        org_row = max(org_candidates, key=lambda w: w["Consumption"] or 0,
                      default=None)

        entry = {
            "tpid": tpid,
            "alias": alias,
            "customer": display_name,
            "workload_hint": hint,
            "org_consumption_acu": (org_row["Consumption"] if org_row else None),
            "org_entity_name": (org_row["EntityName"] if org_row else None),
            "org_entity_type": (org_row["EntityType"] if org_row else None),
            "hint_matched_consumption_acu": sum(
                (w["Consumption"] or 0) for w in matches
            ) if matches else None,
            "hint_matched_workloads": [
                {
                    "name": w["EntityName"],
                    "type": w["EntityType"],
                    "subs": w["SubscriptionsCount"],
                    "consumption_acu": w["Consumption"],
                }
                for w in matches
            ],
            "all_workloads": [
                {
                    "name": w["EntityName"],
                    "type": w["EntityType"],
                    "subs": w["SubscriptionsCount"],
                    "consumption_acu": w["Consumption"],
                    "industry": w["IndustryName"],
                    "vertical": w["VerticalName"],
                    "region": w["RegionName"],
                }
                for w in workloads
            ],
        }
        customers_out.append(entry)

    return {
        "captured_utc": now,
        "source": {
            "cluster": KUSTO_CLUSTER,
            "database": KUSTO_DATABASE,
            "table": "WorkloadSearchSummarized",
            "metric": "Consumption (TTM Azure Consumption Units per workload)",
        },
        "notes": (
            "Consumption is the annualized (TTM) ACU value per workload — "
            "the same value CX Observe shows in the Consumption tile. "
            "This replaces the DOM-hover monthly value collection. Monthly "
            "MoM data is NOT available from this table; ACR_Prod_Staging has "
            "monthly ACR per TPID but as of 2026-07 only extends through "
            "2025-07."
        ),
        "roster_size": len(CUSTOMERS),
        "resolved_count": sum(1 for c in customers_out if c["all_workloads"]),
        "customers": customers_out,
    }


# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Loader-compatible snapshot (for generate_dashboard_v1.py)
#
# Produces a snapshot with the same field names the existing loader reads
# (`acu_this_month`, `prev_month`, `delta_pct`, `acu_display`, `prev_display`)
# BUT the semantics change:
#   • `acu_this_month` now holds the **TTM Consumption** (Trailing Twelve
#     Months) for the customer's SAP / EPIC scope
#   • `prev_month` / `delta_pct` are `null` — this table does not carry
#     month-over-month; the dashboard suppresses the MoM arrow when null
# The snapshot-level `metric_type = "TTM"` field signals downstream code that
# the values are TTM (not monthly) and that the "TTM = Trailing Twelve Months"
# footnote should be shown on the cards.
# ---------------------------------------------------------------------------
def build_loader_snapshot(result: dict, scope: str = "hint_matched") -> dict:
    """Return a dict in the shape `generate_dashboard_v1.load_acr_snapshot`
    expects. `scope` controls which TTM number is used per customer:
       • "hint_matched" — sum of SAP / EPIC-tagged workloads (default)
       • "org"          — the S500 / ACE-AED org-level row
    """
    customers_out = []
    for c in result["customers"]:
        if scope == "org":
            ttm = c.get("org_consumption_acu")
        else:
            ttm = c.get("hint_matched_consumption_acu")
        entry = {
            "tpid": c["tpid"],
            "customer": c["customer"],
            "alias": c["alias"],
            "workload_hint": c["workload_hint"],
            "acu_this_month": int(round(ttm)) if ttm else None,
            "prev_month": None,
            "delta_pct": None,
            "acu_display": _fmt_acu_compact(ttm) if ttm else None,
            "prev_display": None,
            "org_entity_name": c.get("org_entity_name"),
            "hint_matched_workloads": c.get("hint_matched_workloads", []),
        }
        customers_out.append(entry)

    return {
        "metric_type": "TTM",
        "metric_note": "TTM = Trailing Twelve Months",
        "snapshot_month": None,
        "prev_month": None,
        "captured_utc": result["captured_utc"],
        "source": (
            "Kusto: customerdomrptwus3prod.westus3.kusto.windows.net / "
            "customerdomdata / WorkloadSearchSummarized · Consumption (TTM)"
        ),
        "level": f"{scope} (per-customer aggregate across matching workloads)",
        "unit": "ACU (Azure Consumption Units, TTM)",
        "notes": (
            "Values are Trailing Twelve Months (TTM) Azure Consumption Units "
            "per customer. Month-over-month delta is NOT available from this "
            "source; `prev_month` and `delta_pct` are null by design. "
            "Skipped customers (null value): PepsiCo (636846) and Ferrero "
            "(523595) have no workload with 'SAP' in the entity name — "
            "pending CaaS Lead scope confirmation. SAP RISE tenant 3 "
            "(2699441) returned no rows from the source table."
        ),
        "customers": customers_out,
    }


def _fmt_acu_compact(n) -> str:
    if n is None:
        return "—"
    n = float(n)
    if abs(n) >= 1e9:
        return f"{n / 1e9:.2f}B"
    if abs(n) >= 1e6:
        return f"{n / 1e6:.2f}M"
    if abs(n) >= 1e3:
        return f"{n / 1e3:.1f}K"
    return f"{n:.0f}"


# ---------------------------------------------------------------------------
def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True,
                   help="Raw Kusto response JSON (from MCP kusto_query)")
    p.add_argument("--out", required=True,
                   help="Output snapshot JSON path (rich per-workload)")
    p.add_argument("--out-loader", default=None,
                   help="Optional loader-compatible snapshot path "
                        "(consumed by generate_dashboard_v1.py). "
                        "Values are TTM Consumption.")
    p.add_argument("--scope", choices=("hint_matched", "org"),
                   default="hint_matched",
                   help="Which TTM number to write into the loader snapshot "
                        "(default: hint_matched)")
    args = p.parse_args()

    raw = json.loads(Path(args.input).read_text(encoding="utf-8"))
    result = process_raw(raw)
    Path(args.out).write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"[acr-kusto] wrote {args.out}")
    print(f"[acr-kusto] resolved {result['resolved_count']}/"
          f"{result['roster_size']} customers")

    if args.out_loader:
        loader = build_loader_snapshot(result, scope=args.scope)
        Path(args.out_loader).write_text(
            json.dumps(loader, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(f"[acr-kusto] wrote {args.out_loader} (scope={args.scope}, "
              f"metric_type=TTM)")

    for c in result["customers"]:
        wl = len(c["all_workloads"])
        hm = len(c["hint_matched_workloads"])
        org = c["org_consumption_acu"]
        org_s = f"{org/1e6:.2f}M" if org else "—"
        hint_s = (
            f"{c['hint_matched_consumption_acu']/1e6:.2f}M"
            if c["hint_matched_consumption_acu"] else "—"
        )
        print(f"  {c['tpid']:>10s}  {c['alias']:<20s}  wl={wl:>2d}  "
              f"{c['workload_hint']}-match={hm:>2d}  "
              f"org={org_s:>10s}  hint-total={hint_s:>10s}")


if __name__ == "__main__":
    main()
