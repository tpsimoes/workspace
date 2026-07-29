"""Populate customer_wiki_summaries.json with SAP customer Know-Me highlights extracted
from the AzureStrategicWorkloads wiki (SAP/SfMC-Customers tree).

Sources: raw wiki markdown saved under Skills/asw_caas_lead/references/_wiki_raw/ .
All highlights are grounded in the actual wiki text; no fabrication.

Categories:
  A. SUBSTANTIVE — has content, populate 3-5 English highlights + last_updated + notes.
  B. STUB       — Know-Me page exists but is "Under Construction"; has_content=false, note that stub exists.
  C. ABSENT     — No Know-Me page at all in the SAP SfMC-Customers CaaS Leads table.
"""
from __future__ import annotations
import json, pathlib
from datetime import datetime, timezone

REF_DIR = pathlib.Path(r'c:\GitHubCopilot\IronMan\Skills\asw_caas_lead\references')
JSON_PATH = REF_DIR / 'customer_wiki_summaries.json'

NOW = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')

WIKI_BASE = 'https://supportability.visualstudio.com/AzureStrategicWorkloads/_wiki/wikis/AzureStrategicWorkloads'

def url(page_id: int, slug: str) -> str:
    return f'{WIKI_BASE}/{page_id}/{slug}'

# =====================================================================
# A. SUBSTANTIVE  — 7 customers with real Know-Me content
# =====================================================================
SUBSTANTIVE = {
    '520706': {   # Bayer AG
        'wiki_url_guess': url(1825766, 'Bayer'),
        'has_content': True,
        'highlights': [
            "Bayer landscape consists of 254 SAP systems, split across Cropscience, Pharma, and Consumer Health / Cross-functional workloads. HANA-based SAP systems are hosted on Azure; Oracle-based SAP systems run in a Capgemini-managed private cloud.",
            "Customer sensitivity — Outdated Linux OS versions (SUSE and RHEL): in-place upgrade PoC is planned in a test environment, gated on the Capgemini contractual negotiation. Complications include RHEL 7 → 8 with Pacemaker and unclear SAP / 3rd-party software support for in-place upgrades.",
            "Customer sensitivity — Frequent VirtualMachinePossiblyDegradedDueToHardwareFailure health alerts on M and Mv2 series VMs; tracked via GetHelp #11350566.",
            "Extended-support conversations for the legacy SUSE / RHEL estate are active — Microsoft has already provided upgrade guidance and extended-support purchase paths across multiple customer sessions.",
            "Azure subscription footprint spans Germany (SAP-GDA and SAP-ERPCore, Prod + NonProd) and Canada DR1 / DR2 (Prod + Non-Prod) — dual-region DR posture."
        ],
        'last_updated': '2025-02-25',
        'notes': 'Author: Francisco Paulos. Tags: asw.Sfmc, asw.SAP, asw.Bayer, asw.Know-Me, asw.Reviewed-06-2024.'
    },
    '523272': {   # BHP
        'wiki_url_guess': url(1640779, 'BHP'),
        'has_content': True,
        'highlights': [
            "Mining super-major (iron ore, copper, coal, petroleum). ERP workloads split across two subscriptions — production (mPRD landscape) and non-production (mQAS, mDEV, iQAS, iDEV, Playpen, Reference); each subscription is spread across US-West-2 and US-East-1 regions.",
            "2025 project pipeline — Ransomware testing (Mar 2025), SAP SPS and Release upgrade (Sep 2025), Payroll Future (Sep–Oct 2025).",
            "Customer hot issue — Recurring pattern of VM restart / stopped unexpectedly and 'Cannot connect to VM' events.",
            "Customer hot issue — M832 VM Performance and Latency (ICM 481226321); ongoing engagement with Product Group.",
            "Latest Plan of Record: BHP PoR JUN 2025 (SharePoint). Support delivery is coordinated via the MWS500BHP SharePoint site and the BHPATUOnly team space."
        ],
        'last_updated': None,  # No explicit page-time captured; Reviewed-06-2024 tag only
        'notes': 'Tags: asw.Sfmc, asw.SAP, asw.CustomerName, asw.Know-Me, asw.Reviewed-06-2024. Last-modified date not captured in this fetch.'
    },
    '605015': {   # Lego
        'wiki_url_guess': url(2521742, 'Lego'),
        'has_content': True,
        'highlights': [
            "LEGO Group, S500 strategic. All infrastructure hosted in North Europe; DR is designed to go back on-premises. No Production workloads live yet — SAP lift-and-shift migration in progress.",
            "Milestones roadmap — QA System 1 single-VM (Mar) → QA System 2 single-VM (Jun) → QA System 3 HA multi-zone (Aug) → Pre-Prod HA (late Q3 / Q4) → Production build & migration after summer (around Aug 26).",
            "Critical VM dependency — 2× Standard_M416ds_8_v3 VMs in North Europe are the largest / most sensitive components; ASW to advise on storage (Azure NetApp Files vs Premium SSD) and Pacemaker-based HA design.",
            "Customer sensitivity — Networking security review post-lift-shift: all traffic currently routed back on-prem except App Gateway traffic; legacy rules need cleanup.",
            "Cross-cloud complexity — 4,000+ interfaces spanning on-prem, AWS, and Azure; customer is seeking a single-pane monitoring / log-aggregation solution across all three environments."
        ],
        'last_updated': None,
        'notes': 'Tags: asw.Sfmc, asw.SAP, asw.Lego, asw.Know-Me, asw.Reviewed-11-2024. Primary contributor: pedmarqu@microsoft.com.'
    },
    '682354': {   # Medline
        'wiki_url_guess': url(1936621, 'Medline'),
        'has_content': True,
        'highlights': [
            "Largest US medical-surgical distributor. Business hours 7:00 AM – 7:00 PM CST; downtime cost is approximately **$2M per hour** — highest per-hour impact in the SAP portfolio.",
            "**First MCSAW (Mission Critical Services for Azure Workload) customer running SAP on Azure** — evolution of SfMC aimed at elevating enterprise support experience and minimizing time-to-mitigation.",
            "Architecture — Primary and secondary sit in East US (single region), HA in place via Availability Zone 2; **no cross-region DR is currently in place**.",
            "SAP ECC (system ID MDP) is the heart of the estate. Grafana Customer Analyzer and DFM Cases dashboards are already stood up on the Medline Grafana tenant.",
            "Customer hot issue — Connectivity issue between App VM and Oracle DB@Azure (tracked in wiki page 1936619); active investigation."
        ],
        'last_updated': None,
        'notes': 'Tags: asw.Sfmc, asw.SAP, asw.CustomerName, asw.Know-Me. Microsoft-side contacts include CSAM Jim Boyd, CSA Anuradha Karnam, ASW CaaS Leads Naga Mutya & Frank Gong.'
    },
    '640443': {   # Nike
        'wiki_url_guess': url(1710356, 'Nike'),
        'has_content': True,
        'highlights': [
            "Nike — S500 strategic customer; global footwear / apparel. Operating segments span North America, EMEA, Greater China, Asia-Pacific, and Latin America.",
            "Three named architectures on file — NikeArchDiag (base), NikeArchDiagSAPsecHAdr (SAP secondary HA/DR), and NikeArchDiagOracleSAP (Oracle-fronted SAP topology).",
            "**Major project in flight — FHP system migration from 24 TB to 32 TB**, generating high case volume; original cut-over of 19 Oct was pushed to an undetermined new date.",
            "Reference documentation on file — Nike-SUSE Consulting Onsite Status Report (17 Sep 2024), Nike-Milestone1-Documentation, NIKE-Milestone2-Documentation.",
            "CSA Brownbag session library is flagged 'Under Construction' — knowledge-transfer material for this account is still being built."
        ],
        'last_updated': None,
        'notes': 'Tags: asw.Sfmc, asw.SAP, asw.CustomerName, asw.Know-Me, asw.Reviewed-06-2024. Primary contributor: alkassap@microsoft.com. ACE Program link still being investigated.'
    },
    '636846': {   # PepsiCo
        'wiki_url_guess': url(1256067, 'PepsiCo'),
        'has_content': True,
        'highlights': [
            "PepsiCo — S500 strategic. Microsoft strategic partnership signed December 2019. Part of the ACE Program with a published PepsiCo Know-Me One-Pager in the Azure ACE Wiki.",
            "Two named architectures — PGT–A1P Production environment (South Central US) and PGT–GCP e-HANA system. HANA storage layouts are documented separately for A1P and GCP.",
            "Customer hot issues — App-server-to-DB timeouts and SAP latency: once Azure Platform is ruled out, PepsiCo to open OSS ticket with SAP Partners.",
            "Customer hot issue — VM Hung / KDump: standard playbook links to RHEL and SLES kdump configuration KBs.",
            "Capacity constraints (specific to the PGT architecture) require immediate escalation to Joanne Marime and the Capacity Customer Experience Operations PD DL (`ccxopspd@microsoft.com`)."
        ],
        'last_updated': None,
        'notes': 'Tags: asw.Sfmc, asw.SAP, asw.PepsiCo, asw.Know-Me, asw.Reviewed-01-2024. Two SAP subscriptions on file: PEP-SAP-01-SUB and PEP-SAP-NONPROD-01-SUB (both mixed Prod/Non-Prod, Critical).'
    },
    '101552': {   # Unilever
        'wiki_url_guess': url(1565133, 'Unilever'),
        'has_content': True,
        'highlights': [
            "Unilever — S500 strategic. Multinational consumer goods company (nutrition, hygiene, personal care). Full CSAM / CSA / ACE / PG / CaaS-Lead focal-point matrix documented on the wiki.",
            "Part of the ACE Program with a published Unilever Know-Me One-Pager in the Azure ACE Wiki (page 187281).",
            "Customer hot issue — Platform reboots: majority of reboots are driven by the customer's **Parkmycloud orchestration**, which shuts down VMs every single day.",
            "Customer hot issue — Disk Detach issue tied to **Commvault backup** operations.",
            "Grafana observability stack — dedicated Unilever Customer Analyzer plus the shared CaaS Lead dashboard and Azure ACE 360 BI dashboard. Architecture pages (Production environment, Storage layout, Networking) are still flagged 'Working in progress'."
        ],
        'last_updated': None,
        'notes': 'Tags: asw.Sfmc, asw.SAP, asw.Unilever, asw.Know-Me, asw.Reviewed-10-2024. Named customer contacts: Yogesh Singh, Tinu Jain.'
    },
}

