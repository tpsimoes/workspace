"""ASW CaaS Lead 2.0 - Monthly Business Insight Dashboard V2 (FY-parameterised)
Aligned to FY27 Customer Outreach KPIs sheet:
    "Program- CaaS Lead 2.0 Rollup (Mission Critical, Potential MC & RISE Selected)"

v3.0 (2026-07-20) — FY27 build support
    * Add FY_TAG switch (fy26 / fy27) at CLI: `--fy=fy27` (default) or `--fy=fy26`
    * FY27 pulls Kusto FY-YTD (2026-07-01 onward), 294 cases as of 2026-07-20
    * Insights+_v3 baseline for FY27 is Kusto-derived (PBI dashboard refreshes at month-end)
    * CX Observe (ACR) / SharePoint (Change Events) / ADO Wiki carry FY26 Jun snapshots
      pending end-of-Jul 2026 refresh; labelled "Carried over" in Data Source modal
    * FY-scope banner rendered below header with active data-range and provenance notes
    * Post-render text substitution swaps FY26 labels/filenames to active FY tag

Layout:
    Section 1 - Program-wide Rollup (all 26 focus customers)
    Section 2 - SAP RISE + SAP Native with Mission Critical -> 8 customers (Walgreens removed: not MC-signed)
    Section 3 - SAP Native Mission Critical              -> 7 customers
    Section 4 - EPIC Mission Critical                    -> 9 customers
    Section 5 - SAP RISE Selected (General Motors & CVS) -> 2 customers

Data sources
    Panel A (Support Delivery): Output/asw_fy{26|27}_all_cases.json (Kusto snapshot)
    Panel B (Program Indicators): CaaS Lead Sync PPT extracts + Insights+_v3 (Fabric)
    Panel A CSAT / DSAT / IR% / CPE / Collaborate flag / ACR: mixed provenance —
        see Data Source modal at top-right of the rendered dashboard for details.
"""
from __future__ import annotations
import json
import sys
import math
import html
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"c:\GitHubCopilot\IronMan")

# =============================================================================
# Fiscal Year switch (v3.0 — FY27 support with month-range awareness)
# Override at CLI: `python generate_dashboard_v1.py --fy=fy26`  (or fy27, default)
# All downstream data paths / labels / output filename derive from FY_TAG.
# =============================================================================
FY_TAG = "fy27"   # default; override via CLI --fy=fy26
for _a in sys.argv[1:]:
    if _a.startswith("--fy="):
        FY_TAG = _a.split("=", 1)[1].strip().lower()

# Fiscal year metadata table: FY26 = 2025-07 → 2026-06, FY27 = 2026-07 → 2027-06
_FY_META = {
    "fy26": dict(
        label="FY26", window="2025-07-01 → 2026-06-30 UTC",
        fy_start="2025-07-01", fy_end="2026-07-01",
        cases_json="asw_fy26_all_cases.json",
        csat_json="cpe_fy26_final.json",
        change_events="fy26_change_events.json",
        acr_snapshot="fy26_acr_snapshot.json",
        insights_v3="asw_baseline_insights_v3.json",
        review_summaries="caas_lead_reviews_jun2026.json",
        out_html="caas_lead_monthly_FY26.html",
        review_month_label="Jun 2026 (CaaS Lead Sync)",
    ),
    "fy27": dict(
        label="FY27", window="2026-07-01 → 2027-06-30 UTC",
        fy_start="2026-07-01", fy_end="2027-07-01",
        cases_json="asw_fy27_all_cases.json",
        csat_json="cpe_fy27_final.json",  # FY27 CSAT — 7 surveys as of 2026-07-20 (Kusto)
        change_events="fy27_change_events.json",
        acr_snapshot="fy27_acr_snapshot.json",
        insights_v3="asw_baseline_insights_v3_fy27.json",
        review_summaries="caas_lead_reviews_jul2026.json",
        out_html="caas_lead_monthly_FY27.html",
        review_month_label="Jul 2026 (placeholder — CaaS Lead Sync pending)",
    ),
}
if FY_TAG not in _FY_META:
    raise SystemExit(f"Unknown FY tag: {FY_TAG!r}. Supported: {list(_FY_META.keys())}")
_META = _FY_META[FY_TAG]

DATA_JSON   = ROOT / "Output" / _META["cases_json"]
CSAT_JSON   = ROOT / "Output" / _META["csat_json"]
ROSTER_JSON = ROOT / "Skills" / "asw_caas_lead" / "references" / "asw_roster_fy26.json"
CHANGE_EVENTS_JSON = ROOT / "Skills" / "asw_caas_lead" / "references" / _META["change_events"]  # from ASW_Cx_Changing_Activities xlsx (SharePoint, month-end refresh)
ACR_SNAPSHOT_JSON  = ROOT / "Skills" / "asw_caas_lead" / "references" / _META["acr_snapshot"]    # CX Observe monthly Consumption snapshot
INSIGHTS_V3_JSON   = ROOT / "Skills" / "asw_caas_lead" / "references" / _META["insights_v3"]     # A&I and DTP | Insights+_v3_AIDTP_Fabric — team-wide baseline
WIKI_SUMMARIES_JSON = ROOT / "Skills" / "asw_caas_lead" / "references" / "customer_wiki_summaries.json"  # Know-Me wiki (customer-level, time-independent)
REVIEW_SUMMARIES_JSON = ROOT / "Skills" / "asw_caas_lead" / "references" / _META["review_summaries"]  # CaaS Lead PPT extracts (Key Updates / Service Delivery / Reminders)
OUT_HTML    = ROOT / "Output" / _META["out_html"]

# Kusto source (documented in §7 of SKILL.md — shown in header for provenance)
KUSTO_CLUSTER = "supportrptwus3prod.westus3.kusto.windows.net"
KUSTO_DB      = "KPISupportData"
KUSTO_TABLE   = "AllCloudsSupportIncidentWithReferenceModelVNext"
FY_LABEL      = _META["label"]
FY_WINDOW     = _META["window"]
FY_START_ISO  = _META["fy_start"]
FY_END_ISO    = _META["fy_end"]
REVIEW_MONTH_LABEL = _META["review_month_label"]

# Manager display names (from Skills/asw_caas_lead/references/asw_roster_fy26.json)
MANAGER_DISPLAY = {
    "jacobw":  "Jacob Wang",
    "kbeller": "Kirk Beller",
    "nasaggu": "Narendra Saggu",
    "noambi":  "Noam Binyamini",
    "dhanat":  "Dhananjay Tripathi",
    "xinxia":  "Xin Xia",
}

# =============================================================================
# Focus Customer Master (26 customers, from FY27 Customer Outreach KPIs sheet)
# section: "R" = SAP RISE (MC/MC Pipeline)
#          "N" = SAP Native Mission Critical
#          "E" = EPIC Mission Critical
#          "S" = SAP RISE Selected (GM & CVS)
# TPIDs verified against Output/asw_fy26_all_cases.json
# =============================================================================
FOCUS = [
    # ── Section 2: SAP RISE (MC / MC Pipeline) ──────────────────────────────
    # SAP RISE tenant — SAP-owned TPIDs (603819 SAP SE, 15902931 SAP, 2699441).
    # Not all SAP RISE cases land in the RISE Escalations queue — some flow through
    # OneSupport System Holding, MSaaS China Epic/SAP, and Native Escalations — so
    # we match by TPID list (any SAP tenant) rather than by queue name.
    dict(section="R", zone=0, workload="RISE", customer="SAP RISE (tenant)", tpid=["603819", "15902931", "2699441"], lead="SAP CSI Team",              stage="Phase 4", ca=True,  ai=False, wiki=True,  ss=0, ce=0, ee=0, mc="Mission Critical (Renew)"),
    dict(section="R", zone=2, workload="SAP",  customer="PepsiCo",   tpid=636846,   lead="Ivan / Lakshma",            stage="Phase 4", ca=True,  ai=False, wiki=False, ss=0, ce=0, ee=0, mc="Mission Critical (Renew)"),
    dict(section="R", zone=1, workload="SAP",  customer="Woolworths", tpid=1719071,  lead="Jake Lin / Priya Kumar",    stage="Phase 4", ca=True,  ai=True,  wiki=False, ss=1, ce=5, ee=0, mc="Mission Critical (Renew)"),
    dict(section="R", zone=2, workload="SAP",  customer="Medline",   tpid=682354,   lead="Shiva Addala / Alexander",  stage="Phase 4", ca=True,  ai=False, wiki=False, ss=1, ce=0, ee=0, mc="Mission Critical (Renew)"),
    dict(section="R", zone=2, workload="SAP",  customer="Shell",     tpid=10545209, lead="Lucas Andreazzi",           stage="Phase 2", ca=False, ai=False, wiki=False, ss=0, ce=0, ee=0, mc="Mission Critical"),
    dict(section="R", zone=2, workload="SAP",  customer="Ferrero",   tpid=523595,   lead="Ruben Sousa",               stage="Phase 4", ca=True,  ai=True,  wiki=False, ss=1, ce=1, ee=0, mc="Mission Critical"),
    dict(section="R", zone=2, workload="SAP",  customer="Lego",      tpid=605015,   lead="Pedro Mota",                stage="Phase 2", ca=False, ai=False, wiki=False, ss=0, ce=0, ee=0, mc="Mission Critical"),
    dict(section="R", zone=1, workload="SAP",  customer="Beiersdorf", tpid=1248703, lead="Venkat / Joao Goncalves",   stage="Phase 1", ca=False, ai=False, wiki=False, ss=0, ce=0, ee=0, mc="Mission Critical"),

    # ── Section 3: SAP Native Mission Critical (Potential MC / High Volume) ─
    dict(section="N", zone=2, workload="SAP",  customer="Nike",        tpid=640443,  lead="Alexander",                 stage="Phase 4", ca=False, ai=False, wiki=False, ss=0, ce=0, ee=0, mc="Non-SFMC"),
    dict(section="N", zone=1, workload="SAP",  customer="Bayer AG",    tpid=520706,  lead="Dante / Farhana",           stage="Phase 4", ca=True,  ai=True,  wiki=False, ss=0, ce=0, ee=0, mc="Non-SFMC"),
    dict(section="N", zone=1, workload="SAP",  customer="BHP",         tpid=523272,  lead="Priya Kumar / Jake Lin",    stage="Phase 4", ca=True,  ai=False, wiki=True,  ss=0, ce=4, ee=0, mc="Non-SFMC"),
    dict(section="N", zone=1, workload="SAP",  customer="Unilever",    tpid=101552,  lead="João Carvalho / Shrouq",    stage="Phase 4", ca=True,  ai=True,  wiki=False, ss=2, ce=0, ee=0, mc="Non-SFMC"),
    dict(section="N", zone=2, workload="SAP",  customer="McKesson",    tpid=645076,  lead="Katherine",                 stage="Phase 4", ca=False, ai=False, wiki=False, ss=1, ce=0, ee=0, mc="Non-SFMC"),
    dict(section="N", zone=2, workload="SAP",  customer="Halliburton", tpid=643195,  lead="Steven Herrera",            stage="Phase 2", ca=False, ai=False, wiki=False, ss=0, ce=0, ee=0, mc="Non-SFMC"),
    dict(section="N", zone=2, workload="SAP",  customer="Petrobras",   tpid=940486,  lead="Lucas Andreazzi",           stage="Phase 4 (dropping)", ca=True, ai=False, wiki=False, ss=1, ce=1, ee=0, mc="Non-SFMC (exiting Azure)"),
    dict(section="N", zone=2, workload="EPIC", customer="Mt. Sinai",   tpid=1283152, lead="Tanner King",               stage="Phase 3", ca=False, ai=False, wiki=False, ss=0, ce=0, ee=0, mc="Non-SFMC (exiting Azure)"),
    dict(section="N", zone=2, workload="SAP",  customer="Walgreens",   tpid=639155,  lead="TBD",                       stage="Phase 4", ca=False, ai=False, wiki=False, ss=0, ce=0, ee=0, mc="MC Pipeline"),

    # ── Section 4: EPIC Mission Critical ────────────────────────────────────
    dict(section="E", zone=2, workload="EPIC", customer="TJU",                   tpid=18982817, lead="Angelica Arce",     stage="Phase 4", ca=True,  ai=False, wiki=False, ss=0, ce=4, ee=0, mc="Yes"),
    dict(section="E", zone=2, workload="EPIC", customer="MichMed",               tpid=1833997,  lead="Tanner King",       stage="Phase 2", ca=False, ai=False, wiki=False, ss=0, ce=0, ee=0, mc="Yes"),
    dict(section="E", zone=2, workload="EPIC", customer="Univ. Kentucky",        tpid=1733740,  lead="Didier Ambroise",   stage="Phase 4", ca=True,  ai=True,  wiki=False, ss=0, ce=0, ee=0, mc="Yes"),
    dict(section="E", zone=2, workload="EPIC", customer="Ascension Health",      tpid=3841220,  lead="Didier Ambroise",   stage="Phase 4", ca=True,  ai=True,  wiki=False, ss=0, ce=2, ee=0, mc="Yes"),
    dict(section="E", zone=2, workload="EPIC", customer="UTMB",                  tpid=680928,   lead="Elliott Johnston",  stage="Phase 1", ca=False, ai=False, wiki=False, ss=0, ce=0, ee=0, mc="Yes"),
    dict(section="E", zone=2, workload="EPIC", customer="Brown University",      tpid=1137436,  lead="Brian Wurzbacher",  stage="Phase 1", ca=False, ai=False, wiki=False, ss=0, ce=0, ee=0, mc="Yes"),
    dict(section="E", zone=2, workload="EPIC", customer="Cone Health",           tpid=5760332,  lead="João Gonçalves",    stage="Phase 1", ca=False, ai=False, wiki=False, ss=0, ce=0, ee=0, mc="Yes"),
    dict(section="E", zone=2, workload="EPIC", customer="Children's Hosp Phila", tpid=2077544,  lead="João Gonçalves",    stage="Phase 1", ca=False, ai=False, wiki=False, ss=0, ce=0, ee=0, mc="Yes"),

    # ── Section 5: SAP RISE Selected (GM & CVS) ─────────────────────────────
    dict(section="S", zone=2, workload="RISE", customer="General Motors", tpid=None, lead="Siddharth Sharma", stage="Phase 2", ca=False, ai=False, wiki=False, ss=0, ce=0, ee=0, mc="Non-SFMC"),
    dict(section="S", zone=2, workload="RISE", customer="CVS",            tpid=None, lead="Sheetal Joyce",    stage="Phase 2", ca=False, ai=False, wiki=False, ss=0, ce=0, ee=0, mc="Non-SFMC"),
    dict(section="S", zone=2, workload="RISE", customer="SAP RISE",       tpid=2688441, lead="TBD",           stage="Phase 1", ca=False, ai=False, wiki=False, ss=0, ce=0, ee=0, mc="Non-SFMC", primary_queue="MSaaS Azure SAP RISE Escalations"),
]

SECTIONS = {
    "R": dict(title="Section 2 · SAP RISE + SAP Native with Mission Critical",
              subtitle="SAP customers (RISE tenant + Native workloads) with Mission Critical contract active",
              color="#0078d4"),
    "E": dict(title="Section 3 · EPIC — Mission Critical",
              subtitle="Healthcare (Epic on Azure) — active MC contracts + onboarding pipeline",
              color="#28a745"),
    "N": dict(title="Section 4 · SAP Native/Epic Potential MC",
              subtitle="High-volume SAP-Native + Epic customers without signed MC (Potential MC / Non-SFMC today)",
              color="#f59e0b"),
    "S": dict(title="Section 5 · SAP RISE Selected",
              subtitle="Newly onboarded RISE customers requested by CSI team (may have no FY26 case data yet)",
              color="#6f42c1"),
}


# =============================================================================
# Case metrics
# =============================================================================
def parse_dt(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def compute_panel_a(cases: list[dict], tpid, queue: str | None = None) -> dict:
    """Compute Panel A metrics.
    tpid may be:
        - None      → zero row (unless queue is set)
        - int / str → single TPID match
        - list/tuple→ match ANY TPID in the list (multi-tenant customer)
    queue: optional exact queue-name filter, ANDed with tpid.
    """
    if tpid is None and queue is None:
        return dict(vol=0, closed=0, avg_dtc=None, pct_close_7=None,
                    critsit=0, top_l2=[], top_l3=[], dtcs=[])
    tpid_set: set[str] | None
    if tpid is None:
        tpid_set = None
    elif isinstance(tpid, (list, tuple, set)):
        tpid_set = {str(t) for t in tpid}
    else:
        tpid_set = {str(tpid)}
    def _match(r: dict) -> bool:
        if queue is not None:
            if (r.get("CurrentQueueName") or "") != queue:
                return False
        if tpid_set is not None:
            if str(r.get("Customer_TPID") or "") not in tpid_set:
                return False
        return True
    rows = [r for r in cases if _match(r)]
    vol = len(rows)
    dtcs: list[float] = []
    critsit = 0
    l2_cnt: Counter = Counter()
    l3_cnt: Counter = Counter()
    for r in rows:
        # IsCritSit is stored as string "True"/"False" in the JSON snapshot, not as bool
        if str(r.get("IsCritSit") or "").lower() == "true":
            critsit += 1
        if r.get("SapSupportPathL2"):
            l2_cnt[r["SapSupportPathL2"]] += 1
        if r.get("SapSupportPathL3"):
            l3_cnt[r["SapSupportPathL3"]] += 1
        c = parse_dt(r.get("CreatedDateTime"))
        cl = parse_dt(r.get("ClosedDateTime"))
        if c and cl and cl > c:
            dtcs.append((cl - c).total_seconds() / 86400.0)
    closed = len(dtcs)
    avg_dtc = round(sum(dtcs) / len(dtcs), 1) if dtcs else None
    pct_7 = round(100.0 * sum(1 for d in dtcs if d < 7) / len(dtcs), 1) if dtcs else None
    return dict(
        vol=vol,
        closed=closed,
        avg_dtc=avg_dtc,
        pct_close_7=pct_7,
        critsit=critsit,
        top_l2=[(k, v) for k, v in l2_cnt.most_common(3)],
        top_l3=[(k, v) for k, v in l3_cnt.most_common(3)],
        dtcs=dtcs,
    )


def rollup(rows: list[dict]) -> dict:
    total_vol = sum(r["vol"] for r in rows)
    total_closed = sum(r["closed"] for r in rows)
    total_critsit = sum(r["critsit"] for r in rows)
    all_dtcs = [d for r in rows for d in r["dtcs"]]
    avg_dtc = round(sum(all_dtcs) / len(all_dtcs), 1) if all_dtcs else None
    pct_7 = round(100.0 * sum(1 for d in all_dtcs if d < 7) / len(all_dtcs), 1) if all_dtcs else None
    return dict(vol=total_vol, closed=total_closed, avg_dtc=avg_dtc, pct_close_7=pct_7, critsit=total_critsit)


def compute_asw_baseline(cases: list[dict]) -> dict:
    """Compute FY26 ASW-wide baseline metrics across the full case snapshot.
    Not limited to focus customers — this is the denominator for coverage %.
    """
    vol = len(cases)
    dtcs = []
    critsit = 0
    for r in cases:
        if str(r.get("IsCritSit") or "").lower() == "true":
            critsit += 1
        c = parse_dt(r.get("CreatedDateTime"))
        cl = parse_dt(r.get("ClosedDateTime"))
        if c and cl and cl > c:
            dtcs.append((cl - c).total_seconds() / 86400.0)
    return dict(
        vol=vol,
        closed=len(dtcs),
        avg_dtc=round(sum(dtcs) / len(dtcs), 2) if dtcs else None,
        pct_close_7=round(100.0 * sum(1 for d in dtcs if d < 7) / len(dtcs), 1) if dtcs else None,
        critsit=critsit,
        distinct_customers=len({str(r.get("Customer_TPID") or "") for r in cases}),
        distinct_engineers=len({(r.get("AgentAlias") or "") for r in cases if r.get("AgentAlias")}),
    )


def load_roster(path: Path = ROSTER_JSON) -> dict[str, str]:
    """Return alias -> manager_alias mapping (skips header row)."""
    if not path.exists():
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    return {r["AgentAlias"]: r["ManagerAlias"]
            for r in raw
            if r.get("AgentAlias") and r["AgentAlias"] != "AgentAlias"}


def compute_manager_rollup(cases: list[dict], roster: dict[str, str],
                            focus_tpids: set[str] | None = None) -> list[dict]:
    """Group focus-customer cases by manager. Returns list of dicts sorted by volume desc."""
    scoped = cases if focus_tpids is None else \
             [r for r in cases if str(r.get("Customer_TPID") or "") in focus_tpids]
    mgr_cases: dict[str, list[dict]] = {}
    for r in scoped:
        alias = r.get("AgentAlias") or ""
        mgr = roster.get(alias)
        if not mgr:
            continue
        mgr_cases.setdefault(mgr, []).append(r)
    out = []
    for mgr, rows in mgr_cases.items():
        dtcs = []
        for r in rows:
            c = parse_dt(r.get("CreatedDateTime"))
            cl = parse_dt(r.get("ClosedDateTime"))
            if c and cl and cl > c:
                dtcs.append((cl - c).total_seconds() / 86400.0)
        engs_all = {a for a, m in roster.items() if m == mgr}
        engs_active = {r.get("AgentAlias") for r in rows if r.get("AgentAlias")}
        out.append(dict(
            manager_alias=mgr,
            manager_name=MANAGER_DISPLAY.get(mgr, mgr),
            vol=len(rows),
            closed=len(dtcs),
            avg_dtc=round(sum(dtcs)/len(dtcs), 1) if dtcs else None,
            pct_7=round(100.0 * sum(1 for d in dtcs if d < 7) / len(dtcs), 1) if dtcs else None,
            engineers_active=len(engs_active),
            engineers_total=len(engs_all),
        ))
    return sorted(out, key=lambda x: -x["vol"])


def cohort_engineers(cases: list[dict], cohort_tpids: set[str]) -> int:
    """Distinct engineers touching a cohort's cases."""
    if not cohort_tpids:
        return 0
    engs = {r.get("AgentAlias") for r in cases
            if str(r.get("Customer_TPID") or "") in cohort_tpids and r.get("AgentAlias")}
    return len(engs)


# =============================================================================
# CSAT (from cpe_fy26_final.json — 170 FY26 ASW survey responses)
# =============================================================================
def load_csat(path: Path = CSAT_JSON) -> dict[str, list[int]]:
    """Return TPID -> list[int] of CSAT scores. Skips rows with empty score."""
    if not path.exists():
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    out: dict[str, list[int]] = {}
    for s in raw:
        sc = s.get("TotalCustomerSATScore")
        tpid = str(s.get("Customer_TPID") or "")
        if not tpid or sc is None or sc == "":
            continue
        try:
            out.setdefault(tpid, []).append(int(sc))
        except (ValueError, TypeError):
            pass
    return out


def csat_stats(csat: dict[str, list[int]], tpid) -> dict:
    """Aggregate CSAT for a single TPID (int/str) or a multi-TPID list.
    Returns dict(n, avg, dsat) or dict(n=0, avg=None, dsat=0) when no surveys.
    """
    if tpid is None:
        return dict(n=0, avg=None, dsat=0)
    if isinstance(tpid, (list, tuple, set)):
        keys = [str(t) for t in tpid]
    else:
        keys = [str(tpid)]
    scores: list[int] = []
    for k in keys:
        scores.extend(csat.get(k, []))
    if not scores:
        return dict(n=0, avg=None, dsat=0)
    return dict(
        n=len(scores),
        avg=round(sum(scores) / len(scores), 2),
        dsat=sum(1 for x in scores if x <= 3),
    )


def csat_rollup_focus(csat: dict[str, list[int]], focus: list[dict]) -> dict:
    """Aggregate CSAT across all focus customers."""
    tpid_set: set[str] = set()
    for c in focus:
        t = c["tpid"]
        if t is None:
            continue
        if isinstance(t, (list, tuple, set)):
            tpid_set.update(str(x) for x in t)
        else:
            tpid_set.add(str(t))
    scores: list[int] = []
    for k in tpid_set:
        scores.extend(csat.get(k, []))
    if not scores:
        return dict(n=0, avg=None, dsat=0, customers_with_survey=0)
    customers_with_survey = sum(
        1 for c in focus
        if csat_stats(csat, c["tpid"])["n"] > 0
    )
    return dict(
        n=len(scores),
        avg=round(sum(scores) / len(scores), 2),
        dsat=sum(1 for x in scores if x <= 3),
        customers_with_survey=customers_with_survey,
    )


def csat_asw_total(csat: dict[str, list[int]]) -> dict:
    """Aggregate CSAT across ALL ASW cases (all TPIDs present in the CSAT dataset)."""
    scores: list[int] = [x for lst in csat.values() for x in lst]
    if not scores:
        return dict(n=0, avg=None, dsat=0)
    return dict(
        n=len(scores),
        avg=round(sum(scores) / len(scores), 2),
        dsat=sum(1 for x in scores if x <= 3),
    )


def load_change_events(path: Path = CHANGE_EVENTS_JSON) -> dict:
    """Load FY26 Change Event aggregates extracted from the annual xlsx.
    Returns a dict with keys: total_tracked, completed, cancelled, customers_with_event.
    Returns None-like structure if file missing so render can fall back to NA.
    """
    if not path.exists():
        return dict(total_tracked=None, completed=None, cancelled=None, customers_with_event=None)
    raw = json.loads(path.read_text(encoding="utf-8"))
    return raw.get("totals", {})


# ---------------------------------------------------------------------------
# ACR snapshot loader (CX Observe Consumption tile, org-level)
# ---------------------------------------------------------------------------
def load_acr_snapshot(path: Path = ACR_SNAPSHOT_JSON) -> dict:
    """Return {'meta': {...}, 'by_tpid': {tpid_str: entry, ...}}.
    Entry has keys: acu_this_month, prev_month, delta_pct, acu_display, prev_display.
    Missing/unavailable customers are silently skipped (their tpid maps to None entry).
    """
    if not path.exists():
        return {"meta": {}, "by_tpid": {}}
    raw = json.loads(path.read_text(encoding="utf-8"))
    by_tpid: dict[str, dict] = {}
    for row in raw.get("customers", []):
        tp = str(row.get("tpid"))
        by_tpid[tp] = row
    return {"meta": {k: raw.get(k) for k in ("snapshot_month", "prev_month", "captured_utc", "unit", "level", "source", "notes", "metric_type", "metric_note")},
            "by_tpid": by_tpid}


def load_insights_v3_baseline(path: Path = INSIGHTS_V3_JSON) -> dict:
    """Return the Insights+_v3_AIDTP_Fabric snapshot for the ASW-wide baseline KPIs.
    Values with `value == null` mean 'not read from Insights+_v3 — caller should fall back to KPISupportData'.
    Schema: {'meta': {...}, 'kpis': {kpi_name: {'value': ..., 'source': 'Insights+_v3' | 'KPISupportData', ...}}}.
    """
    if not path.exists():
        return {"meta": {}, "kpis": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def load_wiki_summaries(path: Path = WIKI_SUMMARIES_JSON) -> dict:
    """Return the Know-Me wiki summary index for focus customers.
    Schema: {'meta': {...}, 'by_key': {tpid_key: {highlights: [...], last_updated, has_content, ...}}}.
    If the file is missing, return an empty scaffold — dashboard still renders (Wiki tag will show 'pending fetch').
    """
    if not path.exists():
        return {"meta": {}, "by_key": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def load_review_summaries(path: Path = REVIEW_SUMMARIES_JSON) -> dict:
    """Return the CaaS Lead monthly review summary index.
    Schema: {'meta': {...}, 'by_key': {tpid_key: {customer, tpid, pptx_name, key_updates: [...], service_delivery: [...], reminders: [...]}}}.
    If the file is missing, return an empty scaffold — the customer name will just render as plain text (no clickable link).
    """
    if not path.exists():
        return {"meta": {}, "by_key": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def _fmt_wiki_date(iso: str | None) -> str:
    """Format an ISO date (YYYY-MM-DD or full ISO-8601) as 'Mon DD, YYYY' to match
    the ADO wiki UI's <time class='last-updated-date'> display."""
    if not iso:
        return "unknown"
    s = str(iso).strip()
    # Trim to date portion
    for sep in ("T", " "):
        if sep in s:
            s = s.split(sep, 1)[0]
            break
    try:
        return datetime.strptime(s, "%Y-%m-%d").strftime("%b %d, %Y")
    except Exception:
        return str(iso)


def _fmt_month_label(iso_month: str | None) -> str:
    """Convert 'YYYY-MM' or 'YYYY-MM-DD' to a short month label like 'Jun 2026'.
    Used for the ACR snapshot's Current / Previous month annotations."""
    if not iso_month:
        return ""
    s = str(iso_month).strip()
    for sep in ("T", " "):
        if sep in s:
            s = s.split(sep, 1)[0]
            break
    for fmt in ("%Y-%m", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt).strftime("%b %Y")
        except Exception:
            continue
    return str(iso_month)


def _fmt_acu(n) -> str:
    """Format an ACR (USD) number to compact display (e.g. 40_110_000 -> '40.11M').
    Function name is legacy (originally ACU); values represent USD since v2.13.0."""
    if n is None:
        return "—"
    n = float(n)
    if abs(n) >= 1_000_000_000:
        return f"{n / 1_000_000_000:.2f}B"
    if abs(n) >= 1_000_000:
        return f"{n / 1_000_000:.2f}M"
    if abs(n) >= 1_000:
        return f"{n / 1_000:.1f}K"
    return f"{n:.0f}"


def _attach_month_labels(entry: dict, meta: dict | None) -> dict:
    """Attach cur_month_label / prev_month_label to an ACR entry from snapshot meta.
    Consumers (customer-card tooltips, JS modal, sub-text lines) read these labels
    instead of hardcoding month names — so a new monthly refresh doesn't need code changes."""
    m = meta or {}
    entry["cur_month_label"]  = _fmt_month_label(m.get("snapshot_month"))
    entry["prev_month_label"] = _fmt_month_label(m.get("prev_month"))
    return entry


def acr_for_focus(f: dict, acr_map: dict, meta: dict | None = None) -> dict | None:
    """Given a FOCUS entry (single or list tpid), return an aggregated ACR entry (in USD).
    Returns None when no captured data exists for this customer.
    When `meta` is supplied, the returned dict also carries cur_month_label / prev_month_label
    (e.g. 'Jun 2026' / 'May 2026') for downstream display."""
    tp = f.get("tpid")
    if tp is None:
        return None
    tpids = [str(t) for t in tp] if isinstance(tp, (list, tuple, set)) else [str(tp)]
    cur_sum = 0
    prev_sum = 0
    have_any = False
    for t in tpids:
        e = acr_map.get(t)
        if not e or e.get("acu_this_month") is None:
            continue
        cur_sum += int(e["acu_this_month"])
        prev_sum += int(e.get("prev_month") or 0)
        have_any = True
    if not have_any:
        return None
    delta_pct = round(100.0 * (cur_sum - prev_sum) / prev_sum, 2) if prev_sum else None
    return _attach_month_labels({
        "acu_this_month": cur_sum,
        "prev_month": prev_sum if prev_sum else None,
        "delta_pct": delta_pct,
        "acu_display": _fmt_acu(cur_sum),
        "prev_display": _fmt_acu(prev_sum) if prev_sum else "—",
    }, meta)


def sum_section_acr(customers: list[dict], acr_map: dict, meta: dict | None = None) -> dict | None:
    """Sum ACR (USD) for a list of FOCUS entries. Returns None if no data at all.
    When `meta` is supplied, attaches cur_month_label / prev_month_label to the result."""
    cur_sum = 0
    prev_sum = 0
    covered = 0
    total = len(customers)
    for f in customers:
        e = acr_for_focus(f, acr_map, meta)
        if not e:
            continue
        cur_sum += e["acu_this_month"]
        prev_sum += e.get("prev_month") or 0
        covered += 1
    if covered == 0:
        return None
    delta_pct = round(100.0 * (cur_sum - prev_sum) / prev_sum, 2) if prev_sum else None
    return _attach_month_labels({
        "acu_this_month": cur_sum,
        "prev_month": prev_sum if prev_sum else None,
        "delta_pct": delta_pct,
        "acu_display": _fmt_acu(cur_sum),
        "prev_display": _fmt_acu(prev_sum) if prev_sum else "—",
        "covered": covered,
        "total": total,
    }, meta)


def acr_trend_html(delta_pct) -> str:
    """Return small HTML arrow + delta% for MoM trend. Green up / red down / grey flat."""
    if delta_pct is None:
        return ''
    if delta_pct > 0.5:
        return (f'<span style="color:#28a745;margin-left:4px;font-size:.85em;font-weight:600" '
                f'title="MoM up">▲ +{delta_pct:.2f}%</span>')
    if delta_pct < -0.5:
        return (f'<span style="color:#dc3545;margin-left:4px;font-size:.85em;font-weight:600" '
                f'title="MoM down">▼ {delta_pct:.2f}%</span>')
    return (f'<span style="color:#94a3b8;margin-left:4px;font-size:.85em;font-weight:600" '
            f'title="MoM flat (±0.5%)">▬ {delta_pct:+.2f}%</span>')


def acr_delta_abs_html(cur, prev) -> str:
    """Return absolute delta in USD (e.g. '+330K' or '-2.04M') for MoM change."""
    if cur is None or prev is None:
        return ''
    diff = cur - prev
    sign = '+' if diff >= 0 else '−'
    return f'{sign}{_fmt_acu(abs(diff))}'


# =============================================================================
# Drill-down (raw-data) dataset builder
# =============================================================================
import re as _re

def _slug(name: str) -> str:
    return _re.sub(r'[^a-z0-9]+', '-', str(name).lower()).strip('-') or 'x'


def _tpid_key(f: dict) -> str:
    t = f.get("tpid")
    if t is None:
        return f'noTPID-{_slug(f["customer"])}'
    if isinstance(t, (list, tuple, set)):
        return "|".join(str(x) for x in t)
    return str(t)


def _case_row(r: dict) -> dict:
    """Slim case row for drill (subset of fields, DTC pre-computed)."""
    c = parse_dt(r.get("CreatedDateTime"))
    cl = parse_dt(r.get("ClosedDateTime"))
    dtc = None
    if c and cl and cl > c:
        dtc = round((cl - c).total_seconds() / 86400.0, 2)
    return {
        "id":   r.get("IncidentId") or "",
        "cust": r.get("Customer_TPName") or "",
        "tpid": r.get("Customer_TPID") or "",
        "eng":  r.get("AgentAlias") or "",
        "created": (r.get("CreatedDateTime") or "")[:19],
        "closed":  (r.get("ClosedDateTime")  or "")[:19] if r.get("ClosedDateTime") else "",
        "queue":   r.get("CurrentQueueName") or "",
        "sev":     r.get("InitialSeverity") or "",
        "crit":    1 if str(r.get("IsCritSit") or "").lower() == "true" else 0,
        "l2":      r.get("SapSupportPathL2") or "",
        "l3":      r.get("SapSupportPathL3") or "",
        "svc":     r.get("ServiceName") or "",
        "region":  r.get("RegionName") or "",
        "dtc":     dtc,
    }


def _csat_row(r: dict) -> dict:
    return {
        "id":      r.get("IncidentId") or "",
        "cust":    r.get("Customer_TPName") or "",
        "tpid":    r.get("Customer_TPID") or "",
        "score":   r.get("TotalCustomerSATScore"),
        "closed":  (r.get("ClosedDateTime") or "")[:19] if r.get("ClosedDateTime") else "",
        "eng":     r.get("AgentAlias") or "",
        "engname": r.get("AgentName") or "",
        "svc":     r.get("ServiceName") or "",
        "region":  r.get("RegionName") or "",
        "verbatim":(r.get("SurveyVerbatims") or "")[:400],
    }


def build_drill_dataset(cases: list[dict], csat_raw: list[dict],
                        focus: list[dict], acr_snapshot: dict) -> dict:
    """Build the drill payload for JS. Keyed by tpid-key, section-letter (SECTION_R…),
    and 'PROGRAM' for org-wide rollup. Each entry has: label, tpid, cases[], csat[], acr{}."""
    acr_map = acr_snapshot.get("by_tpid", {})
    acr_meta = acr_snapshot.get("meta", {})
    entries: dict[str, dict] = {}

    # index cases + surveys by TPID once
    cases_by_tpid: dict[str, list[dict]] = {}
    for r in cases:
        t = str(r.get("Customer_TPID") or "")
        if not t: continue
        cases_by_tpid.setdefault(t, []).append(r)
    csat_by_tpid: dict[str, list[dict]] = {}
    for r in csat_raw:
        t = str(r.get("Customer_TPID") or "")
        if not t: continue
        csat_by_tpid.setdefault(t, []).append(r)

    def _collect_tpids(f):
        t = f.get("tpid")
        if t is None: return []
        if isinstance(t, (list, tuple, set)): return [str(x) for x in t]
        return [str(t)]

    # per-customer
    for f in focus:
        key = _tpid_key(f)
        tpids = _collect_tpids(f)
        crows = []; srows = []
        for t in tpids:
            crows.extend(cases_by_tpid.get(t, []))
            srows.extend(csat_by_tpid.get(t, []))
        acr_entry = acr_for_focus(f, acr_map, acr_meta)
        entries[key] = {
            "label":   f["customer"],
            "tpid":    " / ".join(tpids) if tpids else "—",
            "section": f["section"],
            "workload": f["workload"],
            "lead":    f["lead"],
            "stage":   f["stage"],
            "cases":   [_case_row(r) for r in crows],
            "csat":    [_csat_row(r) for r in srows],
            "acr":     acr_entry,
        }

    # per-section rollup
    for letter in ("R", "N", "E", "S"):
        subset = [f for f in focus if f["section"] == letter]
        all_tpids: list[str] = []
        for f in subset: all_tpids.extend(_collect_tpids(f))
        crows = [r for t in all_tpids for r in cases_by_tpid.get(t, [])]
        srows = [r for t in all_tpids for r in csat_by_tpid.get(t, [])]
        acr_total = sum_section_acr(subset, acr_map, acr_meta)
        entries[f"SECTION_{letter}"] = {
            "label":  f"Section {letter} · {SECTIONS[letter]['title']}" if letter in SECTIONS else f"Section {letter}",
            "tpid":   f"{len(subset)} customers",
            "cases":  [_case_row(r) for r in crows],
            "csat":   [_csat_row(r) for r in srows],
            "acr":    acr_total,
        }

    # program-wide (all focus customers)
    all_tpids: list[str] = []
    for f in focus: all_tpids.extend(_collect_tpids(f))
    crows = [r for t in all_tpids for r in cases_by_tpid.get(t, [])]
    srows = [r for t in all_tpids for r in csat_by_tpid.get(t, [])]
    entries["PROGRAM"] = {
        "label":  "Program · CaaS Lead 2.0 (all focus customers)",
        "tpid":   f"{len(focus)} customers",
        "cases":  [_case_row(r) for r in crows],
        "csat":   [_csat_row(r) for r in srows],
        "acr":    sum_section_acr(focus, acr_map, acr_meta),
    }

    # ASW baseline (whole snapshot)
    entries["ASW_BASELINE"] = {
        "label":  "ASW FY26 Baseline (all cases)",
        "tpid":   f"{len({str(r.get('Customer_TPID') or '') for r in cases})} distinct TPIDs",
        "cases":  [_case_row(r) for r in cases],
        "csat":   [_csat_row(r) for r in csat_raw],
        "acr":    None,
    }
    return entries


def drill_span(key: str, kpi: str, inner_html: str, extra_class: str = "") -> str:
    """Wrap an inner HTML snippet in a clickable drill-KPI span."""
    cls = ("drill-kpi " + extra_class).strip()
    return (f'<span class="{cls}" data-drill-key="{key}" data-drill-kpi="{kpi}" '
            f'title="Click to view raw data">{inner_html}</span>')


def wiki_tag(key: str, wiki_entry: dict | None) -> str:
    """Render the clickable Wiki tag for a customer card.
    Displays a status glyph + short label; on click opens the wiki modal populated
    from `customer_wiki_summaries.json`. Never fabricates content.
    """
    if wiki_entry is None:
        # No entry in the summary JSON — treat as pending
        label = "Wiki … pending"
        title = "Wiki summary not indexed yet — see fetch_customer_wikis.py"
        color = "#94a3b8"
    else:
        n = len(wiki_entry.get("highlights") or [])
        has = wiki_entry.get("has_content")
        if n > 0:
            label = f"Wiki ✓ {n} note{'s' if n != 1 else ''}"
            last = _fmt_wiki_date(wiki_entry.get("last_updated"))
            title = f"Click to view {n} support-profile highlight{'s' if n != 1 else ''} · last updated {last}"
            color = "#0369a1"
        elif has is False:
            label = "Wiki — no notes"
            title = wiki_entry.get("notes") or "No Know-Me wiki content available for this customer"
            color = "#94a3b8"
        else:
            label = "Wiki … pending"
            title = "Wiki content pending fetch — run scripts/fetch_customer_wikis.py"
            color = "#94a3b8"
    # HTML-escape the title (may contain quotes from notes)
    safe_title = title.replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
    return (
        f'<span class="wiki-tag" data-wiki-key="{key}" title="{safe_title}" '
        f'style="font-size:.66rem;color:{color};cursor:pointer;text-decoration:underline dotted;'
        f'text-underline-offset:2px">{label}</span>'
    )



# =============================================================================
# HTML rendering
# =============================================================================
CSS = """
:root {
    --green:#28a745; --yellow:#ffc107; --red:#dc3545; --blue:#0078d4; --purple:#6f42c1;
    --dark:#1a1a2e; --card-bg:#ffffff; --bg:#f4f6f9; --text:#333333; --border:#e0e0e0;
    --muted:#94a3b8; --na:#c0c4cc;
}
* { margin:0; padding:0; box-sizing:border-box; }
body { font-family:'Segoe UI',-apple-system,sans-serif; background:var(--bg); color:var(--text); line-height:1.5; padding-bottom:60px; }
.header { background:linear-gradient(135deg,var(--dark),#16213e); color:#fff; padding:28px 32px; }
.header h1 { font-size:1.55rem; font-weight:600; }
.header .subtitle { font-size:.95rem; opacity:.85; margin-top:4px; }
.header .meta { font-size:.8rem; opacity:.7; margin-top:8px; display:flex; flex-wrap:wrap; gap:18px; }
.header .meta span::before { content:"●"; margin-right:6px; color:#4a90e2; }
.container { padding:24px 32px; max-width:1600px; margin:0 auto; }

.section-title { font-size:1.15rem; font-weight:700; color:var(--dark); margin:36px 0 8px; padding:10px 14px; border-left:5px solid; background:#ffffff; border-radius:0 6px 6px 0; box-shadow:0 1px 3px rgba(0,0,0,0.05); overflow:hidden; }
.section-title .sub { display:block; font-size:.78rem; font-weight:400; color:#64748b; margin-top:2px; }
.section-title .badge { float:right; background:#f1f5f9; padding:3px 10px; border-radius:12px; font-size:.75rem; color:#475569; font-weight:500; }

.kpi-grid { display:grid; grid-template-columns:repeat(3, 1fr); gap:14px; margin:12px 0 22px; }
.kpi-grid .card { background:#fff; border-radius:10px; padding:18px 20px; box-shadow:0 2px 8px rgba(0,0,0,0.07); border-top:4px solid var(--blue); position:relative; }
.kpi-grid .card .label { font-size:.72rem; color:#64748b; text-transform:uppercase; letter-spacing:.06em; font-weight:600; padding-right:18px; }
.kpi-grid .card .value { font-size:2rem; font-weight:700; color:var(--dark); margin-top:6px; line-height:1; }
.kpi-grid .card .sub { font-size:.7rem; color:#94a3b8; margin-top:6px; }
.kpi-grid .card.na .value { color:var(--na); font-size:1.2rem; font-style:italic; }
.kpi-grid .card .led { position:absolute; top:14px; right:14px; width:12px; height:12px; border-radius:50%; box-shadow:0 0 0 2px #fff, 0 0 4px rgba(0,0,0,0.25); }
.kpi-grid .card .led-green  { background:var(--green);  box-shadow:0 0 0 2px #fff, 0 0 6px rgba(40,167,69,0.55); }
.kpi-grid .card .led-yellow { background:var(--yellow); box-shadow:0 0 0 2px #fff, 0 0 6px rgba(255,193,7,0.55); }
.kpi-grid .card .led-red    { background:var(--red);    box-shadow:0 0 0 2px #fff, 0 0 6px rgba(220,53,69,0.55); }
.kpi-grid .card .led-blue   { background:var(--blue);   box-shadow:0 0 0 2px #fff, 0 0 6px rgba(0,120,212,0.55); }

.mini-grid { display:grid; grid-template-columns:repeat(auto-fit, minmax(150px, 1fr)); gap:10px; margin:10px 0 14px; }
.mini-grid .card { background:#fff; border-radius:8px; padding:12px 14px; box-shadow:0 1px 4px rgba(0,0,0,0.06); border-top:3px solid var(--blue); position:relative; }
.mini-grid .card .label { font-size:.66rem; color:#64748b; text-transform:uppercase; letter-spacing:.04em; font-weight:600; padding-right:16px; }
.src-tag { display:inline-block; margin-left:4px; padding:1px 5px; border-radius:3px; font-size:.55rem; font-weight:700; color:#fff; background:#94a3b8; letter-spacing:.05em; vertical-align:middle; text-transform:none; cursor:help; }
.src-tag[title*="Insights"] { background:#0078d4; }
.src-tag[title*="pending migration"] { background:#f59e0b; color:#1a1a2e; }
.src-tag[title*="Master roster"] { background:#475569; }
.src-tag[title*="CPE Survey"]    { background:#6f42c1; }
.src-tag[title*="xlsx"]          { background:#16a34a; }
.src-tag[title*="CX Observe"]    { background:#14b8a6; }
.src-tag[title*="pending source"]{ background:#dc3545; }
[data-theme="dark"] .src-tag { background:#475569; }
[data-theme="dark"] .src-tag[title*="Insights"] { background:#3b82f6; }
[data-theme="dark"] .src-tag[title*="pending migration"] { background:#fbbf24; color:#1a1a2e; }
[data-theme="dark"] .src-tag[title*="Master roster"] { background:#334155; }
[data-theme="dark"] .src-tag[title*="CPE Survey"]    { background:#8b5cf6; }
[data-theme="dark"] .src-tag[title*="xlsx"]          { background:#22c55e; }
[data-theme="dark"] .src-tag[title*="CX Observe"]    { background:#2dd4bf; }
[data-theme="dark"] .src-tag[title*="pending source"]{ background:#ef4444; }
.mini-grid .card .value { font-size:1.4rem; font-weight:700; color:var(--dark); margin-top:3px; line-height:1; }
.mini-grid .card .sub { font-size:.65rem; color:#94a3b8; margin-top:3px; }
.mini-grid .card .led { position:absolute; top:10px; right:10px; width:10px; height:10px; border-radius:50%; box-shadow:0 0 0 2px #fff, 0 0 4px rgba(0,0,0,0.25); }
.mini-grid .card .led-green  { background:var(--green);  box-shadow:0 0 0 2px #fff, 0 0 5px rgba(40,167,69,0.55); }
.mini-grid .card .led-yellow { background:var(--yellow); box-shadow:0 0 0 2px #fff, 0 0 5px rgba(255,193,7,0.55); }
.mini-grid .card .led-red    { background:var(--red);    box-shadow:0 0 0 2px #fff, 0 0 5px rgba(220,53,69,0.55); }
.mini-grid .card .led-blue   { background:var(--blue);   box-shadow:0 0 0 2px #fff, 0 0 5px rgba(0,120,212,0.55); }

.cust-grid { display:grid; grid-template-columns:repeat(auto-fill, minmax(300px, 1fr)); gap:12px; margin-top:10px; margin-bottom:18px; }
.cust-card { background:#fff; border-radius:8px; padding:14px 16px; box-shadow:0 2px 6px rgba(0,0,0,0.06); border-left:4px solid var(--muted); position:relative; }
.cust-card .led { display:inline-block; width:8px; height:8px; margin-right:5px; vertical-align:middle; border-radius:50%; box-shadow:0 0 0 1px #fff, 0 0 3px rgba(0,0,0,0.18); }
.cust-card .led.led-green  { background:var(--green);  box-shadow:0 0 0 1px #fff, 0 0 4px rgba(40,167,69,0.7); }
.cust-card .led.led-yellow { background:var(--yellow); box-shadow:0 0 0 1px #fff, 0 0 4px rgba(255,193,7,0.7); }
.cust-card .led.led-red    { background:var(--red);    box-shadow:0 0 0 1px #fff, 0 0 4px rgba(220,53,69,0.7); }
.cust-card .led.led-blue   { background:var(--blue);   box-shadow:0 0 0 1px #fff, 0 0 4px rgba(0,120,212,0.7); }
.cust-card .name { font-size:.98rem; font-weight:700; color:var(--dark); }
.cust-card .name .tpid { font-size:.66rem; font-weight:400; color:#94a3b8; margin-left:8px; }
.cust-card .cx-meta { font-size:.7rem; color:#64748b; margin-top:2px; margin-bottom:10px; }
.cust-card .metrics { display:grid; grid-template-columns:repeat(3, 1fr); gap:6px 8px; }
.cust-card .metric { display:flex; flex-direction:column; }
.cust-card .metric .m-label { font-size:.6rem; color:#94a3b8; text-transform:uppercase; letter-spacing:.03em; }
.cust-card .metric .m-value { font-size:.9rem; font-weight:700; color:var(--dark); }
.cust-card .metric .m-value.na { color:var(--na); font-style:italic; font-size:.75rem; font-weight:500; }
.cust-card .tags { margin-top:10px; padding-top:8px; border-top:1px dashed var(--border); display:flex; flex-wrap:wrap; gap:6px; align-items:center; }
.cust-card.p4 { border-left-color:var(--green); }
.cust-card.p3 { border-left-color:var(--blue); }
.cust-card.p2 { border-left-color:var(--yellow); }
.cust-card.p1 { border-left-color:var(--red); }
.cust-card.pdrop { border-left-color:#9ca3af; opacity:.75; }

.table-wrapper { overflow-x:auto; border-radius:8px; box-shadow:0 2px 6px rgba(0,0,0,0.06); background:#fff; margin-top:6px; }
table { width:100%; border-collapse:collapse; font-size:.7rem; background:#fff; table-layout:auto; }
th { background:#f1f5f9; padding:6px 4px; text-align:center; font-weight:600; color:#475569; border-bottom:2px solid var(--border); white-space:nowrap; font-size:.62rem; letter-spacing:.02em; }
td { padding:5px 4px; border-bottom:1px solid #f1f5f9; text-align:center; vertical-align:top; font-size:.68rem; }
tr:hover td { background:#f8fafc; }
td.customer { font-weight:600; text-align:left; min-width:96px; max-width:120px; color:var(--dark); word-break:break-word; }
td.lead { text-align:left; color:#64748b; font-size:.64rem; min-width:80px; max-width:110px; word-break:break-word; }
td.na, .na { color:var(--na); font-style:italic; }
td.topics { text-align:left; font-size:.62rem; color:#475569; min-width:140px; max-width:180px; }
td.topics .topic-item { display:block; padding:1px 0; line-height:1.25; }
td.topics .topic-item .cnt { color:#94a3b8; font-size:.6rem; margin-left:3px; }
/* keep small numeric columns visually tight */
.table-wrapper table td:not(.customer):not(.lead):not(.topics) { white-space:nowrap; }

.phase { display:inline-block; padding:2px 8px; border-radius:10px; font-size:.68rem; font-weight:600; white-space:nowrap; }
.phase-1 { background:#fee2e2; color:#991b1b; }
.phase-2 { background:#fef3c7; color:#854d0e; }
.phase-3 { background:#dbeafe; color:#1e40af; }
.phase-4 { background:#d1fae5; color:#065f46; }
.phase-drop { background:#f3f4f6; color:#4b5563; }
.mc-yes { background:#d1fae5; color:#065f46; padding:2px 6px; border-radius:6px; font-size:.68rem; font-weight:600; white-space:nowrap; }
.mc-pipeline { background:#fef3c7; color:#854d0e; padding:2px 6px; border-radius:6px; font-size:.68rem; font-weight:600; white-space:nowrap; }
.mc-no { color:#94a3b8; font-size:.68rem; }
.bool-yes { color:var(--green); font-weight:700; }
.bool-no { color:#d1d5db; }
.status-ok { color:var(--green); font-weight:700; }
.status-warn { color:var(--yellow); font-weight:700; }
.metric-good { color:var(--green); font-weight:600; }
.metric-warn { color:#d97706; font-weight:600; }
.metric-bad { color:var(--red); font-weight:600; }
.critsit-flag { background:#fee2e2; color:#991b1b; padding:1px 6px; border-radius:4px; font-size:.68rem; font-weight:700; }

.legend { background:#fff; border-radius:8px; padding:14px 20px; margin:16px 0 24px; box-shadow:0 2px 6px rgba(0,0,0,0.06); font-size:.8rem; }
.legend h3 { font-size:.85rem; margin-bottom:10px; color:var(--dark); }
.legend .row { display:flex; flex-wrap:wrap; gap:20px; }
.legend .item { display:flex; align-items:center; gap:6px; color:#475569; }
.legend .na-note { margin-top:10px; padding-top:10px; border-top:1px dashed var(--border); color:#94a3b8; font-size:.72rem; }
.legend .na-note ul { margin:6px 0 0 18px; }

/* Support Themes (Top L2 / L3 across Focus Customers) */
.themes-grid { display:grid; grid-template-columns:repeat(auto-fit, minmax(420px, 1fr)); gap:14px; margin:6px 0 22px; }
.theme-panel { background:#fff; border-radius:10px; padding:14px 18px 16px; box-shadow:0 2px 8px rgba(0,0,0,0.07); border-top:3px solid var(--blue); }
.theme-head { font-size:.82rem; font-weight:700; color:var(--dark); margin-bottom:8px; padding-bottom:6px; border-bottom:1px solid var(--border); display:flex; justify-content:space-between; align-items:baseline; gap:10px; }
.theme-head .theme-sub { font-size:.65rem; font-weight:500; color:#94a3b8; text-transform:uppercase; letter-spacing:.04em; }
.theme-body { display:grid; grid-template-columns:220px 1fr; gap:16px; align-items:center; }
.theme-chart { display:flex; align-items:center; justify-content:center; }
.theme-list { list-style:none; padding:0; margin:0; font-size:.78rem; }
.theme-list li { display:grid; grid-template-columns:12px 1fr auto 46px; align-items:center; gap:8px; padding:3px 0; color:var(--text); }
.theme-list li .theme-swatch { width:10px; height:10px; border-radius:2px; }
.theme-list li .theme-lbl { overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.theme-list li .theme-cnt { font-weight:700; color:var(--dark); font-variant-numeric:tabular-nums; }
.theme-list li .theme-pct { color:#94a3b8; font-size:.7rem; font-variant-numeric:tabular-nums; text-align:right; }
.theme-list li.theme-other { color:#94a3b8; }
.theme-list li.theme-other .theme-cnt { color:#64748b; }
.theme-empty { color:#94a3b8; font-size:.75rem; font-style:italic; }
.theme-insights { margin:14px 0 20px; padding:14px 18px 14px; background:#fff8e1; border-left:4px solid #f59e0b; border-radius:6px; font-size:.72rem; color:#374151; letter-spacing:.02em; }
.theme-insights-head { font-size:.72rem; font-weight:700; color:#92400e; text-transform:uppercase; letter-spacing:.06em; margin-bottom:6px; }
.theme-insights ul { list-style:none; margin:0; padding:0; }
.theme-insights li { position:relative; padding:2px 0 2px 16px; line-height:1.5; }
.theme-insights li::before { content:"▸"; position:absolute; left:2px; top:2px; color:#f59e0b; font-weight:700; }
.theme-insights strong { color:var(--dark); }
@media (max-width:640px) { .theme-body { grid-template-columns:1fr; } .theme-chart { max-width:180px; margin:0 auto; } }

.callout { background:#fff8e1; border-left:4px solid var(--yellow); padding:14px 18px; border-radius:6px; margin:20px 0; font-size:.82rem; }
.callout strong { color:#854d0e; }
.callout.info { background:#eff6ff; border-left-color:var(--blue); }
.callout.info strong { color:#1e40af; }

.footer { padding:16px 32px; font-size:.72rem; color:#94a3b8; text-align:center; border-top:1px solid var(--border); margin-top:32px; }

/* --- Drill-down (raw-data) UI ---------------------------------------- */
.drill-kpi { cursor:pointer; border-bottom:1px dashed rgba(0,120,212,0.45); transition:background .15s; padding:0 1px; border-radius:3px; }
.drill-kpi:hover { background:rgba(0,120,212,0.12); border-bottom-color:var(--blue); }
.drill-kpi:focus { outline:2px solid var(--blue); outline-offset:1px; }
.drill-hint { display:inline-block; margin-left:6px; font-size:.6rem; color:var(--blue); opacity:.55; }
.drill-hint::before { content:"🔍"; }
.legend .drill-note { margin-top:8px; padding:8px 10px; background:#eff6ff; border-left:3px solid var(--blue); border-radius:4px; font-size:.75rem; color:#1e40af; }

.drill-overlay { position:fixed; inset:0; background:rgba(15,23,42,0.55); backdrop-filter:blur(2px); z-index:1000; display:none; align-items:flex-start; justify-content:center; padding:40px 20px; overflow-y:auto; }
.drill-overlay.open { display:flex; }
.drill-modal { background:#fff; border-radius:12px; box-shadow:0 20px 60px rgba(0,0,0,0.35); width:100%; max-width:1300px; max-height:calc(100vh - 80px); display:flex; flex-direction:column; overflow:hidden; }
.drill-modal .dm-head { padding:14px 20px; background:linear-gradient(135deg,var(--dark),#16213e); color:#fff; display:flex; justify-content:space-between; align-items:center; gap:14px; }
.drill-modal .dm-head h2 { font-size:1.05rem; font-weight:600; margin:0; }
.drill-modal .dm-head .dm-sub { font-size:.72rem; opacity:.78; margin-top:2px; }
.drill-modal .dm-head .dm-close { background:transparent; border:0; color:#fff; font-size:1.4rem; line-height:1; cursor:pointer; padding:4px 10px; border-radius:6px; }
.drill-modal .dm-head .dm-close:hover { background:rgba(255,255,255,0.15); }
.drill-modal .dm-toolbar { padding:10px 20px; background:#f8fafc; border-bottom:1px solid var(--border); display:flex; flex-wrap:wrap; gap:10px; align-items:center; font-size:.78rem; }
.drill-modal .dm-toolbar input[type=text] { padding:5px 10px; border:1px solid var(--border); border-radius:6px; font-size:.78rem; width:220px; }
.drill-modal .dm-toolbar .dm-count { color:#64748b; font-size:.72rem; }
.drill-modal .dm-toolbar .dm-btn { padding:5px 12px; background:#fff; border:1px solid var(--border); border-radius:6px; font-size:.72rem; color:#475569; cursor:pointer; font-weight:600; }
.drill-modal .dm-toolbar .dm-btn:hover { background:var(--blue); color:#fff; border-color:var(--blue); }
.drill-modal .dm-toolbar .dm-btn.active { background:var(--blue); color:#fff; border-color:var(--blue); }
.drill-modal .dm-body { flex:1; overflow:auto; padding:0; }
.drill-modal .dm-body .dm-empty { padding:40px 24px; text-align:center; color:#94a3b8; font-style:italic; }
.drill-modal table.dm-tbl { width:100%; border-collapse:collapse; font-size:.72rem; }
.drill-modal table.dm-tbl th { position:sticky; top:0; background:#f1f5f9; padding:7px 8px; text-align:left; border-bottom:2px solid var(--border); color:#334155; font-weight:600; cursor:pointer; white-space:nowrap; z-index:1; }
.drill-modal table.dm-tbl th:hover { background:#e2e8f0; }
.drill-modal table.dm-tbl th.sort-asc::after  { content:" ▲"; color:var(--blue); font-size:.65rem; }
.drill-modal table.dm-tbl th.sort-desc::after { content:" ▼"; color:var(--blue); font-size:.65rem; }
.drill-modal table.dm-tbl td { padding:6px 8px; border-bottom:1px solid #f1f5f9; text-align:left; vertical-align:top; font-family:'Segoe UI',sans-serif; }
.drill-modal table.dm-tbl td.mono { font-family:Consolas,'Courier New',monospace; font-size:.68rem; color:#475569; }
.drill-modal table.dm-tbl td.num { text-align:right; font-variant-numeric:tabular-nums; }
.drill-modal table.dm-tbl tr:hover td { background:#f8fafc; }
.drill-modal table.dm-tbl .badge-crit { background:#fee2e2; color:#991b1b; padding:1px 6px; border-radius:4px; font-size:.66rem; font-weight:700; }
.drill-modal table.dm-tbl .badge-open { background:#fef3c7; color:#854d0e; padding:1px 6px; border-radius:4px; font-size:.66rem; font-weight:600; }
.drill-modal table.dm-tbl .badge-cls  { background:#d1fae5; color:#065f46; padding:1px 6px; border-radius:4px; font-size:.66rem; font-weight:600; }
.drill-modal table.dm-tbl .csat-5 { color:var(--green); font-weight:700; }
.drill-modal table.dm-tbl .csat-4 { color:#0369a1; font-weight:600; }
.drill-modal table.dm-tbl .csat-lo { color:var(--red); font-weight:700; }
.drill-modal .dm-acr { padding:16px 20px; }
.drill-modal .dm-acr .acr-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:10px; }
.drill-modal .dm-acr .acr-cell { background:#f8fafc; border:1px solid var(--border); border-radius:8px; padding:10px 12px; }
.drill-modal .dm-acr .acr-cell .k { font-size:.66rem; color:#94a3b8; text-transform:uppercase; }
.drill-modal .dm-acr .acr-cell .v { font-size:1.1rem; font-weight:700; color:var(--dark); margin-top:2px; }

/* --- Wiki summary modal (v2.11) --------------------------------------- */
.wiki-overlay { position:fixed; inset:0; background:rgba(15,23,42,0.55); backdrop-filter:blur(2px); z-index:1000; display:none; align-items:flex-start; justify-content:center; padding:60px 20px; overflow-y:auto; }
.wiki-overlay.open { display:flex; }
.wiki-modal { background:#fff; border-radius:12px; box-shadow:0 20px 60px rgba(0,0,0,0.35); width:100%; max-width:720px; max-height:calc(100vh - 100px); display:flex; flex-direction:column; overflow:hidden; }
.wiki-modal .wm-head { padding:14px 20px; background:linear-gradient(135deg,var(--dark),#16213e); color:#fff; display:flex; justify-content:space-between; align-items:center; gap:14px; }
.wiki-modal .wm-head h2 { font-size:1.05rem; font-weight:600; margin:0; display:flex; align-items:center; }
.wiki-modal .wm-head .wm-sub { font-size:.72rem; opacity:.78; margin-top:2px; }
.wiki-modal .wm-head .wm-close { background:transparent; border:0; color:#fff; font-size:1.4rem; line-height:1; cursor:pointer; padding:4px 10px; border-radius:6px; }
.wiki-modal .wm-head .wm-close:hover { background:rgba(255,255,255,0.15); }
.wiki-modal .wm-body { flex:1; overflow:auto; padding:18px 24px; font-size:.85rem; line-height:1.55; color:#334155; }
.wiki-modal .wm-body ul { margin:0 0 4px 22px; padding:0; }
.wiki-modal .wm-body li { margin:8px 0; }
.wiki-modal .wm-body .wm-empty { text-align:center; color:#94a3b8; font-style:italic; padding:30px 10px; line-height:1.6; }
.wiki-modal .wm-body .wm-empty code { background:#f1f5f9; padding:2px 6px; border-radius:4px; font-size:.78rem; color:#334155; }
.wiki-modal .wm-meta { border-top:1px solid var(--border); padding:10px 22px; font-size:.72rem; color:#64748b; background:#f8fafc; display:flex; justify-content:space-between; flex-wrap:wrap; gap:10px; }
.wiki-modal .wm-meta a { color:var(--blue); text-decoration:none; font-weight:600; }
.wiki-modal .wm-meta a:hover { text-decoration:underline; }
.wiki-modal .wm-workload { display:inline-block; padding:2px 10px; border-radius:12px; font-size:.66rem; font-weight:700; margin-left:10px; letter-spacing:.03em; text-transform:uppercase; }
.wiki-modal .wm-workload.SAP  { background:#dbeafe; color:#1e40af; }
.wiki-modal .wm-workload.RISE { background:#e0e7ff; color:#4338ca; }
.wiki-modal .wm-workload.EPIC { background:#d1fae5; color:#065f46; }
.wiki-tag { transition:color .12s; }
.wiki-tag:hover { color:var(--blue) !important; }

/* --- CaaS Lead review link + modal (v2.14) --------------------------- */
.review-link { color:inherit; text-decoration:none; border-bottom:1px dashed rgba(59,130,246,0.55); padding-bottom:1px; cursor:pointer; transition:color .12s, border-color .12s; }
.review-link:hover { color:var(--blue); border-bottom-color:var(--blue); border-bottom-style:solid; }
.review-link:focus { outline:2px solid rgba(59,130,246,0.35); outline-offset:2px; border-radius:2px; }
.review-modal .rv-section { margin:0 0 22px 0; }
.review-modal .rv-section:last-child { margin-bottom:4px; }
.review-modal .rv-section h3 { font-size:.82rem; font-weight:700; letter-spacing:.04em; text-transform:uppercase; color:#0f172a; margin:0 0 8px 0; padding:6px 12px; border-radius:6px; background:#f1f5f9; border-left:3px solid var(--blue); display:flex; align-items:center; justify-content:space-between; gap:8px; }
.review-modal .rv-section h3 .rv-count { font-size:.66rem; color:#64748b; font-weight:600; letter-spacing:.02em; text-transform:none; }
.review-modal .rv-section.key h3    { border-left-color:#0078d4; }
.review-modal .rv-section.svc h3    { border-left-color:#28a745; }
.review-modal .rv-section.rem h3    { border-left-color:#f59e0b; }
.review-modal .rv-section ul { margin:0 0 4px 22px; padding:0; }
.review-modal .rv-section li { margin:6px 0; font-size:.83rem; line-height:1.55; }
.review-modal .rv-empty-line { color:#94a3b8; font-style:italic; padding:4px 0 4px 4px; font-size:.78rem; }

/* --- Cohort tabs (v2.6.0) --------------------------------------------- */
.cohort-tabs { margin:24px 0 12px; }
.cohort-tabs .tab-bar { display:flex; flex-wrap:wrap; gap:0; border-bottom:2px solid var(--border); padding-left:4px; }
.cohort-tabs .tab-btn { background:#f8fafc; border:1px solid var(--border); border-bottom:0; padding:10px 20px; margin-right:4px; margin-bottom:-2px; border-radius:8px 8px 0 0; cursor:pointer; font-size:.85rem; font-weight:600; color:#64748b; transition:all .15s; position:relative; display:flex; flex-direction:column; align-items:flex-start; gap:2px; min-width:180px; font-family:inherit; }
.cohort-tabs .tab-btn:hover { background:#eff6ff; color:#1e40af; }
.cohort-tabs .tab-btn .tab-title { font-size:.85rem; font-weight:700; }
.cohort-tabs .tab-btn .tab-sub { font-size:.65rem; font-weight:500; color:#94a3b8; text-transform:none; }
.cohort-tabs .tab-btn.active { background:#fff; color:var(--dark); border-color:var(--border); border-bottom:2px solid #fff; z-index:2; box-shadow:0 -2px 6px rgba(0,0,0,0.04); }
.cohort-tabs .tab-btn.active .tab-sub { color:#475569; }
.cohort-tabs .tab-btn.active::before { content:""; position:absolute; top:-2px; left:0; right:0; height:3px; background:var(--tab-color, var(--blue)); border-radius:3px 3px 0 0; }
.cohort-tabs .tab-pane { display:none; padding:16px 4px 4px; animation:fadeIn .18s ease-out; }
.cohort-tabs .tab-pane.active { display:block; }
.cohort-tabs .tab-pane > .section-title:first-child { margin-top:0; }
@keyframes fadeIn { from { opacity:0; transform:translateY(4px); } to { opacity:1; transform:translateY(0); } }

/* --- Theme toggle (v2.7.0) -------------------------------------------- */
.theme-toggle { position:fixed; top:20px; right:24px; z-index:900; display:inline-flex; align-items:center; gap:8px; padding:7px 14px 7px 10px; background:rgba(255,255,255,0.14); color:#fff; border:1px solid rgba(255,255,255,0.25); border-radius:999px; cursor:pointer; font-family:inherit; font-size:.75rem; font-weight:600; letter-spacing:.02em; backdrop-filter:blur(6px); transition:background .15s, transform .15s; }
.theme-toggle:hover { background:rgba(255,255,255,0.24); transform:translateY(-1px); }
.theme-toggle:focus { outline:2px solid #93c5fd; outline-offset:2px; }
.theme-toggle .tt-icon { font-size:1rem; line-height:1; }
.theme-toggle .tt-label { text-transform:uppercase; }
[data-theme="dark"] .theme-toggle { background:rgba(30,41,59,0.7); border-color:rgba(148,163,184,0.4); color:#fbbf24; }
[data-theme="dark"] .theme-toggle:hover { background:rgba(51,65,85,0.9); }

/* --- Dark theme override (v2.7.0) ------------------------------------ */
/* Palette shift — keep colored accents (LED/phase/badges) intact, only re-tint surfaces & text */
[data-theme="dark"] {
    --bg:#0f172a;              /* slate-900 */
    --card-bg:#1e293b;         /* slate-800 */
    --dark:#f1f5f9;            /* used as text/heading colour in dark */
    --text:#e2e8f0;
    --border:#334155;          /* slate-700 */
    --muted:#94a3b8;
    --na:#64748b;
    color-scheme:dark;
}
[data-theme="dark"] body { background:var(--bg); color:var(--text); }
[data-theme="dark"] .header { background:linear-gradient(135deg,#020617,#0f172a); border-bottom:1px solid #1e293b; }
[data-theme="dark"] .section-title { background:#1e293b; color:#f1f5f9; box-shadow:0 1px 3px rgba(0,0,0,0.3); }
[data-theme="dark"] .section-title .sub { color:#94a3b8; }
[data-theme="dark"] .section-title .badge { background:#334155; color:#cbd5e1; }
[data-theme="dark"] .kpi-grid .card,
[data-theme="dark"] .mini-grid .card,
[data-theme="dark"] .cust-card,
[data-theme="dark"] .table-wrapper,
[data-theme="dark"] table,
[data-theme="dark"] .legend { background:#1e293b; box-shadow:0 2px 8px rgba(0,0,0,0.35); }
[data-theme="dark"] .kpi-grid .card .value,
[data-theme="dark"] .mini-grid .card .value,
[data-theme="dark"] .cust-card .name,
[data-theme="dark"] .cust-card .metric .m-value,
[data-theme="dark"] td.customer,
[data-theme="dark"] .legend h3 { color:#f1f5f9; }
[data-theme="dark"] .kpi-grid .card .label,
[data-theme="dark"] .mini-grid .card .label,
[data-theme="dark"] .cust-card .cx-meta,
[data-theme="dark"] .legend .item,
[data-theme="dark"] td.lead,
[data-theme="dark"] td.topics { color:#cbd5e1; }
[data-theme="dark"] .kpi-grid .card .sub,
[data-theme="dark"] .mini-grid .card .sub,
[data-theme="dark"] .cust-card .metric .m-label,
[data-theme="dark"] .cust-card .name .tpid,
[data-theme="dark"] td.topics .topic-item .cnt { color:#94a3b8; }
[data-theme="dark"] .kpi-grid .card .led,
[data-theme="dark"] .mini-grid .card .led,
[data-theme="dark"] .cust-card .led { box-shadow:0 0 0 2px #1e293b, 0 0 6px rgba(0,0,0,0.5); }
[data-theme="dark"] .kpi-grid .card .led-green  { box-shadow:0 0 0 2px #1e293b, 0 0 7px rgba(40,167,69,0.65); }
[data-theme="dark"] .kpi-grid .card .led-yellow { box-shadow:0 0 0 2px #1e293b, 0 0 7px rgba(255,193,7,0.65); }
[data-theme="dark"] .kpi-grid .card .led-red    { box-shadow:0 0 0 2px #1e293b, 0 0 7px rgba(220,53,69,0.65); }
[data-theme="dark"] .kpi-grid .card .led-blue   { box-shadow:0 0 0 2px #1e293b, 0 0 7px rgba(0,120,212,0.65); }
[data-theme="dark"] .mini-grid .card .led-green  { box-shadow:0 0 0 2px #1e293b, 0 0 6px rgba(40,167,69,0.65); }
[data-theme="dark"] .mini-grid .card .led-yellow { box-shadow:0 0 0 2px #1e293b, 0 0 6px rgba(255,193,7,0.65); }
[data-theme="dark"] .mini-grid .card .led-red    { box-shadow:0 0 0 2px #1e293b, 0 0 6px rgba(220,53,69,0.65); }
[data-theme="dark"] .mini-grid .card .led-blue   { box-shadow:0 0 0 2px #1e293b, 0 0 6px rgba(0,120,212,0.65); }
[data-theme="dark"] th { background:#0f172a; color:#cbd5e1; border-bottom-color:#334155; }
[data-theme="dark"] td { border-bottom-color:#334155; }
[data-theme="dark"] tr:hover td { background:#334155; }
[data-theme="dark"] .cust-card .tags { border-top-color:#334155; }
[data-theme="dark"] .cust-card.pdrop { opacity:.55; }
[data-theme="dark"] .callout { background:#422006; color:#fde68a; }
[data-theme="dark"] .callout strong { color:#fbbf24; }
[data-theme="dark"] .callout.info { background:#0c2340; color:#bfdbfe; }
[data-theme="dark"] .callout.info strong { color:#93c5fd; }
[data-theme="dark"] .legend .na-note { color:#94a3b8; border-top-color:#334155; }
[data-theme="dark"] .theme-panel { background:#1e293b; box-shadow:0 2px 8px rgba(0,0,0,0.35); }
[data-theme="dark"] .theme-head { color:#f1f5f9; border-bottom-color:#334155; }
[data-theme="dark"] .theme-head .theme-sub { color:#64748b; }
[data-theme="dark"] .theme-list li { color:#cbd5e1; }
[data-theme="dark"] .theme-list li .theme-cnt { color:#f1f5f9; }
[data-theme="dark"] .theme-list li .theme-pct { color:#64748b; }
[data-theme="dark"] .theme-list li.theme-other { color:#64748b; }
[data-theme="dark"] .theme-insights { background:#422006; color:#fde68a; border-left-color:#f59e0b; }
[data-theme="dark"] .theme-insights-head { color:#fbbf24; }
[data-theme="dark"] .theme-insights strong { color:#fef3c7; }
[data-theme="dark"] .footer { color:#64748b; border-top-color:#334155; }
[data-theme="dark"] .phase-1 { background:#7f1d1d; color:#fecaca; }
[data-theme="dark"] .phase-2 { background:#78350f; color:#fde68a; }
[data-theme="dark"] .phase-3 { background:#1e3a8a; color:#bfdbfe; }
[data-theme="dark"] .phase-4 { background:#064e3b; color:#a7f3d0; }
[data-theme="dark"] .phase-drop { background:#1f2937; color:#9ca3af; }
[data-theme="dark"] .mc-yes { background:#064e3b; color:#a7f3d0; }
[data-theme="dark"] .mc-pipeline { background:#78350f; color:#fde68a; }
[data-theme="dark"] .mc-no { color:#64748b; }
[data-theme="dark"] .critsit-flag { background:#7f1d1d; color:#fecaca; }
[data-theme="dark"] .status-ok, [data-theme="dark"] .metric-good { color:#34d399; }
[data-theme="dark"] .status-warn, [data-theme="dark"] .metric-warn { color:#fbbf24; }
[data-theme="dark"] .metric-bad { color:#f87171; }
[data-theme="dark"] .bool-no { color:#475569; }
[data-theme="dark"] .drill-kpi { border-bottom-color:rgba(147,197,253,0.55); }
[data-theme="dark"] .drill-kpi:hover { background:rgba(59,130,246,0.22); border-bottom-color:#93c5fd; }
[data-theme="dark"] .legend .drill-note { background:#0c2340; color:#bfdbfe; border-left-color:#3b82f6; }
[data-theme="dark"] .drill-overlay { background:rgba(2,6,23,0.75); }
[data-theme="dark"] .drill-modal { background:#1e293b; box-shadow:0 20px 60px rgba(0,0,0,0.6); }
[data-theme="dark"] .drill-modal .dm-head { background:linear-gradient(135deg,#020617,#0f172a); }
[data-theme="dark"] .drill-modal .dm-toolbar { background:#0f172a; border-bottom-color:#334155; color:#cbd5e1; }
[data-theme="dark"] .drill-modal .dm-toolbar input[type=text] { background:#1e293b; border-color:#334155; color:#e2e8f0; }
[data-theme="dark"] .drill-modal .dm-toolbar .dm-btn { background:#334155; border-color:#475569; color:#e2e8f0; }
[data-theme="dark"] .drill-modal .dm-toolbar .dm-btn:hover { background:#475569; }
[data-theme="dark"] .drill-modal .dm-toolbar .dm-count { color:#94a3b8; }
[data-theme="dark"] .drill-modal .dm-body { background:#1e293b; }
[data-theme="dark"] .drill-modal .dm-tbl th { background:#0f172a; color:#cbd5e1; }
[data-theme="dark"] .drill-modal .dm-tbl td { border-bottom-color:#334155; color:#e2e8f0; }
[data-theme="dark"] .drill-modal .dm-tbl tr:hover td { background:#334155; }
[data-theme="dark"] .drill-modal .dm-acr .acr-cell { background:#0f172a; border-color:#334155; }
[data-theme="dark"] .drill-modal .dm-acr .acr-cell .k { color:#64748b; }
[data-theme="dark"] .drill-modal .dm-acr .acr-cell .v { color:#f1f5f9; }
[data-theme="dark"] .wiki-overlay { background:rgba(2,6,23,0.75); }
[data-theme="dark"] .wiki-modal { background:#1e293b; box-shadow:0 20px 60px rgba(0,0,0,0.6); }
[data-theme="dark"] .wiki-modal .wm-head { background:linear-gradient(135deg,#020617,#0f172a); }
[data-theme="dark"] .wiki-modal .wm-body { background:#1e293b; color:#cbd5e1; }
[data-theme="dark"] .wiki-modal .wm-body .wm-empty code { background:#0f172a; color:#e2e8f0; }
[data-theme="dark"] .wiki-modal .wm-meta { background:#0f172a; border-top-color:#334155; color:#94a3b8; }
[data-theme="dark"] .wiki-modal .wm-workload.SAP  { background:#1e3a8a; color:#dbeafe; }
[data-theme="dark"] .wiki-modal .wm-workload.RISE { background:#3730a3; color:#e0e7ff; }
[data-theme="dark"] .wiki-modal .wm-workload.EPIC { background:#065f46; color:#d1fae5; }
[data-theme="dark"] .cohort-tabs .tab-bar { border-bottom-color:#334155; }
[data-theme="dark"] .cohort-tabs .tab-btn { background:#0f172a; border-color:#334155; color:#94a3b8; }
[data-theme="dark"] .cohort-tabs .tab-btn:hover { background:#1e293b; color:#93c5fd; }
[data-theme="dark"] .cohort-tabs .tab-btn.active { background:#1e293b; color:#f1f5f9; border-bottom-color:#1e293b; }
[data-theme="dark"] .cohort-tabs .tab-btn.active .tab-sub { color:#cbd5e1; }
[data-theme="dark"] .cohort-tabs .tab-btn .tab-sub { color:#64748b; }

/* --- Data Source toggle + modal (v2.14.3) ----------------------------- */
.datasource-toggle { position:fixed; top:20px; right:128px; z-index:900; display:inline-flex; align-items:center; gap:8px; padding:7px 14px 7px 10px; background:rgba(255,255,255,0.14); color:#fff; border:1px solid rgba(255,255,255,0.25); border-radius:999px; cursor:pointer; font-family:inherit; font-size:.75rem; font-weight:600; letter-spacing:.02em; backdrop-filter:blur(6px); transition:background .15s, transform .15s; }
.datasource-toggle:hover { background:rgba(255,255,255,0.24); transform:translateY(-1px); }
.datasource-toggle:focus { outline:2px solid #93c5fd; outline-offset:2px; }
.datasource-toggle .ds-icon { font-size:1rem; line-height:1; }
.datasource-toggle .ds-label { text-transform:uppercase; }
[data-theme="dark"] .datasource-toggle { background:rgba(30,41,59,0.7); border-color:rgba(148,163,184,0.4); color:#93c5fd; }
[data-theme="dark"] .datasource-toggle:hover { background:rgba(51,65,85,0.9); }

.datasource-modal { max-width:1200px !important; }
.datasource-modal .wm-body { padding:20px 26px; }
.ds-intro { font-size:.83rem; line-height:1.65; color:#475569; margin:0 0 18px; padding:12px 14px; background:#f1f5f9; border-left:3px solid #0078d4; border-radius:6px; }
.ds-intro b { color:#0f172a; }
.ds-diagram { display:flex; flex-direction:column; align-items:stretch; gap:4px; margin:0 0 22px; }
.ds-tier { background:#f8fafc; border:1px solid #e2e8f0; border-radius:10px; padding:12px 14px; }
.ds-tier-label { font-size:.68rem; font-weight:700; color:#64748b; letter-spacing:.06em; text-transform:uppercase; margin:0 0 10px; display:flex; align-items:center; gap:8px; }
.ds-step { display:inline-flex; align-items:center; justify-content:center; width:22px; height:22px; border-radius:50%; background:#0078d4; color:#fff; font-size:.72rem; font-weight:700; flex-shrink:0; }
.ds-tier-boxes { display:grid; gap:8px; }
.ds-tier.tier-src .ds-tier-boxes { grid-template-columns:repeat(5,1fr); }
.ds-tier.tier-stg .ds-tier-boxes { grid-template-columns:repeat(4,1fr); }
.ds-src { background:#fff; border-radius:8px; padding:9px 10px 10px; border-top:3px solid #0078d4; box-shadow:0 1px 2px rgba(15,23,42,0.06); font-size:.72rem; line-height:1.4; color:#334155; text-align:center; }
.ds-src.k { border-top-color:#7c3aed; }
.ds-src.p { border-top-color:#0078d4; }
.ds-src.c { border-top-color:#f59e0b; }
.ds-src.w { border-top-color:#0ea5e9; }
.ds-src.s { border-top-color:#10b981; }
.ds-src .ds-name { font-weight:700; color:#0f172a; font-size:.78rem; margin-bottom:2px; display:block; }
.ds-src .ds-note { font-size:.66rem; color:#64748b; line-height:1.35; display:block; }
.ds-file { background:#fff; border-radius:6px; padding:6px 9px; border:1px solid #e2e8f0; font-family:ui-monospace,SFMono-Regular,Consolas,monospace; font-size:.68rem; color:#0f172a; text-align:center; word-break:break-all; }
.ds-render { background:#0f172a; color:#f1f5f9; border-radius:8px; padding:12px 16px; font-size:.78rem; text-align:center; font-weight:600; display:flex; align-items:center; justify-content:center; gap:10px; flex-wrap:wrap; }
.ds-render .ds-step { background:#fff; color:#0f172a; }
.ds-render code { background:rgba(255,255,255,0.12); padding:2px 7px; border-radius:4px; font-size:.72rem; color:#e2e8f0; font-family:ui-monospace,SFMono-Regular,Consolas,monospace; }
.ds-arrow { text-align:center; color:#94a3b8; font-size:1.1rem; line-height:1; padding:2px 0; }
.ds-table { width:100%; border-collapse:collapse; font-size:.76rem; margin-top:4px; table-layout:fixed; }
.ds-table col.c-num  { width:38px; }
.ds-table col.c-sys  { width:96px; }
.ds-table col.c-src  { width:22%; }
.ds-table col.c-ext  { width:22%; }
.ds-table col.c-stg  { width:22%; }
.ds-table col.c-feed { width:auto; }
.ds-table th { text-align:left; background:#0f172a; color:#f1f5f9; font-weight:600; padding:7px 10px; font-size:.7rem; letter-spacing:.03em; text-transform:uppercase; }
.ds-table th:first-child { border-radius:6px 0 0 0; width:38px; text-align:center; }
.ds-table th:last-child { border-radius:0 6px 0 0; }
.ds-table td { padding:8px 10px; border-bottom:1px solid #e2e8f0; vertical-align:top; color:#334155; line-height:1.5; word-break:break-word; overflow-wrap:break-word; }
.ds-table td:first-child { text-align:center; }
.ds-table tr:last-child td { border-bottom:0; }
.ds-table code { background:#f1f5f9; padding:1px 5px; border-radius:3px; font-size:.7rem; color:#0f172a; font-family:ui-monospace,SFMono-Regular,Consolas,monospace; }
.ds-table .ds-tag { display:inline-block; padding:1px 8px; border-radius:10px; font-size:.65rem; font-weight:700; text-transform:uppercase; letter-spacing:.03em; min-width:22px; }
.ds-table .ds-tag.k { background:#ede9fe; color:#6d28d9; }
.ds-table .ds-tag.p { background:#dbeafe; color:#1d4ed8; }
.ds-table .ds-tag.c { background:#fef3c7; color:#b45309; }
.ds-table .ds-tag.w { background:#e0f2fe; color:#0369a1; }
.ds-table .ds-tag.s { background:#dcfce7; color:#166534; }
.ds-table .ds-tag.m { background:#f1f5f9; color:#475569; }

[data-theme="dark"] .ds-intro { background:#0f172a; color:#cbd5e1; border-left-color:#38bdf8; }
[data-theme="dark"] .ds-intro b { color:#f1f5f9; }
[data-theme="dark"] .ds-tier { background:#0f172a; border-color:#334155; }
[data-theme="dark"] .ds-tier-label { color:#94a3b8; }
[data-theme="dark"] .ds-src { background:#1e293b; color:#cbd5e1; box-shadow:0 1px 2px rgba(0,0,0,0.3); }
[data-theme="dark"] .ds-src .ds-name { color:#f1f5f9; }
[data-theme="dark"] .ds-src .ds-note { color:#94a3b8; }
[data-theme="dark"] .ds-file { background:#1e293b; border-color:#334155; color:#e2e8f0; }
[data-theme="dark"] .ds-render { background:#020617; color:#e2e8f0; }
[data-theme="dark"] .ds-render code { background:rgba(255,255,255,0.08); color:#e2e8f0; }
[data-theme="dark"] .ds-table th { background:#020617; }
[data-theme="dark"] .ds-table td { color:#cbd5e1; border-bottom-color:#334155; }
[data-theme="dark"] .ds-table code { background:#0f172a; color:#e2e8f0; }
[data-theme="dark"] .ds-table .ds-tag.k { background:#4c1d95; color:#e9d5ff; }
[data-theme="dark"] .ds-table .ds-tag.p { background:#1e40af; color:#dbeafe; }
[data-theme="dark"] .ds-table .ds-tag.c { background:#78350f; color:#fef3c7; }
[data-theme="dark"] .ds-table .ds-tag.w { background:#075985; color:#e0f2fe; }
[data-theme="dark"] .ds-table .ds-tag.s { background:#14532d; color:#dcfce7; }
[data-theme="dark"] .ds-table .ds-tag.m { background:#334155; color:#cbd5e1; }
"""


def _dtc_class(v):
    if v is None: return None
    if v <= 12: return "metric-good"
    if v <= 20: return "metric-warn"
    return "metric-bad"


def _pct7_class(v):
    if v is None: return None
    if v >= 50: return "metric-good"
    if v >= 35: return "metric-warn"
    return "metric-bad"


def _csat_class(avg):
    if avg is None: return None
    if avg >= 4.8: return "metric-good"
    if avg >= 4.5: return "metric-warn"
    return "metric-bad"


def status_led(value, target, higher_is_better=True) -> str:
    """Return the LED HTML for a KPI card.

    Rules (per user spec 2026-07-18):
      * Green  = value meets or beats target
      * Yellow = value trails target by <= 3%
      * Red    = value trails target by >  3% (5%+ definitely red)
      * Blue   = informational / pending / no target (value=None or target=None)

    'higher_is_better=True'  -> good when value >= target (CSAT, %<7d)
    'higher_is_better=False' -> good when value <= target (DTC, Avg Age)
    """
    if value is None or target is None:
        return '<span class="led led-blue" title="Informational"></span>'
    try:
        v = float(value); t = float(target)
    except (TypeError, ValueError):
        return '<span class="led led-blue" title="Informational"></span>'
    if higher_is_better:
        if v >= t:
            return f'<span class="led led-green" title="Meets target {t}"></span>'
        gap_pct = (t - v) / t * 100.0 if t else 0.0
    else:
        if v <= t:
            return f'<span class="led led-green" title="Meets target {t}"></span>'
        gap_pct = (v - t) / t * 100.0 if t else 0.0
    if gap_pct <= 3.0:
        return f'<span class="led led-yellow" title="Trails target by {gap_pct:.1f}% (<=3%)"></span>'
    return f'<span class="led led-red" title="Trails target by {gap_pct:.1f}% (>3%)"></span>'


LED_BLUE = '<span class="led led-blue" title="Informational"></span>'


def worst_led(pa: dict, cs: dict) -> str:
    """Aggregate LED for a customer card: worst of DTC / %<7d / CSAT (only KPIs with targets).
    Priority: red > yellow > green; blue if no target-based KPI has data."""
    leds: list[str] = []
    if pa.get('avg_dtc') is not None:
        leds.append(status_led(pa['avg_dtc'], 12, higher_is_better=False))
    if pa.get('pct_close_7') is not None:
        leds.append(status_led(pa['pct_close_7'], 50, higher_is_better=True))
    if cs.get('n', 0) > 0:
        leds.append(status_led(cs['avg'], 4.8, higher_is_better=True))
    if not leds:
        return LED_BLUE
    for tag in ('led-red', 'led-yellow', 'led-green'):
        for l in leds:
            if tag in l:
                return l
    return LED_BLUE


def fmt_stage(stage: str) -> str:
    s = stage.lower()
    cls = "phase-drop" if "drop" in s else \
          "phase-1" if "phase 1" in s else \
          "phase-2" if "phase 2" in s else \
          "phase-3" if "phase 3" in s else \
          "phase-4" if "phase 4" in s else "phase-2"
    # Display as "Stage N" (per CaaS Lead 2.0 PPT p.17) while keeping
    # the underlying data field and CSS class names for backward compatibility.
    label = stage.replace("Phase", "Stage").replace("phase", "Stage")
    return f'<span class="phase {cls}">{label}</span>'


def fmt_mc(mc: str) -> str:
    if "Non-SFMC" in mc or "exiting" in mc:
        return f'<span class="mc-no">{mc}</span>'
    if "Pipeline" in mc:
        return f'<span class="mc-pipeline">{mc}</span>'
    return f'<span class="mc-yes">{mc}</span>'


def _is_mc_active(mc: str) -> bool:
    """True if the customer has an active MC contract (not pipeline, not Non-SFMC, not exiting)."""
    s = str(mc or "").strip().lower()
    if not s:
        return False
    if "non-sfmc" in s or "exiting" in s or "pipeline" in s:
        return False
    return s.startswith("yes") or s.startswith("mission critical")


def fmt_bool(v: bool) -> str:
    return '<span class="bool-yes">✓</span>' if v else '<span class="bool-no">—</span>'


def fmt_status(v: bool) -> str:
    """Green check when delivered, yellow warning triangle when not yet started."""
    return '<span class="status-ok">✓</span>' if v else '<span class="status-warn">⚠</span>'


def fmt_topics(topics: list[tuple[str, int]]) -> str:
    if not topics:
        return '<span class="na">NA</span>'
    return "".join(
        f'<span class="topic-item">{t}<span class="cnt">({n})</span></span>'
        for t, n in topics
    )


def phase_class(stage: str) -> str:
    s = stage.lower()
    if "drop" in s: return "pdrop"
    if "phase 4" in s: return "p4"
    if "phase 3" in s: return "p3"
    if "phase 2" in s: return "p2"
    if "phase 1" in s: return "p1"
    return ""


def render_asw_baseline(baseline: dict, focus_vol: int, asw_csat: dict,
                        insights_snapshot: dict | None = None) -> str:
    """ASW-wide FY26 baseline strip (denominator for coverage %). Shown ABOVE Section 1.

    KPIs source split (v2.8.0):
      * The six team-wide KPIs (Case Vol, Closed, Avg CSAT, Avg DTC, %<7d, CritSit Rate) are
        preferentially read from the A&I and DTP | Insights+_v3_AIDTP_Fabric snapshot to align
        with the leadership-facing dashboard. Any KPI whose value is null in the snapshot falls
        back to the KPISupportData-computed value from `baseline`.
      * Distinct Customers and CaaS Lead Coverage remain KPISupportData (Insights+_v3 does not
        expose them at this level).

    Coverage denominator (v2.9.1):
      * `CaaS Lead Coverage` % and `non_focus_vol` use the Insights+_v3 `ASW Created Cases`
        override when available (aligns with the leadership-facing card). Falls back to
        `baseline["vol"]` (KPISupportData Case Raw) when Insights+_v3 value is null.
    """
    # Merge Insights+_v3 overrides where available, otherwise KPISupportData fallback
    kpis = (insights_snapshot or {}).get("kpis", {})

    # Effective ASW-wide denominator: prefer Insights+_v3 override, else KPISupportData
    _cv_entry = (kpis.get("case_vol") or {})
    effective_asw_vol = _cv_entry.get("value") if _cv_entry.get("value") is not None else baseline["vol"]
    non_focus_vol = effective_asw_vol - focus_vol
    focus_pct = round(100.0 * focus_vol / effective_asw_vol, 1) if effective_asw_vol else 0.0

    def _pick(name: str, fallback):
        """Return (value, source, pending_source) tuple.

        * value        — Insights+_v3 override if present, else fallback (typically KPISupportData).
        * source       — "Insights+_v3" when the override is used, otherwise "KPISupportData".
        * pending_source — string set on the JSON entry when the KPI is queued to migrate to a
          new source (e.g. "Insights+_v3") but the value hasn't been captured yet. Used by the
          rendered pill to display a `K*` marker so viewers know the routing decision is
          documented and the value will move once captured. Returns "" (empty) if no migration
          is pending or the value is already sourced from the pending source.
        """
        entry = kpis.get(name) or {}
        v = entry.get("value")
        if v is not None:
            src = entry.get("source", "KPISupportData")
            pending = ""  # already using the intended source
        else:
            src = "KPISupportData"
            pending = entry.get("pending_source", "") or ""
        return (v if v is not None else fallback), src, pending

    computed_critsit_rate = round(100.0 * baseline["critsit"] / baseline["vol"], 1) if baseline["vol"] else 0.0
    computed_close_rate   = round(100.0 * baseline["closed"] / baseline["vol"], 1) if baseline["vol"] else 0.0

    vol_v,    vol_src,    vol_pend    = _pick("case_vol",     baseline["vol"])
    closed_v, closed_src, closed_pend = _pick("closed",       baseline["closed"])
    csat_v,   csat_src,   csat_pend   = _pick("csat_avg",     asw_csat.get("avg") if asw_csat.get("n") else None)
    ir_v,     ir_src,     ir_pend     = _pick("ir_met_pct",   None)
    dtc_v,    dtc_src,    dtc_pend    = _pick("avg_dtc",      baseline["avg_dtc"])
    pct7_v,   pct7_src,   pct7_pend   = _pick("pct_close_7d", baseline["pct_close_7"])
    crit_v,   crit_src,   crit_pend   = _pick("critsit_rate", computed_critsit_rate)

    # LED assignments — KPIs with target get red/yellow/green, others blue
    dtc_led  = status_led(dtc_v,  12, higher_is_better=False) if dtc_v  is not None else LED_BLUE
    pct7_led = status_led(pct7_v, 50, higher_is_better=True)  if pct7_v is not None else LED_BLUE
    ir_led   = status_led(ir_v,   95, higher_is_better=True)  if ir_v   is not None else LED_BLUE

    # CSAT block — honour Insights+_v3 override if present, else use KPISupportData survey stats
    if csat_v is not None:
        csat_cls = _csat_class(csat_v) or ""
        # Prefer snapshot's survey stats if provided, otherwise use asw_csat computed stats
        insights_csat = kpis.get("csat_avg") or {}
        surveys_n     = insights_csat.get("surveys") if insights_csat.get("surveys") is not None else asw_csat.get("n", 0)
        response_pct  = insights_csat.get("response_pct")
        if response_pct is None:
            response_pct = round(100.0 * asw_csat.get("n", 0) / baseline["vol"], 1) if baseline["vol"] else 0.0
        dsat_n = insights_csat.get("dsat") if insights_csat.get("dsat") is not None else asw_csat.get("dsat", 0)
        csat_value = f'<div class="value {csat_cls}">{csat_v:.2f}</div>'
        csat_sub_parts = []
        if surveys_n:        csat_sub_parts.append(f"{surveys_n:,} surveys")
        if response_pct:     csat_sub_parts.append(f"{response_pct}% response")
        if dsat_n is not None: csat_sub_parts.append(f"DSAT {dsat_n}")
        csat_sub = " · ".join(csat_sub_parts) if csat_sub_parts else "&nbsp;"
        csat_led = status_led(csat_v, 4.8, higher_is_better=True)
    else:
        csat_value = '<div class="value">no surveys</div>'
        csat_sub   = 'no CSAT responses'
        csat_led   = LED_BLUE

    # Source-badge label — mixed if any Insights+_v3 override is present OR pending
    any_insights = any(v == "Insights+_v3" for v in (vol_src, closed_src, csat_src, ir_src, dtc_src, pct7_src, crit_src))
    any_pending  = any(p == "Insights+_v3" for p in (vol_pend, closed_pend, csat_pend, ir_pend, dtc_pend, pct7_pend, crit_pend))
    source_badge = "Insights+_v3 + KPISupportData" if (any_insights or any_pending) else KUSTO_DB

    # Per-KPI source suffix (tiny, muted) so reviewers can tell which came from where.
    #   I+ = live Insights+_v3 value
    #   K  = live KPISupportData value
    #   K* = KPISupportData value, but source is queued to migrate to Insights+_v3
    #        (see `pending_source` / `insights_v3_field` in asw_baseline_insights_v3.json)
    def _src_tag(src: str, pending: str = "") -> str:
        if src == "Insights+_v3":
            label = "I+"
            title = "Source: Insights+_v3"
        elif pending == "Insights+_v3":
            label = "K*"
            title = "Source: KPISupportData (pending migration to Insights+_v3 — value not yet captured)"
        else:
            label = "K"
            title = f"Source: {src}"
        return f'<span class="src-tag" title="{title}">{label}</span>'

    close_rate_display = round(100.0 * closed_v / vol_v, 1) if vol_v else 0.0

    return f"""
    <div class="section-title" style="border-left-color:#1a1a2e; color:#1a1a2e; background:linear-gradient(90deg,#f8fafc 0%,#fff 100%)">
      ASW FY26 Baseline &amp; CaaS Lead Coverage
      <span class="badge">source: {source_badge}</span>
      <span class="sub">Whole-ASW denominator built from the {baseline['vol']:,}-case snapshot. CaaS Lead focus-customer volume is a subset. <em>I+ = Insights+_v3 · K = KPISupportData · K* = pending migration to Insights+_v3</em></span>
    </div>
    <div class="mini-grid">
      <div class="card" style="border-top-color:#1a1a2e">{LED_BLUE}<div class="label">ASW Created Cases {_src_tag(vol_src, vol_pend)}</div><div class="value">{vol_v:,}</div><div class="sub">created in FY26</div></div>
      <div class="card" style="border-top-color:#1a1a2e">{LED_BLUE}<div class="label">ASW Closed Cases {_src_tag(closed_src, closed_pend)}</div><div class="value">{closed_v:,}</div><div class="sub">{close_rate_display}% close rate</div></div>
      <div class="card" style="border-top-color:#1a1a2e">{csat_led}<div class="label">ASW CSAT 5 * Avg {_src_tag(csat_src, csat_pend)}</div>{csat_value}<div class="sub">{csat_sub}</div></div>
      <div class="card" style="border-top-color:#1a1a2e">{ir_led}<div class="label">ASW IR Met% {_src_tag(ir_src, ir_pend)}</div><div class="value">{ir_v if ir_v is not None else 'n/a'}{'<span style="font-size:.7rem">%</span>' if ir_v is not None else ''}</div><div class="sub">target ≥ 95%</div></div>
      <div class="card" style="border-top-color:#1a1a2e">{dtc_led}<div class="label">ASW Avg DTC {_src_tag(dtc_src, dtc_pend)}</div><div class="value">{dtc_v}<span style="font-size:.7rem">d</span></div><div class="sub">target ≤ 12</div></div>
      <div class="card" style="border-top-color:#1a1a2e">{pct7_led}<div class="label">ASW %&lt;7d {_src_tag(pct7_src, pct7_pend)}</div><div class="value">{pct7_v}<span style="font-size:.7rem">%</span></div><div class="sub">target ≥ 50%</div></div>
      <div class="card" style="border-top-color:#1a1a2e">{LED_BLUE}<div class="label">ASW CritSit Rate {_src_tag(crit_src, crit_pend)}</div><div class="value">{crit_v}<span style="font-size:.7rem">%</span></div><div class="sub">{baseline['critsit']:,} CritSit / {baseline['vol']:,} cases</div></div>
      <div class="card" style="border-top-color:#0078d4">{LED_BLUE}<div class="label">CaaS Lead Coverage</div><div class="value">{focus_vol:,}</div><div class="sub">{focus_pct}% of ASW Created Cases · {non_focus_vol:,} non-focus</div></div>
    </div>"""


def render_manager_rollup(mgr_rows: list[dict], roster: dict[str, str]) -> str:
    """Manager-level view of focus-customer case work."""
    if not mgr_rows:
        return ""
    cards = ""
    for m in mgr_rows:
        dtc_cls = _dtc_class(m["avg_dtc"]) or ""
        pct_cls = _pct7_class(m["pct_7"]) or ""
        cards += f"""
        <div class="card" style="border-top-color:#6f42c1">
          <div class="label">{m['manager_name']}</div>
          <div class="value">{m['vol']:,}</div>
          <div class="sub">
            {m['engineers_active']}/{m['engineers_total']} eng ·
            <span class="{dtc_cls}">{m['avg_dtc']}d</span> ·
            <span class="{pct_cls}">{m['pct_7']}%&lt;7</span>
          </div>
        </div>"""
    total_vol = sum(m["vol"] for m in mgr_rows)
    total_engs_active = sum(m["engineers_active"] for m in mgr_rows)
    total_engs = sum(m["engineers_total"] for m in mgr_rows)
    return f"""
    <div class="section-title" style="border-left-color:#6f42c1; color:#6f42c1; margin-top:24px">
      Section 1a · Manager Rollup (Focus Customers Only)
      <span class="badge">{total_vol:,} focus cases · {total_engs_active}/{total_engs} eng</span>
      <span class="sub">Focus-customer case load per ASW manager — sourced from the AgentAlias→Manager mapping in <code>asw_roster_fy26.json</code></span>
    </div>
    <div class="mini-grid">{cards}</div>"""


def render_program_rollup(focus_pas: list[dict], focus: list[dict], csat_summary: dict, asw_vol: int, change_events: dict, acr_snapshot: dict) -> str:
    r = rollup(focus_pas)
    total_ss = sum(c["ss"] for c in focus)
    total_ee = sum(c["ee"] for c in focus)
    mc_count = sum(1 for c in focus if _is_mc_active(c.get("mc", "")))
    # Section 1 per-card source tag helper — mirrors baseline strip's `_src_tag`.
    # Label conventions (also documented in the Section 1 title legend):
    #   M   = Focus Master (roster / FOCUS constant)
    #   K   = KPISupportData (Kusto snapshot asw_fy26_all_cases.json)
    #   I+  = Insights+_v3 (leadership dashboard)
    #   CPE = CPE Survey (cpe_fy26_final.json)
    #   X   = FY26 ASW Cx Changing Activities xlsx
    #   CX  = CX Observe / ACR snapshot
    #   ?   = pending source (no live feed yet)
    def _s1_tag(label: str, tooltip: str) -> str:
        return f'<span class="src-tag" title="{tooltip}">{label}</span>'
    TAG_M    = _s1_tag("M",   "Master roster (FOCUS list + asw_stakeholder.json)")
    TAG_K    = _s1_tag("K",   "KPISupportData (Kusto asw_fy26_all_cases.json)")
    TAG_KI   = _s1_tag("K",   "KPISupportData (Kusto asw_fy26_all_cases.json)") + _s1_tag("I+", "Insights+_v3 (ASW Created Cases denominator)")
    TAG_CPE  = _s1_tag("CPE", "CPE Survey (cpe_fy26_final.json)")
    TAG_XLSX = _s1_tag("X",   "FY26 ASW Cx Changing Activities xlsx (SharePoint)")
    TAG_CX   = _s1_tag("CX",  "CX Observe / ACR snapshot (asw_acr_snapshot.json)")
    TAG_PEND = _s1_tag("?",   "pending source — awaiting data feed")
    # MC breakdown by workload: RISE=SAP RISE tenant, SAP=SAP Native, EPIC=Epic
    # (Note: earlier revisions grouped by cohort section R/N/E which put every
    # MC customer in the Section-R cohort into the "RISE" bucket even though most
    # were SAP Native workloads. Grouping by `workload` gives the leadership-facing
    # split by workload type, matching the FOCUS list `workload` field.)
    mc_by_wl = {"RISE": 0, "SAP": 0, "EPIC": 0}
    for c in focus:
        if _is_mc_active(c.get("mc", "")):
            wl = c.get("workload", "")
            if wl in mc_by_wl:
                mc_by_wl[wl] += 1
    coverage_pct = round(100.0 * r["vol"] / asw_vol, 1) if asw_vol else 0.0
    # CSAT card content — CaaS Lead 2.0 focus customers only
    if csat_summary["n"] > 0:
        csat_cls = _csat_class(csat_summary["avg"]) or ""
        csat_led = status_led(csat_summary["avg"], 4.8, higher_is_better=True)
        csat_value_inner = f'<div class="value {csat_cls}">{csat_summary["avg"]:.2f}</div>'
        csat_value_html = drill_span("PROGRAM", "csat", csat_value_inner)
        csat_card = (
            f'<div class="card">{csat_led}<div class="label">5 · FY26 CaaS Lead Avg CSAT {TAG_K}</div>'
            f'{csat_value_html}'
            f'<div class="sub">{csat_summary["n"]} surveys · {csat_summary["customers_with_survey"]}/{len(focus)} customers · DSAT {csat_summary["dsat"]}</div></div>'
        )
    else:
        csat_card = ('<div class="card na">' + LED_BLUE + '<div class="label">5 · FY26 CaaS Lead Avg CSAT ' + TAG_K + '</div>'
                     '<div class="value">no surveys</div><div class="sub">focus customers had 0 CSAT responses</div></div>')
    # Change Event card content — sourced from FY26 annual xlsx
    ce_link = ('<a href="https://microsoft.sharepoint.com/:x:/t/AzureStrategicWorkloads-SAP/'
               'cQq8BQ68wj2SRIsPSYUuhuM6EgUCeu633SA-bLTnZRE0eKi3wg" target="_blank" rel="noopener">'
               'FY26 ASW Cx Changing Activities ↗</a>')
    ce_total = change_events.get("total_tracked")
    if ce_total is not None:
        ce_completed = change_events.get("completed", 0)
        ce_cancelled = change_events.get("cancelled", 0)
        ce_customers = change_events.get("customers_with_event", 0)
        change_card = (
            f'<div class="card">{LED_BLUE}<div class="label">10 · FY26 Change Event Support {TAG_XLSX}</div>'
            f'<div class="value">{ce_total}</div>'
            f'<div class="sub">{ce_customers} customers · {ce_completed} completed · {ce_cancelled} cancelled · SS {total_ss} · Exec Esc {total_ee} · {ce_link}</div></div>'
        )
    else:
        change_card = (
            f'<div class="card na">{LED_BLUE}<div class="label">10 · FY26 Change Event Support {TAG_XLSX}</div>'
            f'<div class="value">pending</div><div class="sub">source: {ce_link}</div></div>'
        )
    # LEDs for DTC and %<7d cards (need conditional class for value coloring)
    dtc_val = r['avg_dtc']
    dtc_led = status_led(dtc_val, 12, higher_is_better=False) if dtc_val is not None else LED_BLUE
    pct7_val = r['pct_close_7']
    pct7_led = status_led(pct7_val, 50, higher_is_better=True) if pct7_val is not None else LED_BLUE
    # Card 11 · Azure Consumption TTM (Trailing Twelve Months, aggregated across SAP/EPIC-scoped workloads)
    acr_map = acr_snapshot.get("by_tpid", {})
    acr_meta = acr_snapshot.get("meta", {})
    acr_total = sum_section_acr(focus, acr_map, acr_meta)
    is_ttm = (acr_meta.get("metric_type") == "TTM")
    snap_month = acr_meta.get("snapshot_month", "")
    snap_label = _fmt_month_label(snap_month) or snap_month
    if acr_total is not None:
        acr_arrow = acr_trend_html(acr_total.get("delta_pct"))
        acr_abs = acr_delta_abs_html(acr_total.get("acu_this_month"), acr_total.get("prev_month"))
        if is_ttm:
            acr_card_label = f"11 · Azure Consumption (TTM) {TAG_CX}"
            acr_sub = f"TTM = Trailing Twelve Months · {acr_total['covered']}/{acr_total['total']} covered · Kusto"
        else:
            acr_card_label = f"11 · FY26 Jun Sum {TAG_CX}"
            acr_sub = (f"{acr_total['covered']}/{acr_total['total']} covered · vs prev {acr_total['prev_display']}"
                       f" ({acr_abs} ACU)" if acr_total.get('delta_pct') is not None
                       else f"Azure Consumption Units · {snap_label} · CX Observe · {acr_total['covered']}/{acr_total['total']} covered")
        acr_value_inner = f'<div class="value" title="{"Trailing Twelve Months" if is_ttm else "Monthly Consumption"}">{acr_total["acu_display"]}{acr_arrow}</div>'
        acr_value_html = drill_span("PROGRAM", "acr", acr_value_inner)
        acr_card = (
            f'<div class="card">{LED_BLUE}<div class="label">{acr_card_label}</div>'
            f'{acr_value_html}'
            f'<div class="sub">{acr_sub}</div></div>'
        )
    else:
        acr_card_label = ("11 · Azure Consumption (TTM) " + TAG_CX) if is_ttm else ("11 · FY26 Jun Sum " + TAG_CX)
        acr_card = (
            f'<div class="card na">{LED_BLUE}<div class="label">{acr_card_label}</div>'
            f'<div class="value">NA</div><div class="sub">ACR snapshot not loaded</div></div>'
        )
    return f"""
    <div class="kpi-grid">
      <div class="card">{LED_BLUE}<div class="label">1 · Focus Customers {TAG_M}</div><div class="value">{len(focus)}</div><div class="sub">SAP RISE + Mission Critical + Potential MC + RISE Selected</div></div>
      <div class="card">{LED_BLUE}<div class="label">2 · Mission Critical Customers {TAG_M}</div><div class="value">{mc_count}</div><div class="sub">Mission Critical contract active (SAP RISE: {mc_by_wl['RISE']}, SAP Native: {mc_by_wl['SAP']}, Epic: {mc_by_wl['EPIC']})</div></div>
      <div class="card">{LED_BLUE}<div class="label">3 · Total CaaS 2.0 Cover Case Creation {TAG_KI}</div>{drill_span("PROGRAM", "vol", f'<div class="value">{r["vol"]:,}</div>')}<div class="sub">{coverage_pct}% of ASW Created Cases ({r['vol']:,} / {asw_vol:,})</div></div>
      <div class="card">{LED_BLUE}<div class="label">4 · FY26 Total Case Close Volume {TAG_K}</div>{drill_span("PROGRAM", "closed", f'<div class="value">{r["closed"]:,}</div>')}<div class="sub">{round(100.0 * r['closed'] / r['vol']) if r['vol'] else 0}% close rate</div></div>
      {csat_card}
      <div class="card na">{LED_BLUE}<div class="label">6 · FY26 IR Met % {TAG_PEND}</div><div class="value">pending source</div><div class="sub">CSS A&amp;I dashboard integration required</div></div>
      <div class="card">{dtc_led}<div class="label">7 · FY26 CaaS Lead 2.0 Total Case Avg DTC {TAG_K}</div>{drill_span("PROGRAM", "dtc", f'<div class="value">{dtc_val if dtc_val is not None else "NA"}<span style="font-size:.9rem">d</span></div>')}<div class="sub">target ≤ 12 days · {r['closed']:,} closed cases</div></div>
      <div class="card">{pct7_led}<div class="label">8 · FY26 CaaS Lead 2.0 % Case Close &lt; 7 d {TAG_K}</div>{drill_span("PROGRAM", "pct7", f'<div class="value">{pct7_val if pct7_val is not None else "NA"}<span style="font-size:.9rem">%</span></div>')}<div class="sub">target ≥ 50% · {r['closed']:,} closed cases</div></div>
      <div class="card na">{LED_BLUE}<div class="label">9 · FY26 Collaborate Case Creation {TAG_PEND}</div><div class="value">pending source</div><div class="sub">needs collaborate-created flag in case schema</div></div>
      {change_card}
      {acr_card}
    </div>"""


# ---------------------------------------------------------------------------
# Support Themes (Top L2 / L3 across all focus customers)
# ---------------------------------------------------------------------------

# Color palette shared between the pie chart slices and the ordered list swatches.
# 10 distinct hues, colour-blind friendly (mixes Microsoft Blue with contrasting
# amber / green / red / purple etc.) so the top-10 items are visually separable.
THEME_PALETTE = [
    "#0078d4", "#28a745", "#f59e0b", "#dc3545", "#7c3aed",
    "#0ea5e9", "#14b8a6", "#f97316", "#6366f1", "#ec4899",
]
THEME_OTHER_COLOR = "#94a3b8"


def compute_focus_themes(cases: list[dict], focus: list[dict], top_n: int = 10) -> dict:
    """Aggregate SapSupportPathL2 / L3 case counts across all focus customer TPIDs.
    Returns top_n items for each dimension plus totals for share-of-focus calc.
    """
    focus_tpids: set[str] = set()
    for c in focus:
        t = c.get("tpid")
        if t is None:
            continue
        if isinstance(t, (list, tuple, set)):
            focus_tpids.update(str(x) for x in t)
        else:
            focus_tpids.add(str(t))
    l2_cnt: Counter = Counter()
    l3_cnt: Counter = Counter()
    focus_case_count = 0
    for r in cases:
        if str(r.get("Customer_TPID") or "") not in focus_tpids:
            continue
        focus_case_count += 1
        if r.get("SapSupportPathL2"):
            l2_cnt[r["SapSupportPathL2"]] += 1
        if r.get("SapSupportPathL3"):
            l3_cnt[r["SapSupportPathL3"]] += 1
    return dict(
        l2_top=l2_cnt.most_common(top_n),
        l3_top=l3_cnt.most_common(top_n),
        l2_total=sum(l2_cnt.values()),
        l3_total=sum(l3_cnt.values()),
        focus_case_count=focus_case_count,
    )


def _pie_svg(items: list[tuple[str, int]], total: int, size: int = 220) -> str:
    """Render an inline SVG donut chart for the given (label, count) items.
    `total` is the sum used as the 100% denominator (may be larger than
    sum(items) when items is only the top-N — the remainder becomes an
    'Other' grey slice).
    """
    if not items or total <= 0:
        return f'<svg viewBox="0 0 {size} {size}" style="width:100%;height:auto"></svg>'
    cx = cy = size / 2
    r_outer = size / 2 - 6
    r_inner = size / 4  # donut hole
    top_sum = sum(v for _, v in items)
    other = max(total - top_sum, 0)
    slices: list[tuple[str, int, str]] = [
        (lbl, cnt, THEME_PALETTE[i % len(THEME_PALETTE)])
        for i, (lbl, cnt) in enumerate(items)
    ]
    if other > 0:
        slices.append(("Other", other, THEME_OTHER_COLOR))
    # Build donut segments via SVG paths (M outer -> A outer -> L inner -> A inner -> Z)
    paths: list[str] = []
    angle = -math.pi / 2  # start at 12 o'clock
    two_pi = 2 * math.pi
    for lbl, cnt, color in slices:
        frac = cnt / total
        sweep = frac * two_pi
        end = angle + sweep
        large = 1 if sweep > math.pi else 0
        x1o = cx + r_outer * math.cos(angle);  y1o = cy + r_outer * math.sin(angle)
        x2o = cx + r_outer * math.cos(end);    y2o = cy + r_outer * math.sin(end)
        x1i = cx + r_inner * math.cos(end);    y1i = cy + r_inner * math.sin(end)
        x2i = cx + r_inner * math.cos(angle);  y2i = cy + r_inner * math.sin(angle)
        # If a single slice covers the entire ring, SVG A cannot draw a full circle;
        # emit two concentric circles instead (outer filled, inner as hole).
        if frac >= 0.999:
            paths.append(
                f'<circle cx="{cx}" cy="{cy}" r="{r_outer}" fill="{color}"/>'
                f'<circle cx="{cx}" cy="{cy}" r="{r_inner}" fill="var(--card-bg,#fff)"/>'
            )
        else:
            d = (f"M {x1o:.2f} {y1o:.2f} "
                 f"A {r_outer:.2f} {r_outer:.2f} 0 {large} 1 {x2o:.2f} {y2o:.2f} "
                 f"L {x1i:.2f} {y1i:.2f} "
                 f"A {r_inner:.2f} {r_inner:.2f} 0 {large} 0 {x2i:.2f} {y2i:.2f} Z")
            pct = frac * 100
            safe_lbl = html.escape(lbl)
            paths.append(
                f'<path d="{d}" fill="{color}" stroke="var(--card-bg,#fff)" stroke-width="1.5">'
                f'<title>{safe_lbl} — {cnt:,} ({pct:.1f}%)</title></path>'
            )
        angle = end
    center_txt = (
        f'<text x="{cx}" y="{cy - 4}" text-anchor="middle" '
        f'style="font-size:1.15rem;font-weight:700;fill:var(--dark,#1a1a2e)">{total:,}</text>'
        f'<text x="{cx}" y="{cy + 14}" text-anchor="middle" '
        f'style="font-size:.6rem;fill:#64748b;text-transform:uppercase;letter-spacing:.05em">cases</text>'
    )
    return (f'<svg viewBox="0 0 {size} {size}" role="img" '
            f'style="width:100%;height:auto;max-width:{size}px">'
            + "".join(paths) + center_txt + "</svg>")


def _theme_list(items: list[tuple[str, int]], total: int) -> str:
    """Render the ordered list to the right of the pie chart.
    Each item shows a colour swatch matching the pie slice + label + count + %.
    """
    if not items:
        return '<div class="theme-empty">No data</div>'
    rows: list[str] = []
    top_sum = sum(v for _, v in items)
    for i, (lbl, cnt) in enumerate(items):
        color = THEME_PALETTE[i % len(THEME_PALETTE)]
        pct = (cnt / total * 100) if total else 0
        rows.append(
            f'<li><span class="theme-swatch" style="background:{color}"></span>'
            f'<span class="theme-lbl">{html.escape(lbl)}</span>'
            f'<span class="theme-cnt">{cnt:,}</span>'
            f'<span class="theme-pct">{pct:.1f}%</span></li>'
        )
    other = max(total - top_sum, 0)
    if other > 0:
        pct = other / total * 100
        rows.append(
            f'<li class="theme-other"><span class="theme-swatch" style="background:{THEME_OTHER_COLOR}"></span>'
            f'<span class="theme-lbl">Other</span>'
            f'<span class="theme-cnt">{other:,}</span>'
            f'<span class="theme-pct">{pct:.1f}%</span></li>'
        )
    return f'<ol class="theme-list">{"".join(rows)}</ol>'


def _themes_insights(themes: dict) -> list[str]:
    """Auto-derive 3 bullet insights from the L2/L3 counters.

    Each bullet is a pre-formatted HTML snippet (already escape-safe).
    Insights are data-driven so they stay accurate month over month.
    """
    l2_top   = themes["l2_top"]
    l3_top   = themes["l3_top"]
    l2_total = themes["l2_total"]
    l3_total = themes["l3_total"]
    bullets: list[str] = []

    # Insight 1 · Concentration of the top-3 L2 paths (surface how compute-heavy
    # the case load is, and highlight the single most dominant product family).
    if l2_top and l2_total > 0:
        top_lbl, top_cnt = l2_top[0]
        top_pct = top_cnt / l2_total * 100
        top3_sum = sum(v for _, v in l2_top[:3])
        top3_pct = top3_sum / l2_total * 100
        bullets.append(
            f"<strong>Compute-heavy footprint</strong> — <strong>{html.escape(top_lbl)}</strong> alone drives "
            f"<strong>{top_pct:.1f}%</strong> of L2 cases; the top 3 L2 paths cover "
            f"<strong>{top3_pct:.1f}%</strong> of {l2_total:,} tagged cases."
        )

    # Insight 2 · Leading L3 scenario (translates a product line into an
    # actionable failure mode reviewers should prioritise).
    if l3_top and l3_total > 0:
        top_lbl, top_cnt = l3_top[0]
        top_pct = top_cnt / l3_total * 100
        bullets.append(
            f"<strong>{html.escape(top_lbl)}</strong> is the #1 scenario — "
            f"<strong>{top_cnt:,} cases ({top_pct:.1f}%)</strong> of tagged L3, "
            f"pointing at VM stability &amp; availability as the recurring support burden for focus customers."
        )

    # Insight 3 · Strategic workload share (SAP on Azure + Epic on Azure — the
    # workloads ASW is explicitly funded to defend). Everything else sits under
    # Compute/Network sub-paths and needs deeper drill to attribute back to SAP/Epic.
    strategic_labels = {"SAP on Azure", "Epic on Azure"}
    strategic_hits = [(lbl, cnt) for lbl, cnt in l2_top if lbl in strategic_labels]
    if l2_total > 0:
        if strategic_hits:
            s_sum = sum(cnt for _, cnt in strategic_hits)
            s_pct = s_sum / l2_total * 100
            parts = " + ".join(
                f"{html.escape(lbl)} ({cnt:,})" for lbl, cnt in strategic_hits
            )
            bullets.append(
                f"<strong>Native SAP/Epic workloads visible directly</strong>: {parts} = "
                f"<strong>{s_pct:.1f}%</strong> of L2 — the remainder sits under Compute/Network sub-paths, "
                f"suggesting most SAP/Epic outages are logged against the underlying IaaS product."
            )
        else:
            bullets.append(
                "<strong>SAP/Epic on Azure not in top L2</strong> — cases are logged against the "
                "underlying IaaS product (VM / Network / Storage) instead of the workload path."
            )
    return bullets


def render_focus_themes(themes: dict) -> str:
    """Build the 'Support Themes Across Focus Customers' block: two side-by-side
    panels (Top L2 / Top L3), each with a donut chart + ranked list.
    Inserted between the 11-card program rollup and the Legend section.
    """
    l2_top   = themes["l2_top"]
    l3_top   = themes["l3_top"]
    l2_total = themes["l2_total"]
    l3_total = themes["l3_total"]
    case_n   = themes["focus_case_count"]
    insight_bullets = _themes_insights(themes)
    insights_html = ""
    if insight_bullets:
        items = "".join(f"<li>{b}</li>" for b in insight_bullets)
        insights_html = (
            '<div class="theme-insights">'
            '<div class="theme-insights-head">Key Take Away</div>'
            f'<ul>{items}</ul>'
            '</div>'
        )
    return f"""
    <div class="section-title" style="border-left-color:var(--dark); color:var(--dark); margin-top:24px">
      Support Themes Across Focus Customers
      <span class="badge">{case_n:,} focus cases</span>
      <span class="sub">Top issue families from <code>SapSupportPathL2</code> / <code>SapSupportPathL3</code> in KPISupportData.
        Hover a slice for exact case count &amp; share.</span>
    </div>
    <div class="themes-grid">
      <div class="theme-panel">
        <div class="theme-head">Top L2 paths <span class="theme-sub">{len(l2_top)} of {l2_total:,} tagged</span></div>
        <div class="theme-body">
          <div class="theme-chart">{_pie_svg(l2_top, l2_total)}</div>
          {_theme_list(l2_top, l2_total)}
        </div>
      </div>
      <div class="theme-panel">
        <div class="theme-head">Top L3 paths <span class="theme-sub">{len(l3_top)} of {l3_total:,} tagged</span></div>
        <div class="theme-body">
          <div class="theme-chart">{_pie_svg(l3_top, l3_total)}</div>
          {_theme_list(l3_top, l3_total)}
        </div>
      </div>
    </div>
    {insights_html}
    """


def render_customer_card(f: dict, pa: dict, cs: dict, show_acr: bool = False, acr_entry: dict | None = None, wiki_entry: dict | None = None, review_entry: dict | None = None) -> str:
    ph_cls = phase_class(f["stage"])
    dkey = _tpid_key(f)
    # Per-KPI LEDs (only target-based KPIs get red/yellow/green; blue when no data)
    dtc_led  = status_led(pa['avg_dtc'],     12, higher_is_better=False) if pa['avg_dtc']     is not None else LED_BLUE
    pct7_led = status_led(pa['pct_close_7'], 50, higher_is_better=True)  if pa['pct_close_7'] is not None else LED_BLUE
    csat_led = status_led(cs['avg'],        4.8, higher_is_better=True)  if cs['n'] > 0                   else LED_BLUE
    tpid_val = f["tpid"]
    if tpid_val is None:
        tpid_str = "TPID —"
    elif isinstance(tpid_val, (list, tuple, set)):
        tpid_str = f"TPID {' / '.join(str(t) for t in tpid_val)}"
    else:
        tpid_str = f"TPID {tpid_val}"
    zone_str = f"Zone {f['zone']}" if f["zone"] else "All Zones"
    queue_hint = f'<br><span style="font-size:.62rem;color:#6f42c1;font-weight:600">Queue: {f["queue"]}</span>' if f.get("queue") else ""
    # CSAT metric: show "{avg} (n=xx)" if we have surveys, else NA
    if cs["n"] > 0:
        cs_cls = _csat_class(cs["avg"]) or ""
        csat_inner = f'<span class="m-value {cs_cls}">{cs["avg"]:.2f}<span style="font-size:.6rem;color:#94a3b8;margin-left:3px">n={cs["n"]}</span></span>'
        csat_html = drill_span(dkey, "csat", csat_inner)
    else:
        csat_html = '<span class="m-value na">no surveys</span>'
    # ACR metric — only shown when show_acr flag is on.
    # Value = TTM Consumption (Trailing Twelve Months) sourced from Kusto
    # WorkloadSearchSummarized.Consumption; monthly MoM is not available so
    # `prev_month` / `delta_pct` are null and the arrow is suppressed.
    if show_acr:
        # Determine metric label once (falls back to legacy label when metric_type absent)
        acr_label_text = "Azure Consumption (TTM)"
        if acr_entry:
            arrow = acr_trend_html(acr_entry.get("delta_pct"))
            abs_delta = acr_delta_abs_html(acr_entry.get("acu_this_month"), acr_entry.get("prev_month"))
            is_ttm_entry = (acr_entry.get("prev_month") is None and acr_entry.get("delta_pct") is None)
            if is_ttm_entry:
                tooltip = f"Trailing Twelve Months (TTM) · {acr_entry['acu_display']} ACU"
                sub_line = ''
            else:
                cur_lbl  = acr_entry.get("cur_month_label")  or "this month"
                prev_lbl = acr_entry.get("prev_month_label") or "prev"
                tooltip = (f"{cur_lbl} {acr_entry['acu_display']} vs {prev_lbl} {acr_entry.get('prev_display','—')}"
                           + (f" ({acr_entry['delta_pct']:+.2f}%, {abs_delta} ACU)" if acr_entry.get('delta_pct') is not None else ""))
                sub_line = (f'<span style="display:block;font-size:.6rem;color:#94a3b8;line-height:1">{abs_delta} vs {acr_entry.get("prev_display","—")}</span>'
                            if abs_delta else '')
            acr_inner = (f'<span class="m-value" title="{tooltip}">{acr_entry["acu_display"]}{arrow}{sub_line}</span>')
            acr_val_html = drill_span(dkey, "acr", acr_inner)
            acr_html = (f'<div class="metric"><span class="m-label" title="TTM = Trailing Twelve Months">{LED_BLUE}{acr_label_text}</span>{acr_val_html}</div>')
        else:
            acr_html = (f'<div class="metric"><span class="m-label" title="TTM = Trailing Twelve Months">{LED_BLUE}{acr_label_text}</span>'
                        f'<span class="m-value na" style="font-size:.75rem">N/A</span></div>')
    else:
        acr_html = ''
    # Wrap numeric KPI values with drill spans
    vol_html    = drill_span(dkey, "vol",    f'<span class="m-value">{pa["vol"]}</span>')
    closed_html = drill_span(dkey, "closed", f'<span class="m-value">{pa["closed"]}</span>')
    crit_pct_txt = (str(round(100.0 * pa['critsit'] / pa['vol'], 1)) + '%') if pa['vol'] else 'NA'
    crit_inner   = f'<span class="m-value" title="{pa["critsit"]} CritSit / {pa["vol"]} cases">{crit_pct_txt}<span style="font-size:.6rem;color:#94a3b8;margin-left:3px">n={pa["critsit"]}</span></span>'
    crit_html    = drill_span(dkey, "critsit", crit_inner) if pa['critsit'] > 0 else crit_inner
    dtc_inner    = f'<span class="m-value {_dtc_class(pa["avg_dtc"]) or ""}">{"NA" if pa["avg_dtc"] is None else str(pa["avg_dtc"]) + "d"}</span>'
    dtc_html     = drill_span(dkey, "dtc", dtc_inner) if pa['avg_dtc'] is not None else dtc_inner
    pct7_inner   = f'<span class="m-value {_pct7_class(pa["pct_close_7"]) or ""}">{"NA" if pa["pct_close_7"] is None else str(pa["pct_close_7"]) + "%"}</span>'
    pct7_html    = drill_span(dkey, "pct7", pct7_inner) if pa['pct_close_7'] is not None else pct7_inner
    # Customer-name display: if we have a CaaS Lead review entry, wrap the
    # name in a clickable link that opens the review modal (v2.14). Otherwise
    # render it as plain text.
    cust_name = f['customer']
    if review_entry:
        name_html = (
            f'<a href="#" class="review-link" data-review-key="{dkey}" '
            f'title="Open latest CaaS Lead review">{cust_name}</a>'
        )
    else:
        name_html = cust_name
    return f"""
    <div class="cust-card {ph_cls}">
      <div class="name">{name_html}<span class="tpid">{tpid_str}</span></div>
      <div class="cx-meta">{zone_str} · {f['workload']} · Lead: {f['lead']}{queue_hint}</div>
      <div class="metrics">
        <div class="metric"><span class="m-label">Case Vol</span>{vol_html}</div>
        <div class="metric"><span class="m-label">Closed</span>{closed_html}</div>
        <div class="metric"><span class="m-label">CritSit %</span>{crit_html}</div>
        <div class="metric"><span class="m-label">{dtc_led}Avg DTC</span>{dtc_html}</div>
        <div class="metric"><span class="m-label">{pct7_led}%&lt;7d</span>{pct7_html}</div>
        <div class="metric"><span class="m-label">{csat_led}CSAT</span>{csat_html}</div>
        <div class="metric"><span class="m-label">#Story</span><span class="m-value">{f['ss']}</span></div>
        <div class="metric"><span class="m-label">#Event Support</span><span class="m-value">{f['ce']}</span></div>
        <div class="metric"><span class="m-label">#Exec Escalation</span><span class="m-value">{f['ee']}</span></div>
        {acr_html}
      </div>
      <div class="tags">
        {fmt_stage(f['stage'])}
        {fmt_mc(f['mc'])}
        <span title="Case Analysis & Support Insight regular delivery" style="font-size:.66rem;color:#64748b">Insight Deliver {fmt_status(f['ca'])}</span>
        {wiki_tag(dkey, wiki_entry)}
      </div>
    </div>"""


def render_detail_table(customers: list[dict], pas: list[dict], css: list[dict]) -> str:
    body_rows = []
    for f, pa, cs in zip(customers, pas, css):
        t = f["tpid"]
        if t is None:
            tpid = "—"
        elif isinstance(t, (list, tuple, set)):
            tpid = " / ".join(str(x) for x in t)
        else:
            tpid = str(t)
        dtc_html = f'<span class="{_dtc_class(pa["avg_dtc"])}">{pa["avg_dtc"]}d</span>' if pa["avg_dtc"] is not None else '<span class="na">NA</span>'
        pct7_html = f'<span class="{_pct7_class(pa["pct_close_7"])}">{pa["pct_close_7"]}%</span>' if pa["pct_close_7"] is not None else '<span class="na">NA</span>'
        crit_html = '0' if pa["critsit"] == 0 else f'<span class="critsit-flag">{pa["critsit"]}</span>'
        if cs["n"] > 0:
            csat_html = f'<span class="{_csat_class(cs["avg"]) or ""}">{cs["avg"]:.2f}</span><br><span style="font-size:.62rem;color:#94a3b8">n={cs["n"]}</span>'
            dsat_html = str(cs["dsat"]) if cs["dsat"] == 0 else f'<span class="critsit-flag">{cs["dsat"]}</span>'
        else:
            csat_html = '<span class="na">no surveys</span>'
            dsat_html = '<span class="na">—</span>'
        body_rows.append(f"""
        <tr>
          <td class="customer">{f['customer']}<br><span style="font-size:.64rem;font-weight:400;color:#94a3b8">TPID {tpid} · Z{f['zone']} · {f['workload']}</span></td>
          <td class="lead">{f['lead']}</td>
          <td>{fmt_stage(f['stage'])}</td>
          <td><strong>{pa['vol']}</strong></td>
          <td>{pa['closed']}</td>
          <td>{dtc_html}</td>
          <td>{pct7_html}</td>
          <td>{crit_html}</td>
          <td>{csat_html}</td>
          <td>{dsat_html}</td>
          <td class="na">NA</td>
          <td class="topics">{fmt_topics(pa['top_l2'])}</td>
          <td class="topics">{fmt_topics(pa['top_l3'])}</td>
          <td>{fmt_bool(f['ca'])}</td>
          <td>{fmt_bool(f['ai'])}</td>
          <td>{fmt_bool(f['wiki'])}</td>
          <td>{f['ss']}</td>
          <td>{f['ce']}</td>
          <td>{f['ee']}</td>
          <td>{fmt_mc(f['mc'])}</td>
          <td class="na">NA</td>
        </tr>""")
    return f"""
    <div class="table-wrapper">
      <table>
        <thead>
          <tr>
            <th rowspan="2" style="text-align:left">Customer</th>
            <th rowspan="2" style="text-align:left">CaaS Lead</th>
            <th rowspan="2">Stage</th>
            <th colspan="10" style="background:#e7f0fb; color:#1e40af;">Panel A · Support Delivery (FY26)</th>
            <th colspan="6" style="background:#fef3c7; color:#854d0e;">Panel B · Program Indicators</th>
            <th rowspan="2">MC Contract</th>
            <th rowspan="2">ACR YoY %</th>
          </tr>
          <tr>
            <th>Case Vol</th><th>Closed</th><th>Avg DTC</th><th>%&lt;7d</th><th>CritSit</th>
            <th>CSAT</th><th>DSAT</th><th>IR%</th>
            <th>Top L2 (Product)</th><th>Top L3 (Scenario)</th>
            <th>Case Analysis</th><th>+AI</th><th>Wiki/PoR</th>
            <th>#Success</th><th>#Change Evt</th><th>#Exec Esc</th>
          </tr>
        </thead>
        <tbody>{''.join(body_rows)}</tbody>
      </table>
    </div>"""


def render_section(letter: str, customers: list[dict], cases: list[dict],
                    csat: dict[str, list[int]], with_table: bool, acr_snapshot: dict | None = None,
                    wiki_summaries: dict | None = None, review_summaries: dict | None = None) -> str:
    meta = SECTIONS[letter]
    pas = [compute_panel_a(cases, c["tpid"], c.get("queue")) for c in customers]
    css = [csat_stats(csat, c["tpid"]) for c in customers]
    acr_map = (acr_snapshot or {}).get("by_tpid", {})
    acr_meta = (acr_snapshot or {}).get("meta", {})
    snap_month = acr_meta.get("snapshot_month", "")
    snap_label = _fmt_month_label(snap_month) or snap_month
    wiki_map = (wiki_summaries or {}).get("by_key", {})
    review_map = (review_summaries or {}).get("by_key", {})
    sub = rollup(pas)
    sub_ss = sum(c["ss"] for c in customers)
    sub_ce = sum(c["ce"] for c in customers)
    sub_ee = sum(c["ee"] for c in customers)
    sub_ca = sum(1 for c in customers if c["ca"])
    sub_mc = sum(1 for c in customers if _is_mc_active(c["mc"]))
    sub_phase4 = sum(1 for c in customers if "phase 4" in c["stage"].lower())

    # Per-card source tags — mirrors Section 1's `_s1_tag` pattern.
    #   M   = Master roster (FOCUS list + asw_stakeholder.json)
    #   K   = KPISupportData (Kusto asw_fy26_all_cases.json)
    #   X   = FY26 ASW Cx Changing Activities xlsx
    #   CX  = CX Observe / ACR snapshot
    def _s_tag(label: str, tooltip: str) -> str:
        return f'<span class="src-tag" title="{tooltip}">{label}</span>'
    TAG_M  = _s_tag("M",  "Master roster (FOCUS list + asw_stakeholder.json)")
    TAG_K  = _s_tag("K",  "KPISupportData (Kusto asw_fy26_all_cases.json)")
    TAG_X  = _s_tag("X",  "FY26 ASW Cx Changing Activities xlsx (SharePoint)")
    TAG_CX = _s_tag("CX", "CX Observe / ACR snapshot (asw_acr_snapshot.json)")
    TAG_MX = TAG_M + TAG_X  # combined: Master (Story/ExecEsc) + xlsx (Event Support)

    # Distinct engineers touching cohort cases
    cohort_tpids = set()
    for c in customers:
        t = c["tpid"]
        if t is None:
            continue
        if isinstance(t, (list, tuple, set)):
            cohort_tpids.update(str(x) for x in t)
        else:
            cohort_tpids.add(str(t))
    eng_count = cohort_engineers(cases, cohort_tpids)

    # Cohort CSAT rollup
    cohort_surveys = [x for cs in css for x in [cs] if cs["n"] > 0]
    cohort_scores_n = sum(cs["n"] for cs in css)
    sec_key = f"SECTION_{letter}"
    if cohort_scores_n > 0:
        weighted_avg = round(sum(cs["avg"] * cs["n"] for cs in css if cs["n"] > 0) / cohort_scores_n, 2)
        cohort_dsat = sum(cs["dsat"] for cs in css)
        cohort_csat_led = status_led(weighted_avg, 4.8, higher_is_better=True)
        csat_val_html = drill_span(sec_key, "csat", f'<div class="value {_csat_class(weighted_avg) or ""}">{weighted_avg:.2f}</div>')
        cohort_csat_card = (f'<div class="card" style="border-top-color:{meta["color"]}">{cohort_csat_led}<div class="label">Avg CSAT {TAG_K}</div>'
                            f'{csat_val_html}'
                            f'<div class="sub">n={cohort_scores_n} · DSAT {cohort_dsat}</div></div>')
    else:
        cohort_csat_card = (f'<div class="card" style="border-top-color:{meta["color"]}">{LED_BLUE}<div class="label">Avg CSAT {TAG_K}</div>'
                            f'<div class="value na" style="font-size:.9rem">no surveys</div><div class="sub">0 CSAT responses</div></div>')

    # Section summary LEDs — only KPIs with targets get red/yellow/green
    dtc_led  = status_led(sub['avg_dtc'],     12, higher_is_better=False) if sub['avg_dtc']     is not None else LED_BLUE
    pct7_led = status_led(sub['pct_close_7'], 50, higher_is_better=True)  if sub['pct_close_7'] is not None else LED_BLUE
    ca_pct   = round(100.0 * sub_ca / len(customers), 1) if customers else 0
    ca_led   = status_led(ca_pct, 100, higher_is_better=True)
    critsit_pct = round(100.0 * sub['critsit'] / sub['vol'], 1) if sub['vol'] else 0.0

    # Section ACR card — TTM Consumption aggregated across SAP/EPIC workloads in this section
    section_acr = sum_section_acr(customers, acr_map, acr_meta) if acr_map else None
    is_ttm = (acr_meta.get("metric_type") == "TTM")
    sec_acr_label = (f"Azure Consumption (TTM) {TAG_CX}" if is_ttm
                     else f"FY26 Jun Sum {TAG_CX}")
    if section_acr:
        s_arrow = acr_trend_html(section_acr.get("delta_pct"))
        s_abs = acr_delta_abs_html(section_acr.get("acu_this_month"), section_acr.get("prev_month"))
        if is_ttm:
            s_sub = f"TTM = Trailing Twelve Months · {section_acr['covered']}/{section_acr['total']} covered"
        else:
            s_sub = (f"Azure Consumption Units · {snap_label} · "
                     f"{section_acr['covered']}/{section_acr['total']} covered"
                     f" · vs prev {section_acr['prev_display']} ({s_abs} ACU)"
                     if section_acr.get('delta_pct') is not None
                     else f"Azure Consumption Units · {snap_label} · {section_acr['covered']}/{section_acr['total']} covered")
        s_acr_val_html = drill_span(sec_key, "acr", f'<div class="value" title="{"Trailing Twelve Months" if is_ttm else "Monthly Consumption"}">{section_acr["acu_display"]}{s_arrow}</div>')
        section_acr_card = (
            f'<div class="card" style="border-top-color:{meta["color"]}">{LED_BLUE}<div class="label">{sec_acr_label}</div>'
            f'{s_acr_val_html}'
            f'<div class="sub">{s_sub}</div></div>'
        )
    else:
        section_acr_card = (
            f'<div class="card na" style="border-top-color:{meta["color"]}">{LED_BLUE}<div class="label">{sec_acr_label}</div>'
            f'<div class="value">N/A</div><div class="sub">no ACR data for this section</div></div>'
        )

    sub_row = f"""
    <div class="mini-grid">
      <div class="card" style="border-top-color:{meta['color']}">{LED_BLUE}<div class="label">Customers {TAG_M}</div><div class="value">{len(customers)}</div><div class="sub">{sub_phase4} Phase 4 · {sub_mc} MC</div></div>
      <div class="card" style="border-top-color:{meta['color']}">{LED_BLUE}<div class="label">Case Volume {TAG_K}</div>{drill_span(sec_key, "vol", f'<div class="value">{sub["vol"]:,}</div>')}<div class="sub">{sub['closed']:,} closed</div></div>
      {cohort_csat_card}
      <div class="card" style="border-top-color:{meta['color']}">{dtc_led}<div class="label">Avg DTC {TAG_K}</div>{drill_span(sec_key, "dtc", f'<div class="value">{sub["avg_dtc"] if sub["avg_dtc"] is not None else "NA"}<span style="font-size:.7rem">d</span></div>')}<div class="sub">target ≤ 12</div></div>
      <div class="card" style="border-top-color:{meta['color']}">{pct7_led}<div class="label">%&lt;7d {TAG_K}</div>{drill_span(sec_key, "pct7", f'<div class="value">{sub["pct_close_7"] if sub["pct_close_7"] is not None else "NA"}<span style="font-size:.7rem">%</span></div>')}<div class="sub">target ≥ 50%</div></div>
      <div class="card" style="border-top-color:{meta['color']}">{LED_BLUE}<div class="label">CritSit Rate {TAG_K}</div>{drill_span(sec_key, "critsit", f'<div class="value">{critsit_pct}<span style="font-size:.7rem">%</span></div>')}<div class="sub">{sub['critsit']:,} CritSit / {sub['vol']:,} cases</div></div>
      <div class="card" style="border-top-color:{meta['color']}">{ca_led}<div class="label">Case Insight Deliver {TAG_M}</div><div class="value">{sub_ca}/{len(customers)}</div><div class="sub">target 100% delivered</div></div>
      <div class="card" style="border-top-color:{meta['color']}">{LED_BLUE}<div class="label">Story / Event Support / Exec Escalation {TAG_MX}</div><div class="value" style="font-size:1.1rem">{sub_ss} / {sub_ce} / {sub_ee}</div><div class="sub">FY26 cumulative</div></div>
      {section_acr_card}
    </div>"""

    show_acr = (letter in ('R', 'E', 'N', 'S'))
    # Sort customer cards by Case Volume desc (ties broken by customer name asc)
    card_triples = sorted(
        zip(customers, pas, css),
        key=lambda t: (-(t[1].get('vol') or 0), t[0]['customer'].lower())
    )
    cards = '<div class="cust-grid">' + ''.join(
        render_customer_card(
            f, pa, cs, show_acr=show_acr,
            acr_entry=acr_for_focus(f, acr_map, acr_meta) if acr_map else None,
            wiki_entry=wiki_map.get(_tpid_key(f)),
            review_entry=review_map.get(_tpid_key(f)),
        )
        for f, pa, cs in card_triples
    ) + '</div>'
    table = render_detail_table(customers, pas, css) if with_table else ''

    return f"""
    <div class="section-title" style="border-left-color:{meta['color']}; color:{meta['color']}">
      {meta['title']}
      <span class="badge">{len(customers)} customers</span>
      <span class="sub">{meta['subtitle']}
        <em>Sources: {TAG_M}
        <a href="https://microsoft.sharepoint.com/teams/AzureStrategicWorkloads-SAP/Shared%20Documents/Forms/AllItems.aspx?id=%2Fteams%2FAzureStrategicWorkloads%2DSAP%2FShared%20Documents%2FGeneral%2FCxOutreach" target="_blank" rel="noopener">Focus Master ↗</a> ·
        {TAG_K} KPISupportData (Kusto <code>asw_fy26_all_cases.json</code> · CPE Survey <code>cpe_fy26_final.json</code>) ·
        {TAG_X}
        <a href="https://microsoft.sharepoint.com/:x:/t/AzureStrategicWorkloads-SAP/cQq8BQ68wj2SRIsPSYUuhuM6EgUCeu633SA-bLTnZRE0eKi3wg" target="_blank" rel="noopener">FY26 ASW Cx Changing Activities ↗</a> ·
        {TAG_CX}
        <a href="https://cxp.azure.com/cxobserve/home" target="_blank" rel="noopener">CX Observe ↗</a></em>
      </span>
    </div>
    {sub_row}
    {cards}
    {table}
    """


def render(cases: list[dict]) -> str:
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    roster = load_roster()
    csat = load_csat()
    # Raw CSAT rows (needed for drill-down modal — load_csat() returns aggregate only)
    csat_raw = json.loads(CSAT_JSON.read_text(encoding="utf-8")) if CSAT_JSON.exists() else []
    baseline = compute_asw_baseline(cases)
    focus_pas = [compute_panel_a(cases, c["tpid"], c.get("queue")) for c in FOCUS]
    focus_vol = sum(pa["vol"] for pa in focus_pas)
    csat_summary = csat_rollup_focus(csat, FOCUS)

    # Build focus TPID set for manager rollup (flatten multi-TPID)
    focus_tpid_set: set[str] = set()
    for c in FOCUS:
        t = c["tpid"]
        if t is None:
            continue
        if isinstance(t, (list, tuple, set)):
            focus_tpid_set.update(str(x) for x in t)
        else:
            focus_tpid_set.add(str(t))
    mgr_rows = compute_manager_rollup(cases, roster, focus_tpid_set)

    asw_csat_total       = csat_asw_total(csat)
    acr_snapshot         = load_acr_snapshot()
    insights_snapshot    = load_insights_v3_baseline()
    wiki_summaries       = load_wiki_summaries()
    review_summaries     = load_review_summaries()
    # Effective ASW-wide denominator for coverage %: prefer Insights+_v3 `ASW Created Cases`
    # override (aligns with the leadership-facing dashboard), else KPISupportData fallback.
    _iv_case_vol = ((insights_snapshot or {}).get("kpis", {}).get("case_vol") or {}).get("value")
    effective_asw_vol = _iv_case_vol if _iv_case_vol is not None else baseline["vol"]
    baseline_html        = render_asw_baseline(baseline, focus_vol, asw_csat_total, insights_snapshot)
    program_rollup_html  = render_program_rollup(focus_pas, FOCUS, csat_summary, effective_asw_vol, load_change_events(), acr_snapshot)
    focus_themes_html    = render_focus_themes(compute_focus_themes(cases, FOCUS, top_n=10))
    manager_rollup_html  = render_manager_rollup(mgr_rows, roster)

    sections_html = ""
    # All four cohort sections (R, E, N, S) go into cohort tabs — table format enabled for all
    tab_config = [
        ("R", "SAP RISE + SAP Native MC",       "Mission Critical (Renew) + MC contracts", "#0078d4"),
        ("E", "EPIC — Mission Critical",         "Epic on Azure — MC customers",            "#28a745"),
        ("N", "SAP Native / Epic Potential MC",  "Potential MC · high-volume · pipeline",   "#f59e0b"),
        ("S", "SAP RISE Selected",               "GM & CVS · pre-onboarding",               "#7c3aed"),
    ]
    tab_buttons = []
    tab_panes = []
    for i, (letter, title, subtitle, color) in enumerate(tab_config):
        cust = [c for c in FOCUS if c["section"] == letter]
        pane_html = render_section(letter, cust, cases, csat, with_table=True, acr_snapshot=acr_snapshot, wiki_summaries=wiki_summaries, review_summaries=review_summaries)
        active_cls = " active" if i == 0 else ""
        tab_buttons.append(
            f'<button class="tab-btn{active_cls}" data-tab="tab-{letter}" style="--tab-color:{color}">'
            f'<span class="tab-title" style="color:{color}">{title}</span>'
            f'<span class="tab-sub">{subtitle} · {len(cust)} customers</span>'
            f'</button>'
        )
        tab_panes.append(f'<div class="tab-pane{active_cls}" id="tab-{letter}">{pane_html}</div>')

    tabs_html = (
        '<div class="cohort-tabs">'
        '<div class="tab-bar" role="tablist">' + "".join(tab_buttons) + '</div>'
        + "".join(tab_panes) +
        '</div>'
    )

    sections_html = tabs_html

    # Drill-down dataset (embedded as JSON at page bottom, wired via JS modal)
    drill_data = build_drill_dataset(cases, csat_raw, FOCUS, acr_snapshot)
    drill_json = json.dumps(drill_data, ensure_ascii=False, separators=(',', ':'))
    # Neutralise any </script> or HTML-comment sequences that could escape the JSON <script> block
    drill_json = drill_json.replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')

    # Wiki summaries dataset (embedded as JSON, powers the Wiki tag modal)
    wiki_json = json.dumps(wiki_summaries, ensure_ascii=False, separators=(',', ':'))
    wiki_json = wiki_json.replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')

    # CaaS Lead review summaries dataset (embedded as JSON, powers the review-link modal - v2.14)
    review_json = json.dumps(review_summaries, ensure_ascii=False, separators=(',', ':'))
    review_json = review_json.replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ASW CaaS Lead 2.0 &mdash; {FY_LABEL} Monthly Business Insight (V2)</title>
<script>
  // Apply saved theme immediately to avoid flash-of-light on reload
  (function() {{
    try {{
      var t = localStorage.getItem('caas-theme');
      if(t !== 'dark' && t !== 'light') {{
        t = (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) ? 'dark' : 'light';
      }}
      document.documentElement.setAttribute('data-theme', t);
    }} catch(_) {{ /* ignore */ }}
  }})();
</script>
<style>{CSS}</style>
</head>
<body>
<button class="theme-toggle" id="themeToggle" type="button" aria-label="Toggle light/dark theme" title="Toggle light/dark theme (Alt+T)">
  <span class="tt-icon" id="ttIcon">🌙</span>
  <span class="tt-label" id="ttLabel">Dark</span>
</button>
<button class="datasource-toggle" id="dsToggle" type="button" aria-label="View data sources" title="View data sources (Alt+D)">
  <span class="ds-icon">🗂️</span>
  <span class="ds-label">Data Source</span>
</button>
<div class="header">
  <h1>Program &mdash; CaaS Lead 2.0 Rollup (Mission Critical, Potential MC &amp; RISE Selected)</h1>
  <div class="subtitle">{FY_LABEL} Monthly Business Insight Dashboard · V2 · {FY_WINDOW}</div>
  <div class="meta">
    <span>Sponsor: Steve Pogge</span>
    <span>Program Owners: Kirk Beller &amp; Jacob Wang</span>
    <span>PM: Tiago Simões</span>
    <span>Generated: {generated}</span>
  </div>
  <div class="meta" style="margin-top:4px; opacity:.55">
    <span>Kusto: <code>{KUSTO_CLUSTER}</code></span>
    <span>DB: <code>{KUSTO_DB}</code></span>
    <span>Table: <code>{KUSTO_TABLE}</code></span>
    <span>Roster: {len(roster)} engineers ({len({m for m in roster.values()})} managers)</span>
    <span>Snapshot: {len(cases):,} cases</span>
  </div>
</div>

<div class="container">

  {baseline_html}

  <div class="section-title" style="border-left-color:var(--dark); color:var(--dark)">
    Section 1 · CaaS Lead 2.0 Rollup (Focus Customers)
    <span class="badge">{len(FOCUS)} focus customers</span>
    <span class="sub">Aggregate FY26 support delivery across all 4 cohorts (SAP RISE + Mission Critical + Potential MC + RISE Selected).
      <em>Sources: <span class="src-tag" title="Master roster">M</span>
      <a href="https://microsoft.sharepoint.com/teams/AzureStrategicWorkloads-SAP/Shared%20Documents/Forms/AllItems.aspx?id=%2Fteams%2FAzureStrategicWorkloads%2DSAP%2FShared%20Documents%2FGeneral%2FCxOutreach" target="_blank" rel="noopener">Focus Master ↗</a> ·
      <span class="src-tag" title="KPISupportData">K</span> KPISupportData (Kusto <code>asw_fy26_all_cases.json</code> · CPE Survey <code>cpe_fy26_final.json</code>) ·
      <span class="src-tag" title="Insights+_v3">I+</span> Insights+_v3 (leadership dashboard) ·
      <span class="src-tag" title="xlsx">X</span>
      <a href="https://microsoft.sharepoint.com/:x:/t/AzureStrategicWorkloads-SAP/cQq8BQ68wj2SRIsPSYUuhuM6EgUCeu633SA-bLTnZRE0eKi3wg" target="_blank" rel="noopener">FY26 ASW Cx Changing Activities ↗</a> ·
      <span class="src-tag" title="CX Observe">CX</span>
      <a href="https://cxp.azure.com/cxobserve/home" target="_blank" rel="noopener">CX Observe ↗</a> ·
      <span class="src-tag" title="pending source">?</span> pending source</em>
    </span>
  </div>
  {program_rollup_html}

  {focus_themes_html}

  <div class="legend">
    <h3>Legend &amp; Data Sources</h3>
    <div class="row">
      <div class="item"><span class="phase phase-1">Stage 1</span> Cx Assignment — TPID, Buddy/Mentor, CX Observe</div>
      <div class="item"><span class="phase phase-2">Stage 2</span> Stakeholder Engagement — Intro deck, Subs/Tags, Case creation (SAP on Azure)</div>
      <div class="item"><span class="phase phase-3">Stage 3</span> Toward Proactive — PoR + Wiki, Architecture &amp; Layout, Grafana, ZebraAI insight</div>
      <div class="item"><span class="phase phase-4">Stage 4</span> Workload Experience — CSS/CSU integration, Cx-facing meetings, Brownbag, Self-Help AI diagnostics</div>
    </div>
    <div class="row" style="margin-top:8px">
      <div class="item"><span class="metric-good">Green</span> = meets target</div>
      <div class="item"><span class="metric-warn">Amber</span> = warning</div>
      <div class="item"><span class="metric-bad">Red</span> = misses target</div>
      <div class="item">Targets: DTC ≤ 12d · %&lt;7 ≥ 50% · IR% ≥ 99% · Exec Esc = 0</div>
    </div>
    <div class="na-note">
      <strong>NA fields — pending data-source integration:</strong>
      <ul>
        <li><strong>IR Met %</strong> — will pull from CSS A&amp;I / DTP Power BI per TPID (see <code>review-reporter</code> skill). Kusto <code>IsIrMet</code> column is empty for FY26+ records.</li>
        <li><strong>Collaborate Case Creation</strong> — needs collaborate-created flag in the case schema.</li>
        <li><strong>ACR YoY %</strong> — FY27 ACR baseline &amp; growth source pending user guidance.</li>
        <li><strong>Customers marked TPID —</strong> (Univ. Kentucky, UTMB, Brown, Cone Health, CHOP, General Motors, CVS) have no TPID in the master list yet or no FY26 ASW cases. Shown as 0 volume.</li>
        <li><strong>CSAT</strong> is sourced from <code>Output/cpe_fy26_final.json</code> (170 FY26 ASW survey responses); customers with 0 responses show &quot;no surveys&quot;.</li>
      </ul>
    </div>
    <div class="drill-note">
      <strong>🔍 Verify the numbers.</strong> Any KPI value shown with a dashed blue underline is clickable — click it to open a modal with the underlying raw case list (IncidentId, engineer, queue, DTC, CritSit, product path, region) or CSAT survey rows. You can search, sort, and export to CSV. Source: <code>Output/asw_fy26_all_cases.json</code> (Kusto snapshot) &amp; <code>Output/cpe_fy26_final.json</code> (CSAT survey verbatims).
    </div>
  </div>

  {sections_html}

  <div class="callout info">
    <strong>Reading the dashboard.</strong> Section 1 above shows the 11 program-wide summary cards (Focus Customers, Mission Critical count, Total Case Vol, Closed, CSAT, IR%, DTC, %&lt;7d, Collaborate, Change Events, FY26 Jun ACR).
    The <strong>four cohort tabs</strong> below hold the detailed views for
    <em>SAP RISE + SAP Native MC</em>, <em>EPIC — Mission Critical</em>, <em>SAP Native/Epic Potential MC</em>, and <em>SAP RISE Selected</em> —
    each tab opens with a mini-rollup strip, per-customer summary cards (colour-coded by Engagement Phase: green = P4, blue = P3, amber = P2, red = P1), and a full detail table with Panel A (Support Delivery) &amp; Panel B (Program Indicators).
    Your last-picked tab is remembered between reloads.
  </div>

  <div class="callout">
    <strong>Next actions to complete V2 data coverage.</strong>
    <ul style="margin-top:8px; padding-left:20px;">
      <li>Wire <strong>CSAT / DSAT / IR%</strong> via <code>review-reporter</code> with per-TPID break-out; write monthly to <code>Output/caas_lead_csat_YYYYMM.json</code>.</li>
      <li>Provide <strong>ACR</strong> source (Power BI or Dynamics) &mdash; user follow-up pending.</li>
      <li>Compute <strong>CPE</strong> &mdash; need per-queue engineer roster + monthly capacity (extend <code>asw_musketeers_mission</code>).</li>
      <li>Compute <strong>Case Leakage %</strong> for Wave 1/2 subscription-based routing customers (needs AzureCore case dataset alongside ASW).</li>
      <li>Add <strong>TPIDs for onboarding customers</strong> (UTMB, Brown, Cone, CHOP, Univ. Kentucky, GM, CVS) as they enter routing.</li>
    </ul>
  </div>

</div>

<div class="footer">
  ASW CaaS Lead 2.0 · FY26 Monthly Business Insight · Dashboard V2 · Generated by
  <code>Skills/asw_caas_lead/scripts/generate_dashboard_v1.py</code>
</div>

<!-- Drill-down modal -->
<div id="drillOverlay" class="drill-overlay" role="dialog" aria-modal="true">
  <div class="drill-modal">
    <div class="dm-head">
      <div>
        <h2 id="dmTitle">Raw Data</h2>
        <div class="dm-sub" id="dmSub"></div>
      </div>
      <button class="dm-close" id="dmClose" aria-label="Close">✕</button>
    </div>
    <div class="dm-toolbar" id="dmToolbar">
      <input type="text" id="dmSearch" placeholder="Filter (any field)…" autocomplete="off">
      <span class="dm-count" id="dmCount"></span>
      <span style="flex:1"></span>
      <button class="dm-btn" id="dmExport">⬇ Export CSV</button>
    </div>
    <div class="dm-body" id="dmBody"></div>
  </div>
</div>

<!-- Wiki summary modal (v2.11) -->
<div id="wikiOverlay" class="wiki-overlay" role="dialog" aria-modal="true">
  <div class="wiki-modal">
    <div class="wm-head">
      <div>
        <h2 id="wmTitle">Customer</h2>
        <div class="wm-sub" id="wmSub"></div>
      </div>
      <button class="wm-close" id="wmClose" aria-label="Close">✕</button>
    </div>
    <div class="wm-body" id="wmBody"></div>
    <div class="wm-meta" id="wmMeta"></div>
  </div>
</div>

<!-- CaaS Lead review modal (v2.14) -->
<div id="reviewOverlay" class="wiki-overlay" role="dialog" aria-modal="true">
  <div class="wiki-modal review-modal" style="max-width:820px">
    <div class="wm-head">
      <div>
        <h2 id="rvTitle">Customer</h2>
        <div class="wm-sub" id="rvSub"></div>
      </div>
      <button class="wm-close" id="rvClose" aria-label="Close">✕</button>
    </div>
    <div class="wm-body" id="rvBody"></div>
    <div class="wm-meta" id="rvMeta"></div>
  </div>
</div>

<!-- Data source modal (v2.14.3) -->
<div id="datasourceOverlay" class="wiki-overlay" role="dialog" aria-modal="true">
  <div class="wiki-modal datasource-modal">
    <div class="wm-head">
      <div>
        <h2>Dashboard Data Sources</h2>
        <div class="wm-sub">How this dashboard is assembled &mdash; refreshed monthly by the CaaS Lead pipeline</div>
      </div>
      <button class="wm-close" id="dsClose" aria-label="Close">✕</button>
    </div>
    <div class="wm-body">
      <div class="ds-intro">This dashboard aggregates <b>5 upstream systems</b> into <b>8 JSON staging files</b> that live in the repository, then <b>generate_dashboard_v1.py</b> renders everything into a single self-contained HTML file. Every number on the dashboard is traceable back to one of the sources below.</div>

      <div class="ds-diagram">
        <div class="ds-tier tier-src">
          <div class="ds-tier-label"><span class="ds-step">1</span> Upstream systems</div>
          <div class="ds-tier-boxes">
            <div class="ds-src k"><span class="ds-name">Kusto</span><span class="ds-note">KPISupportData<br>(cases &amp; CSAT)</span></div>
            <div class="ds-src p"><span class="ds-name">Power BI</span><span class="ds-note">Insights+_v3<br>Fabric</span></div>
            <div class="ds-src c"><span class="ds-name">CX Observe</span><span class="ds-note">Consumption<br>tile (ACU)</span></div>
            <div class="ds-src w"><span class="ds-name">Azure DevOps</span><span class="ds-note">SfMC Know-Me<br>wiki pages</span></div>
            <div class="ds-src s"><span class="ds-name">SharePoint</span><span class="ds-note">ASW Team Portal\\CxOutreach</span></div>
          </div>
        </div>
        <div class="ds-arrow">&#9660;</div>
        <div class="ds-tier tier-stg">
          <div class="ds-tier-label"><span class="ds-step">2</span> JSON staging (checked into repo, refreshed monthly)</div>
          <div class="ds-tier-boxes">
            <div class="ds-file">asw_fy26_all_cases.json</div>
            <div class="ds-file">cpe_fy26_final.json</div>
            <div class="ds-file">asw_baseline_insights_v3.json</div>
            <div class="ds-file">fy26_acr_snapshot.json</div>
            <div class="ds-file">customer_wiki_summaries.json</div>
            <div class="ds-file">caas_lead_reviews_jun2026.json</div>
            <div class="ds-file">fy26_change_events.json</div>
            <div class="ds-file">asw_roster_fy26.json</div>
          </div>
        </div>
        <div class="ds-arrow">&#9660;</div>
        <div class="ds-render"><span class="ds-step">3</span> Renderer &nbsp;&middot;&nbsp; <code>generate_dashboard_v1.py</code> &nbsp;&rarr;&nbsp; <code>caas_lead_monthly_FY26.html</code></div>
      </div>

      <table class="ds-table">
        <colgroup>
          <col class="c-num"><col class="c-sys"><col class="c-src"><col class="c-ext"><col class="c-stg"><col class="c-feed">
        </colgroup>
        <thead>
          <tr><th>#</th><th>System</th><th>Source</th><th>Extraction</th><th>Staging file</th><th>Where you see it on this dashboard</th></tr>
        </thead>
        <tbody>
          <tr>
            <td><span class="ds-tag k">1</span></td>
            <td>Kusto</td>
            <td><code>supportrptwus3prod.westus3.kusto.windows.net</code> / <code>KPISupportData</code>.<br><code>AllCloudsSupportIncidentWithReferenceModelVNext</code></td>
            <td>Monthly KQL run over FY26 ASW-owned cases</td>
            <td><code>Output/asw_fy26_all_cases.json</code></td>
            <td>Program-wide Case Vol / Closed / DTC / %&lt;7d / CritSit% rollup, per-customer case metrics, all drill-down modal rows</td>
          </tr>
          <tr>
            <td><span class="ds-tag k">2</span></td>
            <td>Kusto</td>
            <td>Same table &mdash; filtered on <code>TotalCustomerSATScore</code> present</td>
            <td>Monthly KQL run over the FY26 CPE survey subset</td>
            <td><code>Output/cpe_fy26_final.json</code></td>
            <td>CSAT badges on every card, CSAT drill modal with survey verbatims</td>
          </tr>
          <tr>
            <td><span class="ds-tag p">3</span></td>
            <td>Power BI</td>
            <td><b>A&amp;I and DTP &vert; Insights+_v3_AIDTP_Fabric</b> (msit)</td>
            <td>Manual monthly capture (Playwright + external Edge) of the top KPI scorecard and the &ldquo;Key Metrics by Date&rdquo; Total column</td>
            <td><code>references/asw_baseline_insights_v3.json</code></td>
            <td>Top-of-dashboard &ldquo;ASW FY26 Baseline &amp; CaaS Lead Coverage&rdquo; strip (7 KPIs). Blue <span class="ds-tag p">I+</span> pill next to a KPI means the value came from Insights+_v3</td>
          </tr>
          <tr>
            <td><span class="ds-tag c">4</span></td>
            <td>CX Observe</td>
            <td><code>cxp.azure.com/cxobserve</code> &mdash; per-TPID Summary page, Consumption tile (ACU)</td>
            <td>Manual monthly capture per focus TPID (Playwright + external Edge)</td>
            <td><code>references/fy26_acr_snapshot.json</code></td>
            <td>&ldquo;FY26 Jun Sum&rdquo; cards (Program Rollup + each cohort mini-grid), per-customer ACR metric with MoM arrow, ACR drill modal (Raw Current / Raw Previous)</td>
          </tr>
          <tr>
            <td><span class="ds-tag w">5</span></td>
            <td>Azure DevOps Wiki</td>
            <td><code>supportability.visualstudio.com/AzureStrategicWorkloads/_wiki</code> &mdash; SfMC-Customers pages (SAP + Epic parents)</td>
            <td><code>fetch_customer_wikis.py</code> (Playwright + external Edge, incremental &amp; resumable)</td>
            <td><code>references/customer_wiki_summaries.json</code></td>
            <td>&ldquo;Wiki &#10003; N notes / &mdash; no notes&rdquo; tag on each customer card &rarr; opens Know-Me highlights modal</td>
          </tr>
          <tr>
            <td><span class="ds-tag s">6</span></td>
            <td>SharePoint</td>
            <td><code>AzureStrategicWorkloads-SAP</code> &rarr; <b>FY26June - CaaS Lead Sync</b> folder (14 <code>.pptx</code> per month)</td>
            <td>Playwright REST download &rarr; markitdown / PowerPoint COM extract &rarr; <code>_parse_caas_reviews.py</code> (raw) &rarr; <code>_curate_caas_reviews.py</code> (curated, max 3 bullets / section)</td>
            <td><code>references/caas_lead_reviews_jun2026.json</code></td>
            <td>Clickable customer name &rarr; monthly review modal (Key Updates / Service Delivery / ASW Team Reminder)</td>
          </tr>
          <tr>
            <td><span class="ds-tag s">7</span></td>
            <td>SharePoint (xlsx)</td>
            <td><b>FY26_ASW_Cx_Changing_Activities.xlsx</b></td>
            <td>Manual monthly refresh</td>
            <td><code>references/fy26_change_events.json</code></td>
            <td>SS / CE / EE badges + counts (Success Story, Change Event, Executive Escalation) on customer cards</td>
          </tr>
          <tr>
            <td><span class="ds-tag m">8</span></td>
            <td>Roster</td>
            <td>Curated from <code>bedrock.CSI.ASWStakeholder</code></td>
            <td>Hand-maintained JSON, seldom changes</td>
            <td><code>references/asw_roster_fy26.json</code></td>
            <td>CaaS Lead name shown on each customer card</td>
          </tr>
        </tbody>
      </table>
    </div>
    <div class="wm-meta" style="justify-content:space-between;">
      <span>Refresh cadence: <b>monthly</b> &middot; pipeline steps documented in <code>Skills/asw_caas_lead/SKILL.md</code></span>
      <span>Press <code>Esc</code> or <code>Alt+D</code> to toggle &middot; click outside to close</span>
    </div>
  </div>
</div>

<script id="drillData" type="application/json">{drill_json}</script>
<script id="wikiData" type="application/json">{wiki_json}</script>
<script id="reviewData" type="application/json">{review_json}</script>
<script>
(function(){{
  const DATA = JSON.parse(document.getElementById('drillData').textContent);
  const overlay = document.getElementById('drillOverlay');
  const dmTitle = document.getElementById('dmTitle');
  const dmSub   = document.getElementById('dmSub');
  const dmBody  = document.getElementById('dmBody');
  const dmSearch= document.getElementById('dmSearch');
  const dmCount = document.getElementById('dmCount');
  const dmExport= document.getElementById('dmExport');
  const dmClose = document.getElementById('dmClose');
  let state = {{ rows: [], cols: [], sortIdx: null, sortDir: 1, filter: '', kind: 'cases', keyLabel: '' }};

  function esc(s){{ return String(s==null?'':s).replace(/[&<>"']/g, c => ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c])); }}

  function open(){{ overlay.classList.add('open'); document.body.style.overflow='hidden'; }}
  function close(){{ overlay.classList.remove('open'); document.body.style.overflow=''; }}

  const KPI_MAP = {{
    vol:    {{ kind:'cases', label:'Case Volume',       filter:r=>true }},
    closed: {{ kind:'cases', label:'Closed Cases',      filter:r=>!!r.closed }},
    critsit:{{ kind:'cases', label:'CritSit Cases',     filter:r=>r.crit===1 }},
    dtc:    {{ kind:'cases', label:'Avg DTC (closed)',  filter:r=>r.dtc!=null, sort:'dtc-desc' }},
    pct7:   {{ kind:'cases', label:'%<7d (closed)',     filter:r=>r.dtc!=null, sort:'dtc-asc' }},
    csat:   {{ kind:'csat',  label:'CSAT Survey Rows',  filter:r=>true }},
    acr:    {{ kind:'acr',   label:'ACR Snapshot',      filter:r=>true }},
  }};

  const CASE_COLS = [
    {{k:'id',      h:'IncidentId', mono:true}},
    {{k:'cust',    h:'Customer'}},
    {{k:'tpid',    h:'TPID',       mono:true}},
    {{k:'sev',     h:'Sev',        align:'center'}},
    {{k:'crit',    h:'CritSit',    render:v=>v?'<span class="badge-crit">Yes</span>':''}},
    {{k:'created', h:'Created',    mono:true}},
    {{k:'closed',  h:'Closed',     mono:true, render:v=>v?('<span class="badge-cls">'+esc(v)+'</span>'):'<span class="badge-open">open</span>'}},
    {{k:'dtc',     h:'DTC (d)',    num:true, render:v=>v==null?'—':v.toFixed(2)}},
    {{k:'queue',   h:'Queue'}},
    {{k:'l2',      h:'Product (L2)'}},
    {{k:'l3',      h:'Scenario (L3)'}},
    {{k:'eng',     h:'Engineer',   mono:true}},
    {{k:'region',  h:'Region'}},
    {{k:'svc',     h:'ServiceName'}},
  ];

  const CSAT_COLS = [
    {{k:'id',      h:'IncidentId',      mono:true}},
    {{k:'cust',    h:'Customer'}},
    {{k:'tpid',    h:'TPID',            mono:true}},
    {{k:'score',   h:'Score', num:true, render:v => {{
        if(v==null) return '—';
        const c = v>=5?'csat-5':(v>=4?'csat-4':'csat-lo');
        return '<span class="'+c+'">'+v+'</span>';
      }}}},
    {{k:'closed',  h:'Closed',          mono:true}},
    {{k:'engname', h:'Engineer'}},
    {{k:'eng',     h:'Alias',           mono:true}},
    {{k:'svc',     h:'ServiceName'}},
    {{k:'region',  h:'Region'}},
    {{k:'verbatim',h:'Verbatim'}},
  ];

  function renderTable(){{
    const rows = state.rows;
    const cols = state.cols;
    const q = state.filter.toLowerCase();
    const filtered = q ? rows.filter(r => cols.some(c => String(r[c.k]||'').toLowerCase().includes(q))) : rows.slice();
    if(state.sortIdx != null){{
      const c = cols[state.sortIdx], dir = state.sortDir;
      filtered.sort((a,b) => {{
        let x=a[c.k], y=b[c.k];
        if(x==null) x=''; if(y==null) y='';
        if(typeof x==='number' && typeof y==='number') return (x-y)*dir;
        return String(x).localeCompare(String(y))*dir;
      }});
    }}
    dmCount.textContent = filtered.length + ' of ' + rows.length + ' rows';
    if(!filtered.length){{ dmBody.innerHTML = '<div class="dm-empty">No rows to show.</div>'; return; }}
    let html = '<table class="dm-tbl"><thead><tr>';
    cols.forEach((c,i)=>{{
      let cls = '';
      if(state.sortIdx===i) cls = (state.sortDir>0?'sort-asc':'sort-desc');
      html += '<th data-i="'+i+'" class="'+cls+'">'+esc(c.h)+'</th>';
    }});
    html += '</tr></thead><tbody>';
    filtered.forEach(r => {{
      html += '<tr>';
      cols.forEach(c => {{
        const v = r[c.k];
        const rendered = c.render ? c.render(v) : esc(v);
        let cls = '';
        if(c.mono) cls += 'mono ';
        if(c.num)  cls += 'num ';
        if(c.align==='center') cls += 'num ';
        html += '<td class="'+cls.trim()+'">'+rendered+'</td>';
      }});
      html += '</tr>';
    }});
    html += '</tbody></table>';
    dmBody.innerHTML = html;
    dmBody.querySelectorAll('th').forEach(th => {{
      th.addEventListener('click', () => {{
        const i = +th.dataset.i;
        if(state.sortIdx === i) state.sortDir = -state.sortDir;
        else {{ state.sortIdx = i; state.sortDir = 1; }}
        renderTable();
      }});
    }});
  }}

  function renderAcr(entry){{
    const a = entry.acr;
    if(!a){{ dmBody.innerHTML = '<div class="dm-empty">No ACR data.</div>'; dmCount.textContent=''; return; }}
    // TTM mode: prev_month/delta_pct are null and we surface only current TTM Consumption
    const isTtm = (a.prev_month == null && a.delta_pct == null);
    const rows = [];
    if(isTtm){{
      rows.push(['Azure Consumption (TTM)',                a.acu_display || '—']);
      rows.push(['Raw TTM Consumption (ACU)',              a.acu_this_month!=null ? a.acu_this_month.toLocaleString() : '—']);
      rows.push(['Metric',                                  'Trailing Twelve Months · rolling 12-month sum']);
    }} else {{
      const pct = (a.delta_pct!=null) ? (a.delta_pct>=0?'+':'') + a.delta_pct.toFixed(2)+'%' : '—';
      const curLbl  = a.cur_month_label  || 'This month';
      const prevLbl = a.prev_month_label || 'Previous month';
      rows.push(['Current ('+curLbl+')',              a.acu_display || '—']);
      rows.push(['Previous ('+prevLbl+')',            a.prev_display || '—']);
      rows.push(['MoM % Change',                       pct]);
      rows.push(['Raw current (ACU) · '+curLbl,       a.acu_this_month!=null ? a.acu_this_month.toLocaleString() : '—']);
      rows.push(['Raw previous (ACU) · '+prevLbl,     a.prev_month!=null ? a.prev_month.toLocaleString() : '—']);
    }}
    if(a.covered!=null) rows.push(['Coverage', a.covered+'/'+a.total+' customers']);
    if(a.per_tpid){{
      const list = Object.entries(a.per_tpid).map(([tp,val]) => tp+': '+ (val?val.toLocaleString():'—')).join(' · ');
      if(list) rows.push(['Per-TPID breakdown', list]);
    }}
    let html = '<div class="dm-acr"><div class="acr-grid">';
    rows.forEach(([k,v]) => {{
      html += '<div class="acr-cell"><div class="k">'+esc(k)+'</div><div class="v">'+esc(v)+'</div></div>';
    }});
    const footer = isTtm
      ? 'Source: Kusto customerdomrptwus3prod / customerdomdata / <code>WorkloadSearchSummarized</code> · Consumption (TTM, ACU). Snapshot file: <code>Skills/asw_caas_lead/references/fy26_acr_snapshot.json</code>. <b>TTM = Trailing Twelve Months</b>.'
      : 'Source: CX Observe · Summary page Consumption tile (org-level, ACU). Snapshot file: <code>Skills/asw_caas_lead/references/fy26_acr_snapshot.json</code>.';
    html += '</div><div style="margin-top:14px;font-size:.75rem;color:#64748b">'+footer+'</div></div>';
    dmBody.innerHTML = html;
    dmCount.textContent = '';
  }}

  function openDrill(key, kpi){{
    const entry = DATA[key];
    if(!entry){{ alert('No drill data for key: '+key); return; }}
    const cfg = KPI_MAP[kpi];
    if(!cfg){{ alert('Unknown KPI: '+kpi); return; }}
    state.kind = cfg.kind;
    state.keyLabel = entry.label;
    dmTitle.textContent = entry.label + ' — ' + cfg.label;
    dmSub.textContent = (entry.tpid?('TPID: '+entry.tpid+' · '):'') + 'FY26 raw records from Kusto snapshot';
    dmSearch.value = '';
    state.filter = '';
    state.sortIdx = null;
    state.sortDir = 1;
    if(cfg.kind === 'acr'){{
      dmSearch.style.display='none'; dmExport.style.display='none';
      renderAcr(entry);
    }} else {{
      dmSearch.style.display=''; dmExport.style.display='';
      const src = cfg.kind === 'csat' ? entry.csat : entry.cases;
      state.rows = (src||[]).filter(cfg.filter);
      state.cols = cfg.kind === 'csat' ? CSAT_COLS : CASE_COLS;
      if(cfg.sort){{
        const [k,dir] = cfg.sort.split('-');
        const idx = state.cols.findIndex(c => c.k === k);
        if(idx >= 0){{ state.sortIdx = idx; state.sortDir = dir==='asc'?1:-1; }}
      }}
      renderTable();
    }}
    open();
  }}

  function toCSV(){{
    if(state.kind === 'acr') return;
    const cols = state.cols;
    const q = state.filter.toLowerCase();
    const rows = q ? state.rows.filter(r => cols.some(c => String(r[c.k]||'').toLowerCase().includes(q))) : state.rows;
    const esc = v => {{
      if(v==null) return '';
      const s = String(v).replace(/"/g,'""');
      return /[",\\n]/.test(s) ? '"'+s+'"' : s;
    }};
    const lines = [cols.map(c=>c.h).join(',')];
    rows.forEach(r => lines.push(cols.map(c=>esc(r[c.k])).join(',')));
    const blob = new Blob(["\\ufeff"+lines.join('\\r\\n')], {{type:'text/csv;charset=utf-8'}});
    const a = document.createElement('a');
    const nm = state.keyLabel.replace(/[^a-z0-9]+/gi,'_') + '_' + state.kind + '.csv';
    a.href = URL.createObjectURL(blob); a.download = nm; a.click();
    setTimeout(()=>URL.revokeObjectURL(a.href), 5000);
  }}

  // event wiring
  document.addEventListener('click', e => {{
    const t = e.target.closest('.drill-kpi');
    if(!t) return;
    e.preventDefault();
    openDrill(t.dataset.drillKey, t.dataset.drillKpi);
  }});
  dmClose.addEventListener('click', close);
  overlay.addEventListener('click', e => {{ if(e.target === overlay) close(); }});
  document.addEventListener('keydown', e => {{ if(e.key === 'Escape' && overlay.classList.contains('open')) close(); }});
  dmSearch.addEventListener('input', () => {{ state.filter = dmSearch.value; renderTable(); }});
  dmExport.addEventListener('click', toCSV);
}})();

// Wiki summary modal (v2.11)
(function(){{
  const dataEl = document.getElementById('wikiData');
  if(!dataEl) return;
  const WIKI = JSON.parse(dataEl.textContent);
  const byKey = (WIKI && WIKI.by_key) || {{}};
  const overlay = document.getElementById('wikiOverlay');
  const wmTitle = document.getElementById('wmTitle');
  const wmSub   = document.getElementById('wmSub');
  const wmBody  = document.getElementById('wmBody');
  const wmMeta  = document.getElementById('wmMeta');
  const wmClose = document.getElementById('wmClose');
  if(!overlay || !wmTitle) return;
  function esc(s){{
    return String(s==null?'':s).replace(/[&<>"']/g, c => ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c]));
  }}
  function open(){{ overlay.classList.add('open'); document.body.style.overflow='hidden'; }}
  function close(){{ overlay.classList.remove('open'); document.body.style.overflow=''; }}
  function openWiki(key){{
    const e = byKey[key];
    if(!e){{
      wmTitle.textContent = 'Unknown customer';
      wmSub.textContent = 'No wiki index entry for key: '+key;
      wmBody.innerHTML = '<div class="wm-empty">Customer not present in <code>customer_wiki_summaries.json</code>.</div>';
      wmMeta.innerHTML = '';
      open();
      return;
    }}
    const wl = (e.workload||'').toUpperCase();
    wmTitle.innerHTML = esc(e.customer) + '<span class="wm-workload '+esc(wl)+'">'+esc(wl)+'</span>';
    wmSub.textContent = 'Know-Me Wiki · Support Profile Highlights';
    const hl = e.highlights || [];
    if(hl.length > 0){{
      wmBody.innerHTML = '<ul>' + hl.map(h => '<li>'+esc(h)+'</li>').join('') + '</ul>';
    }} else if(e.has_content === false){{
      const note = e.notes || 'No Know-Me wiki content available for this customer.';
      wmBody.innerHTML = '<div class="wm-empty">'+esc(note)+'</div>';
    }} else {{
      wmBody.innerHTML = '<div class="wm-empty">Wiki content has not been fetched yet.<br><br>Run <code>Skills/asw_caas_lead/scripts/fetch_customer_wikis.py</code> after signing into Azure DevOps in Edge (CDP 9222) to populate this modal.</div>';
    }}
    const url = e.wiki_url_guess || e.wiki_parent_url || '#';
    const fmtDate = iso => {{
      if(!iso) return 'unknown';
      const s = String(iso).split('T')[0];
      const m = s.match(/^(\\d{{4}})-(\\d{{2}})-(\\d{{2}})$/);
      if(!m) return iso;
      const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
      const mi = parseInt(m[2], 10) - 1;
      if(mi < 0 || mi > 11) return iso;
      return months[mi] + ' ' + String(parseInt(m[3], 10)) + ', ' + m[1];
    }};
    const last = e.last_updated ? ('Last updated: ' + esc(fmtDate(e.last_updated))) : 'Last updated: unknown';
    const fetched = e.fetched_at ? ('Fetched: ' + esc(e.fetched_at)) : 'Never fetched';
    wmMeta.innerHTML =
      '<span>' + last + ' · ' + fetched + '</span>' +
      '<span><a href="'+esc(url)+'" target="_blank" rel="noopener">Open wiki page ↗</a></span>';
    open();
  }}
  document.addEventListener('click', e => {{
    const t = e.target.closest('.wiki-tag');
    if(!t) return;
    e.preventDefault();
    e.stopPropagation();
    openWiki(t.dataset.wikiKey);
  }});
  wmClose.addEventListener('click', close);
  overlay.addEventListener('click', e => {{ if(e.target === overlay) close(); }});
  document.addEventListener('keydown', e => {{ if(e.key === 'Escape' && overlay.classList.contains('open')) close(); }});
}})();

// CaaS Lead review modal (v2.14) — click customer name -> latest monthly review
(function(){{
  const dataEl = document.getElementById('reviewData');
  if(!dataEl) return;
  const REVIEW = JSON.parse(dataEl.textContent);
  const byKey  = (REVIEW && REVIEW.by_key) || {{}};
  const meta   = (REVIEW && REVIEW.meta)   || {{}};
  const overlay = document.getElementById('reviewOverlay');
  const rvTitle = document.getElementById('rvTitle');
  const rvSub   = document.getElementById('rvSub');
  const rvBody  = document.getElementById('rvBody');
  const rvMeta  = document.getElementById('rvMeta');
  const rvClose = document.getElementById('rvClose');
  if(!overlay || !rvTitle) return;
  function esc(s){{
    return String(s==null?'':s).replace(/[&<>"']/g, c => ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c]));
  }}
  function open(){{ overlay.classList.add('open'); document.body.style.overflow='hidden'; }}
  function close(){{ overlay.classList.remove('open'); document.body.style.overflow=''; }}
  function section(cls, title, items){{
    if(!items || items.length === 0){{
      return '<div class="rv-section '+cls+'"><h3>'+esc(title)+' <span class="rv-count">no items</span></h3><div class="rv-empty-line">— not captured in this month\\'s update.</div></div>';
    }}
    const lis = items.map(it => '<li>'+esc(it)+'</li>').join('');
    return '<div class="rv-section '+cls+'"><h3>'+esc(title)+' <span class="rv-count">'+items.length+' item'+(items.length===1?'':'s')+'</span></h3><ul>'+lis+'</ul></div>';
  }}
  function openReview(key){{
    const e = byKey[key];
    if(!e){{
      rvTitle.textContent = 'No review available';
      rvSub.textContent = 'No CaaS Lead review file was found for key: '+key;
      rvBody.innerHTML = '<div class="wm-empty">The monthly CaaS Lead sync deck for this customer was not uploaded / parsed for '+esc(meta.month_label||'this month')+'.</div>';
      rvMeta.innerHTML = '';
      open();
      return;
    }}
    rvTitle.textContent = e.customer;
    rvSub.textContent = 'CaaS Lead monthly review · ' + (meta.month_label || meta.month || 'latest');
    rvBody.innerHTML =
      section('key', 'Key Updates',      e.key_updates) +
      section('svc', 'Service Delivery', e.service_delivery) +
      section('rem', 'ASW Team Reminder', e.reminders);
    const src = e.pptx_name ? ('Source: ' + esc(e.pptx_name)) : '';
    const folder = meta.sharepoint_folder;
    rvMeta.innerHTML =
      '<span>' + src + '</span>' +
      (folder ? '<span><a href="'+esc(folder)+'" target="_blank" rel="noopener">Open folder ↗</a></span>' : '');
    open();
  }}
  document.addEventListener('click', e => {{
    const t = e.target.closest('.review-link');
    if(!t) return;
    e.preventDefault();
    e.stopPropagation();
    openReview(t.dataset.reviewKey);
  }});
  rvClose.addEventListener('click', close);
  overlay.addEventListener('click', e => {{ if(e.target === overlay) close(); }});
  document.addEventListener('keydown', e => {{ if(e.key === 'Escape' && overlay.classList.contains('open')) close(); }});
}})();

// Cohort tab switcher (v2.6.0)
(function(){{
  const bar = document.querySelector('.cohort-tabs .tab-bar');
  if(!bar) return;
  const container = document.querySelector('.cohort-tabs');
  bar.addEventListener('click', e => {{
    const btn = e.target.closest('.tab-btn');
    if(!btn) return;
    const target = btn.dataset.tab;
    container.querySelectorAll('.tab-btn').forEach(b => b.classList.toggle('active', b === btn));
    container.querySelectorAll('.tab-pane').forEach(p => p.classList.toggle('active', p.id === target));
    // Remember choice for reload
    try {{ sessionStorage.setItem('caas-active-tab', target); }} catch(_){{ /* ignore */ }}
  }});
  // Restore last-picked tab on page load
  try {{
    const saved = sessionStorage.getItem('caas-active-tab');
    if(saved) {{
      const btn = bar.querySelector('.tab-btn[data-tab="'+saved+'"]');
      if(btn) btn.click();
    }}
  }} catch(_) {{ /* ignore */ }}
}})();

// Light/Dark theme toggle (v2.7.0)
(function(){{
  const btn = document.getElementById('themeToggle');
  const icon = document.getElementById('ttIcon');
  const label = document.getElementById('ttLabel');
  if(!btn) return;
  const KEY = 'caas-theme';
  function apply(theme) {{
    document.documentElement.setAttribute('data-theme', theme);
    if(theme === 'dark') {{
      icon.textContent = '☀️';
      label.textContent = 'Light';
    }} else {{
      icon.textContent = '🌙';
      label.textContent = 'Dark';
    }}
  }}
  // Initial theme: saved > system preference > light
  let initial = 'light';
  try {{
    const saved = localStorage.getItem(KEY);
    if(saved === 'dark' || saved === 'light') {{
      initial = saved;
    }} else if(window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {{
      initial = 'dark';
    }}
  }} catch(_) {{ /* ignore */ }}
  apply(initial);
  btn.addEventListener('click', () => {{
    const cur = document.documentElement.getAttribute('data-theme') || 'light';
    const next = cur === 'dark' ? 'light' : 'dark';
    apply(next);
    try {{ localStorage.setItem(KEY, next); }} catch(_) {{ /* ignore */ }}
  }});
  // Alt+T keyboard shortcut
  document.addEventListener('keydown', e => {{
    if(e.altKey && (e.key === 't' || e.key === 'T')) {{
      e.preventDefault();
      btn.click();
    }}
  }});
}})();

// Data source modal (v2.14.3)
(function(){{
  const overlay = document.getElementById('datasourceOverlay');
  const btn     = document.getElementById('dsToggle');
  const closer  = document.getElementById('dsClose');
  if(!overlay || !btn) return;
  function open() {{ overlay.classList.add('open'); document.body.style.overflow = 'hidden'; }}
  function close() {{ overlay.classList.remove('open'); document.body.style.overflow = ''; }}
  btn.addEventListener('click', open);
  if(closer) closer.addEventListener('click', close);
  overlay.addEventListener('click', e => {{ if(e.target === overlay) close(); }});
  document.addEventListener('keydown', e => {{
    if(e.key === 'Escape' && overlay.classList.contains('open')) close();
    if(e.altKey && (e.key === 'd' || e.key === 'D')) {{ e.preventDefault(); open(); }}
  }});
}})();
</script>

</body></html>"""


def _apply_fy_substitutions(html: str) -> str:
    """Post-render text substitution to swap FY26-specific labels for the active FY tag.
    All f-string HTML templates in this file are written with literal 'FY26' / 'Jun 2026'
    references, which are correct for FY26 but stale for FY27+. Rather than converting
    each of ~80 literals to `{FY_LABEL}` interpolation (risky brace escaping in f-strings),
    we apply a deterministic post-render substitution scoped to the active FY tag.
    Safe because these labels are user-visible display strings only.
    """
    if FY_TAG == "fy26":
        return html  # no-op for the source-of-truth FY

    # Filename substitutions (these appear in Data Source modal + Section footers)
    file_map = {
        "asw_fy26_all_cases.json":        _META["cases_json"],
        "cpe_fy26_final.json":            _META["csat_json"],
        "fy26_change_events.json":        _META["change_events"],
        "fy26_acr_snapshot.json":         _META["acr_snapshot"],
        "asw_baseline_insights_v3.json":  _META["insights_v3"],
        "caas_lead_reviews_jun2026.json": _META["review_summaries"],
        "caas_lead_monthly_FY26.html":    _META["out_html"],
    }
    for old, new in file_map.items():
        html = html.replace(old, new)

    # Label substitutions (user-visible strings)
    label_map = [
        # Order matters — longer / more specific first
        ("FY26 Jun Sum",            f"{FY_LABEL} Latest Month Sum"),
        ("FY26June - CaaS Lead Sync", f"{FY_LABEL} Latest - CaaS Lead Sync"),
        ("FY26 Jun ACR",            f"{FY_LABEL} Latest Month ACR"),
        ("FY26 ASW Cx Changing Activities",
                                    f"{FY_LABEL} ASW Cx Changing Activities"),
        ("FY26 CaaS Lead Coverage", f"{FY_LABEL} CaaS Lead Coverage"),
        ("FY26 CaaS Lead 2.0",      f"{FY_LABEL} CaaS Lead 2.0"),
        ("FY26 CaaS Lead",          f"{FY_LABEL} CaaS Lead"),
        ("FY26 Baseline",           f"{FY_LABEL} Baseline"),
        ("FY26 Total Case",         f"{FY_LABEL} Total Case"),
        ("FY26 Change Event",       f"{FY_LABEL} Change Event"),
        ("FY26 Collaborate",        f"{FY_LABEL} Collaborate"),
        ("FY26 IR Met",             f"{FY_LABEL} IR Met"),
        ("FY26 cumulative",         f"{FY_LABEL} cumulative"),
        ("FY26 raw records",        f"{FY_LABEL} raw records"),
        ("FY26 CPE survey verbatims", f"{FY_LABEL} CPE survey verbatims"),
        ("170 FY26 ASW survey",     "FY26 ASW survey (170 rows carried over — refresh at end-of-Jul 2026)"),
        ("FY26+",                   f"{FY_LABEL}+"),
        ("FY26 ASW cases",          f"{FY_LABEL} ASW cases"),
        ("FY26 CaaS Lead 2.0 Total Case Avg DTC", f"{FY_LABEL} CaaS Lead 2.0 Total Case Avg DTC"),
        ("in FY26",                 f"in {FY_LABEL}"),
        ("FY26 case data yet",      f"{FY_LABEL} case data yet"),
        # Meta phrasing
        ("Monthly KQL run over FY26 ASW-owned cases",
                                    f"KQL run over {FY_LABEL} YTD ASW-owned cases"),
        ("Monthly KQL run over the FY26 CPE survey subset",
                                    f"KQL run over {FY_LABEL} CPE survey subset"),
        # Header title / footer
        ("FY26 Monthly Business Insight", f"{FY_LABEL} Monthly Business Insight"),
        # Aggregate footer text
        ("Aggregate FY26 support delivery", f"Aggregate {FY_LABEL} support delivery"),
        # Panel A header inside customer tables
        ("Panel A · Support Delivery (FY26)", f"Panel A · Support Delivery ({FY_LABEL})"),
        # Remaining bare "FY26" — do LAST so specific matches above take precedence
        ("FY26", FY_LABEL),
    ]
    for old, new in label_map:
        html = html.replace(old, new)

    return html


def _render_fy_banner() -> str:
    """FY-scope status banner shown just below the header.
    Lists available months and highlights that this dashboard is FY YTD.
    Placeholder for a full interactive multi-month filter (planned v3.1).
    """
    if FY_TAG != "fy27":
        return ""  # only render for FY27 for now
    return """
<div style="max-width:1360px; margin:12px auto 0; padding:12px 20px; background:linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
            border-left:4px solid #1d4ed8; border-radius:8px; font-size:.85rem; color:#1e3a8a;
            box-shadow:0 1px 3px rgba(30,58,138,.08);">
  <div style="display:flex; align-items:center; gap:10px; flex-wrap:wrap;">
    <span style="font-weight:700; font-size:.95rem;">📅 Data Range</span>
    <span style="background:#1d4ed8; color:#fff; padding:3px 10px; border-radius:12px; font-size:.75rem; font-weight:600; letter-spacing:.02em;">FY27 YTD</span>
    <span style="background:#dbeafe; color:#1e40af; padding:3px 10px; border-radius:12px; font-size:.75rem; font-weight:600;">Jul 2026 · 20 days</span>
    <span style="color:#3730a3; font-size:.8rem;">Fiscal Year 2027 = 2026-07-01 → 2027-06-30 UTC.</span>
  </div>
  <div style="margin-top:8px; font-size:.75rem; color:#4338ca; line-height:1.5;">
    ℹ️ <strong>Multi-month filter (planned v3.1)</strong> — will let stakeholders pick single month / multiple months / FY YTD as more months accumulate.
    Today's view is FY27 YTD (all cases created after 2026-07-01).
    <strong>Data provenance for FY27:</strong> Kusto <code style="background:#fff;padding:1px 5px;border-radius:3px;">KPISupportData</code> is refreshed;
    Insights+_v3 baseline is Kusto-derived (PBI dashboard refreshes at month-end);
    CX Observe / ADO Wiki / SharePoint Change Events carry FY26 Jun snapshots
    <em>(labelled "Carried over" in Data Source modal)</em> pending end-of-Jul 2026 refresh.
  </div>
</div>
"""


def main():
    cases = json.loads(DATA_JSON.read_text(encoding="utf-8"))
    html = render(cases)
    # Post-process: substitute FY26 → active FY labels + filenames
    html = _apply_fy_substitutions(html)
    # Insert FY-scope banner immediately after the header div closes.
    # (The HTML uses `<div class="header">...</div>` followed by `<div class="container">`)
    banner = _render_fy_banner()
    if banner:
        html = html.replace('<div class="container">', banner + '\n<div class="container">', 1)
    OUT_HTML.write_text(html, encoding="utf-8")
    print(f"Wrote: {OUT_HTML}  ({len(html):,} bytes) · FY_TAG={FY_TAG}")


if __name__ == "__main__":
    main()