# =====================================================================
# B. STUB — 5 customers with Know-Me pages that are "Under Construction"
# =====================================================================
STUB = {
    '1248703': (2849082, 'Beiersdorf'),
    'noTPID-cvs': (2849079, 'CVS'),
    '523595': (2849083, 'Ferrero'),
    'noTPID-general-motors': (2849080, 'General-Motors'),
    '10545209': (2849084, 'Shell'),
}
STUB_NOTE = (
    "Know-Me page exists in SAP/SfMC-Customers wiki tree but is currently 'Under Construction' "
    "(no content published yet as of 2026-07-20). Tags: asw.asw, asw.Internal.Processes, asw.SMEs, "
    "asw.EPIC, asw.DLs, asw.Reviewed-07-2026."
)

# =====================================================================
# C. ABSENT — SAP customers with NO Know-Me page in the CaaS Leads table
# =====================================================================
ABSENT_KEYS = [
    '603819|15902931|2699441',  # SAP RISE (tenant)
    '643195',                   # Halliburton
    '645076',                   # McKesson
    '940486',                   # Petrobras
    '639155',                   # Walgreens
]
ABSENT_NOTE = "No Know-Me page in SAP/SfMC-Customers CaaS Leads Info table (as of 2026-07-20)."

# ---------------------------------------------------------------------
# Load, update, write back
# ---------------------------------------------------------------------
data = json.loads(JSON_PATH.read_text(encoding='utf-8'))
data['meta']['last_fetch_run'] = NOW
data['meta']['generated_at'] = NOW

by_key = data['by_key']

updated = {'substantive': 0, 'stub': 0, 'absent': 0, 'skipped_no_entry': []}

for k, v in SUBSTANTIVE.items():
    if k not in by_key:
        updated['skipped_no_entry'].append(k)
        continue
    e = by_key[k]
    e['wiki_url_guess'] = v['wiki_url_guess']
    e['has_content']    = v['has_content']
    e['highlights']     = v['highlights']
    e['last_updated']   = v['last_updated']
    e['fetched_at']     = NOW
    e['notes']          = v['notes']
    updated['substantive'] += 1

for k, (pid, slug) in STUB.items():
    if k not in by_key:
        updated['skipped_no_entry'].append(k)
        continue
    e = by_key[k]
    e['wiki_url_guess'] = url(pid, slug)
    e['has_content']    = False
    e['highlights']     = []
    e['last_updated']   = None
    e['fetched_at']     = NOW
    e['notes']          = STUB_NOTE
    updated['stub'] += 1

for k in ABSENT_KEYS:
    if k not in by_key:
        updated['skipped_no_entry'].append(k)
        continue
    e = by_key[k]
    e['wiki_url_guess'] = None
    e['has_content']    = False
    e['highlights']     = []
    e['last_updated']   = None
    e['fetched_at']     = NOW
    e['notes']          = ABSENT_NOTE
    updated['absent'] += 1

JSON_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')

print('Updated customer_wiki_summaries.json')
print(f"  Substantive (highlights):  {updated['substantive']}")
print(f"  Stub (Under Construction): {updated['stub']}")
print(f"  Absent (no wiki page):     {updated['absent']}")
if updated['skipped_no_entry']:
    print(f"  Skipped (no JSON entry):  {updated['skipped_no_entry']}")
