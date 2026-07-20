#!/usr/bin/env python3
"""Revalidated curated HTML report of RELEVANT Grafana panels for prdsapeccap04 (all2 capture)."""
import base64
import html
import json
import re
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).parent
CAP = BASE / "captures" / "all2"
OUT = BASE / "prdsapeccap04-revalidated-report.html"

VM = "prdsapeccap04"
ARM_ID = ("/subscriptions/be9d60fb-f36a-4b27-bf41-aa14215b2724/resourceGroups/"
          "m1-rg-alz-esserp-saperpus-p-1/providers/Microsoft.Compute/virtualMachines/prdsapeccap04")
WINDOW = "2026-06-26 00:00:00 \u2192 2026-06-28 23:59:59 UTC"
DASH_URL = (
    "https://asw-main-c9d6bfgzgnbydnae.eus2.grafana.azure.com/d/"
    "c3624fcf-e0e9-4514-9f82-8961539cfa3f/virtual-machine-analyzer?orgId=1"
    "&var-_id=6e965a4d-9d96-49ea-bb97-d866f1247659"
    "&from=2026-06-26T00:00:00.000Z&to=2026-06-28T23:59:59.000Z&timezone=utc"
    "&var-_vmId=6e965a4d-9d96-49ea-bb97-d866f1247659"
    "&var-_armId=%2Fsubscriptions%2Fbe9d60fb-f36a-4b27-bf41-aa14215b2724"
    "%2Fresourcegroups%2Fm1-rg-alz-esserp-saperpus-p-1%2Fproviders"
    "%2Fmicrosoft.compute%2Fvirtualmachines%2Fprdsapeccap04"
    "&var-_regionShoebox=AzComputeShoeboxEUS&var-_resourceName=prdsapeccap04"
    "&var-_customerSubscription=be9d60fb-f36a-4b27-bf41-aa14215b2724"
    "&var-_containerId=3853186b-f480-4f60-966c-b0ecfaafa186"
    "&var-_resourceGroupName=M1-RG-ALZ-ESSERP-SAPERPUS-P-1&var-_vmssName="
)

CAT = {"Info": "#1f6feb", "Event": "#a371f7", "Metric": "#db6d28"}


def resolve_file(hardcoded_name):
    """Resolve a panel image by its title-slug, ignoring the capture index
    prefix (panel-NN-). This keeps the report working across dashboards where
    panel order/indices differ (e.g. virtual-machine-analyzer vs
    virtual-machine-reboot-analyzer). Returns the actual filename or None."""
    slug = re.sub(r"^panel-\d+-", "", hardcoded_name)
    for fp in sorted(CAP.glob("panel-*.png")):
        if re.sub(r"^panel-\d+-", "", fp.name) == slug:
            return fp.name
    return None


def img(fname):
    fp = CAP / fname
    if not fp.exists():
        return f'<div class="missing">Image not found: {fname}</div>'
    b64 = base64.b64encode(fp.read_bytes()).decode()
    return f'<img alt="{html.escape(fname)}" src="data:image/png;base64,{b64}"/>'


def kv_table(pairs):
    if not pairs:
        return ""
    rows = "".join(f"<tr><td>{html.escape(k)}</td><td>{v}</td></tr>" for k, v in pairs)
    return f'<table class="kv">{rows}</table>'


PANELS = [
    # ---- Identity / configuration (Info) ----
    {"file": "panel-01-virtual-machine-current-info-ignores-selected-time.png",
     "title": "Virtual Machine \u2014 Current Info", "cat": "Info",
     "why": "Identity panel (IDs, names, region, customer). Always relevant \u2014 defines the asset.",
     "kv": [("Resource / Region", "prdsapeccap04 / useast (East US)"),
            ("Customer", "Medline Industries, LP"),
            ("VirtualMachine Id", "6e965a4d-9d96-49ea-bb97-d866f1247659"),
            ("Current Container / Node", "3853186b\u2026 / 72a7cab6\u2026")]},
    {"file": "panel-02-vm-details-features.png",
     "title": "VM Details (Features)", "cat": "Info",
     "why": "Feature panel. Always relevant \u2014 and directly explains this investigation: the VM is "
            "<strong>LiveMigration&nbsp;Eligible = Yes</strong> and not pinned / not in an availability "
            "set, so the platform may live-migrate it for host maintenance/defrag.",
     "kv": [("SKU", "Standard_E16s_v5"), ("SAP Certified SKU", "Yes"), ("Runs SAP image", "No"),
            ("VM Pinned / In PPG / Avail Set", "No / No / No"),
            ("Accelerated Networking", "Yes"),
            ("<strong>LiveMigration Eligible</strong>", "<strong>Yes</strong>")]},
    {"file": "panel-07-os-image-details.png",
     "title": "OS Image Details", "cat": "Info",
     "why": "Config panel \u2014 non-SAP image, BYOS Linux, not classified Azure-supported image.",
     "kv": [("SAP Image", "No"), ("OS Billing Type", "Linux_IaaS"),
            ("OS License / Image License", "NONE / BYOS"), ("OS Azure Supported", "No")]},
    {"file": "panel-03-installed-extensions.png",
     "title": "Installed Extensions", "cat": "Info",
     "why": "Feature panel \u2014 monitoring, run-command, Site Recovery (DR) and VM snapshot (backup) present.",
     "kv": [("Monitoring", "MonitorX64Linux"), ("Run Command", "RunCommandLinux"),
            ("DR", "SiteRecovery-Linux / -LinuxSLES15"), ("Backup", "VMSnapshotLinux")]},
    {"file": "panel-04-vm-tags.png",
     "title": "VM Tags", "cat": "Info",
     "why": "Tags panel \u2014 always relevant by rule. No tags set (<code>{}</code>) \u2014 worth noting for governance.",
     "kv": [("tags", "{} (none set)")]},
    {"file": "panel-44-details.png",
     "title": "Network Details", "cat": "Info",
     "why": "Network identity panel. Shows the VNet the VM is attached to (other fields not populated).",
     "kv": [("Virtual Network", "M1-ALZ-VNET-ESSERP-P-1 (RG M1-RG-ALZ-ESSERP-P-1)")]},
    {"file": "panel-33-attached-disk.png",
     "title": "Attached Disk", "cat": "Info",
     "why": "Details panel with rows \u2014 lists all managed disks (2 data + 1 OS, all Premium_LRS 100 GB).",
     "kv": [("Data disk (Lun 0)", "prdsapeccap04-datadisk-00 \u2014 Premium_LRS 100 GB"),
            ("Data disk (Lun 1)", "prdsapeccap04-datadisk-00-73dc4667\u2026 \u2014 Premium_LRS 100 GB"),
            ("OS disk", "prdsapeccap04-osdisk \u2014 Premium_LRS 100 GB")]},
    {"file": "panel-20-vm-sku-capacity.png",
     "title": "VM Sku Capacity", "cat": "Info",
     "why": "Capacity/details panel with rows \u2014 Standard_E16s_v5 capacity available across East US AZ01/02/03.",
     "kv": [("SKU / Region", "Standard_E16s_v5 / eastus"),
            ("Physical Zones", "useast-AZ01, AZ02, AZ03 (Upgrade & NewDeployment)")]},

    # ---- Placement & node events (Event) ----
    {"file": "panel-19-vm-placement.png",
     "title": "VM Placement", "cat": "Event",
     "why": "KEY. Rows present \u2192 relevant. Container re-created <strong>twice in-window</strong> "
            "(2026-06-26 07:39 and 2026-06-27 13:13) \u2014 the VM moved to a new physical node each time.",
     "kv": [("Node until 06-26 07:39", "6d389155\u2026 (since 2026-04-03)"),
            ("\u2192 06-26 07:39:33", "026a845f\u2026 (container dbfef662\u2026)"),
            ("\u2192 06-27 13:13:36", "72a7cab6\u2026 (container 3853186b\u2026, current)"),
            ("Cluster (all)", "IAD01PrdApp45")]},
    {"file": "panel-22-node-and-tor-placement-60-days.png",
     "title": "Node and TOR Placement (<60 Days)", "cat": "Event",
     "why": "Placement/ID table with rows \u2014 confirms both moves also changed the <strong>Top-of-Rack "
            "switch / rack</strong> (IPs 10.122.222.152 \u2192 .223.6 \u2192 .223.136), i.e. physical rack changes.",
     "kv": [("06-27 (current) node/IP/TOR", "72a7cab6\u2026 / 10.122.223.136 / iad01-\u20260908-06sc7"),
            ("06-26 node/IP/TOR", "026a845f\u2026 / 10.122.223.6 / iad01-\u20260908-04t0 (Eth13/1)"),
            ("prior node/IP/TOR", "6d389155\u2026 / 10.122.222.152 / iad01-\u20260908-02sc23")]},
    {"file": "panel-05-vm-events.png",
     "title": "VM Events (counters)", "cat": "Event",
     "why": "Summary counters with non-zero values \u2192 relevant. Quantifies the window's activity.",
     "kv": [("Placements", "2"), ("Live Migration", "1"), ("Scheduled Events", "1"), ("VM CRUD", "0")]},
    {"file": "panel-24-rca-helper-node-events-and-errors-check-https-supp.png",
     "title": "RCA Helper: Node Events and Errors", "cat": "Event",
     "why": "KEY. Multiple rows \u2192 relevant. Host maintenance on both nodes: HostGateway, MetadataServer, "
            "HostGAPlugin and firmware (BscCertifier) version upgrades, plus a RestorePoint (backup) QoS event.",
     "kv": [("06-28 19:55 (026a845f)", "BscCertifier firmware \u2192 bsc_master_26_03_05002"),
            ("06-28 04:50 (026a845f)", "VMApiQosEvent \u2014 RestorePoints.RestorePointOperation.PUT"),
            ("06-27 17:59 (026a845f)", "HostGateway / MetadataServerPF / HostGAPlugin upgrades"),
            ("06-27 14:11 (72a7cab6)", "MetadataServerPF / HostGAPlugin / HostGateway upgrades")]},

    # ---- Live migration / scheduled events (Event) ----
    {"file": "panel-29-scheduled-events-detail.png",
     "title": "Scheduled Events Detail", "cat": "Event",
     "why": "KEY. Two rows \u2192 relevant. Two <strong>Infrastructure-initiated LiveMigration</strong> "
            "scheduled events, each freezing Disk/Network/Compute/OS during the move.",
     "kv": [("2026-06-27 13:14:39\u201313:24:23", "LiveMigration \u2014 Infrastructure \u2014 Freeze all (10 min)"),
            ("2026-06-26 07:40:36\u201307:49:42", "LiveMigration \u2014 Infrastructure \u2014 Freeze all (9 min)")]},
    {"file": "panel-30-live-migration-events.png",
     "title": "Live Migration Events", "cat": "Event",
     "why": "KEY \u2014 answers the review reason. Two rows, both <strong>Completed</strong>, "
            "TriggerType <strong>Defrag</strong> (platform defragmentation), no node fault / no guest crash.",
     "kv": [("2026-06-27 13:23:24", "Completed \u2014 Defrag \u2014 \u2192 node 72a7cab6 (container 3853186b)"),
            ("2026-06-26 07:48:59", "Completed \u2014 Defrag \u2014 NetworkReady")]},
    {"file": "panel-31-vm-health-annotations.png",
     "title": "VM Health Annotations", "cat": "Event",
     "why": "Two rows \u2192 relevant. Confirms both migrations <strong>succeeded</strong>, with very short "
            "VM blackout/pause (~0.95 s and ~0.80 s), Defrag-triggered.",
     "kv": [("27-06-2026 13:17", "LiveMigrationSucceeded \u2014 blackout ~0.951 s \u2014 Defrag"),
            ("26-06-2026 07:43", "LiveMigrationSucceeded \u2014 blackout ~0.802 s \u2014 Defrag")]},
    {"file": "panel-27-scheduled-events-reboots.png",
     "title": "Scheduled Events & Reboots (timeline)", "cat": "Event",
     "why": "Two event bars visible (06-26 ~07:40 and 06-27 ~13:14) \u2014 visual corroboration of the two "
            "live-migration scheduled events. No reboot markers.",
     "kv": []},

    # ---- Platform outage (Event) ----
    {"file": "panel-13-outages-impacting-virtual-machines-in-this-vm-s-su.png",
     "title": "Outages impacting Virtual Machines", "cat": "Event",
     "why": "KEY. Listed row \u2192 relevant. Regional East US VM/VMSS management-operation PIR overlapping "
            "the window (red RCA stage). Not a downtime event for this VM but relevant context.",
     "kv": [("Tracking ID / IcM", "ZH_0-XKZ / 824520159"),
            ("Started \u2192 Mitigated", "2026-06-26 17:29:44 \u2192 2026-06-27 02:01:20 UTC"),
            ("Stated impact window", "17:43\u201322:40 UTC, 26 Jun 2026"),
            ("Title", "PIR \u2013 Azure VMSS & VM Management Operation Errors in East US")]},
    {"file": "panel-35-storage-errors-events.png",
     "title": "Storage Errors & Events", "cat": "Event",
     "why": "Panel is flagged (red warning icon) and titled 'Errors' \u2192 relevant by rule. It lists the two "
            "data disks; no discrete error events with timestamps are shown, so treat as a watch item rather "
            "than a confirmed fault.",
     "kv": [("Listed", "prdsapeccap04-datadisk-00 (Lun 0), \u2026-73dc4667 (Lun 1)")]},

    # ---- Metrics (spikes / sustained-high) ----
    {"file": "panel-15-cpu-avg.png",
     "title": "CPU % (Avg / Max)", "cat": "Metric",
     "why": "Abnormal spikes. MAX repeatedly saturates ~100% (red line) \u2014 heavy on 06-26 morning and a "
            "sharp 06-28 spike; average stays low (short, severe per-core saturation).",
     "kv": []},
    {"file": "panel-16-memory-pressure-max.png",
     "title": "% Memory Pressure (Max)", "cat": "Metric",
     "why": "Constantly high \u2014 sits at 119\u2013121% for the whole period it reports (from ~06-27 12:00).",
     "kv": []},
    {"file": "panel-38-data-os-temp-disk-latency-in-milliseconds.png",
     "title": "Data/OS/Temp Disk Latency (ms)", "cat": "Metric",
     "why": "Sudden spikes \u2014 brief latency spikes to ~40\u201364 ms from a ~3 ms baseline, clustered on 06-26 "
            "morning / 06-27 (coinciding with the first migration and CPU bursts).",
     "kv": []},
    {"file": "panel-45-network-in-bytes-per-minute-max.png",
     "title": "Network in bytes / min (Max)", "cat": "Metric",
     "why": "Sudden spike \u2014 inbound peaks to ~5.5 GB/min around 06-27 ~06:00\u201309:00 above a <1 GB baseline.",
     "kv": []},
    {"file": "panel-46-network-out-bytes-per-minute-max.png",
     "title": "Network out bytes / min (Max)", "cat": "Metric",
     "why": "Sudden spikes \u2014 outbound bursts to ~55\u201358 GB/min on 06-26\u201306-27 (likely backup/replication).",
     "kv": []},
    {"file": "panel-47-total-portal-bytes-in-rate-per-minute-max-per-nic-.png",
     "title": "Total Portal Bytes In (per Nic/Container/Node)", "cat": "Metric",
     "why": "Relevant \u2014 the color segments visualize the node transitions (6d389155\u2192026a845f\u219272a7cab6), and "
            "there is a clear <strong>drop</strong> on 06-28 ~08:00\u201310:00.",
     "kv": []},
    {"file": "panel-48-total-portal-bytes-out-rate-per-minute-max-per-nic.png",
     "title": "Total Portal Bytes Out (per Nic/Container/Node)", "cat": "Metric",
     "why": "Relevant \u2014 same node-transition segmentation and a matching <strong>drop</strong> on 06-28 "
            "~08:00\u201310:00 in outbound rate.",
     "kv": []},
]

TIMELINE = [
    ("2026-06-26 07:40\u201307:49 UTC", "LiveMigration", "Scheduled Event: Infrastructure LiveMigration (Freeze). "
     "Live migration #1 Completed (Defrag) \u2014 VM moved 6d389155\u2192026a845f; blackout ~0.80 s."),
    ("2026-06-26 ~06:00\u201312:00 UTC", "Metric", "CPU MAX ~100% bursts; disk latency spikes to ~64 ms."),
    ("2026-06-26 17:29\u201322:40 UTC", "Outage", "Regional East US VM/VMSS management PIR (IcM 824520159); "
     "mitigated 06-27 02:01."),
    ("2026-06-27 13:13\u201313:24 UTC", "LiveMigration", "Scheduled Event: Infrastructure LiveMigration (Freeze). "
     "Live migration #2 Completed (Defrag) \u2014 VM moved 026a845f\u219272a7cab6; blackout ~0.95 s."),
    ("2026-06-27 ~06:00\u201312:00 UTC", "Metric", "Network In spike ~5.5 GB/min; Network Out bursts ~55 GB/min."),
    ("2026-06-27 14:11 UTC", "NodeEvent", "Host agent upgrades on new node 72a7cab6 "
     "(MetadataServerPF, HostGAPlugin, HostGateway)."),
    ("2026-06-27 17:59 UTC", "NodeEvent", "Host agent upgrades on node 026a845f "
     "(HostGateway, MetadataServerPF, HostGAPlugin)."),
    ("2026-06-27 12:00 \u2192 end", "Metric", "Memory pressure sustained high at 119\u2013121%."),
    ("2026-06-28 04:50 UTC", "NodeEvent", "RestorePoint (backup) QoS event on node 026a845f."),
    ("2026-06-28 ~08:00\u201310:00 UTC", "Metric", "Portal Bytes In/Out drop (throughput dip)."),
    ("2026-06-28 19:55 UTC", "NodeEvent", "BscCertifier firmware upgrade on node 026a845f."),
    ("2026-06-28 (late) UTC", "Metric", "Sharp CPU MAX spike to ~100%."),
]

TL_COLOR = {"LiveMigration": "#a371f7", "Outage": "#f85149", "Metric": "#db6d28", "NodeEvent": "#2f81f7"}

EXCLUDED = ("TOR Events (Health 0 / Events 0), Node Storage Error Events (No data), Reboot Detail (No data), "
            "Disk Detach Operations (No data), ICMs Associated (No data), Previous Support Requests (No data), "
            "Microsoft App Links (navigation only), Ram size/Available (stable ~free), VM Bandwidth % and VM "
            "IOPS % (flat at 0), Data/OS Disk Bandwidth % and IOPS % per Lun (\u22641\u20132%, negligible), and "
            "Disk Queue Length (<1). All either say 'No data', show zero/near-zero, or are navigation.")


def panel_block(p):
    color = CAT[p["cat"]]
    return f"""
    <section class="panel">
      <div class="phead"><span class="ptitle">{html.escape(p['title'])}</span>
        <span class="badge" style="background:{color}">{p['cat']}</span></div>
      <div class="pbody"><div class="shot">{img(p['_resolved'])}</div>
        <div class="detail"><p class="why">{p['why']}</p>{kv_table(p['kv'])}</div></div>
    </section>"""


def timeline_block():
    items = ""
    for when, cat, desc in TIMELINE:
        c = TL_COLOR.get(cat, "#8b949e")
        items += (f'<li><span class="when">{html.escape(when)}</span>'
                  f'<span class="tag" style="border-color:{c};color:{c}">{cat}</span>'
                  f'<span class="desc">{html.escape(desc)}</span></li>')
    return f'<ul class="timeline">{items}</ul>'


for _p in PANELS:
    _p["_resolved"] = resolve_file(_p["file"])
UNAVAILABLE = [p["title"] for p in PANELS if not p["_resolved"]]
PANELS = [p for p in PANELS if p["_resolved"]]

try:
    _manifest = json.loads((CAP / "manifest.json").read_text(encoding="utf-8"))
    SCANNED = len(_manifest)
except Exception:
    SCANNED = len(list(CAP.glob("panel-*.png")))

info_n = sum(1 for p in PANELS if p["cat"] == "Info")
event_n = sum(1 for p in PANELS if p["cat"] == "Event")
metric_n = sum(1 for p in PANELS if p["cat"] == "Metric")

HTML = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Revalidated Panels Report \u2014 {VM}</title>
<style>
 :root{{--bg:#0d1117;--panel:#161b22;--border:#30363d;--text:#e6edf3;--muted:#8b949e;--accent:#58a6ff;}}
 *{{box-sizing:border-box;}}
 body{{margin:0;background:var(--bg);color:var(--text);font:15px/1.55 -apple-system,Segoe UI,Roboto,Arial,sans-serif;}}
 .wrap{{max-width:1120px;margin:0 auto;padding:32px 24px 64px;}}
 header{{border-bottom:1px solid var(--border);padding-bottom:20px;margin-bottom:26px;}}
 h1{{font-size:25px;margin:0 0 6px;}}
 h2{{font-size:19px;margin:36px 0 14px;border-left:3px solid var(--accent);padding-left:10px;}}
 .meta{{color:var(--muted);font-size:13.5px;}} .meta code{{color:var(--accent);word-break:break-all;}}
 .summary{{background:var(--panel);border:1px solid var(--border);border-left:4px solid #a371f7;border-radius:8px;padding:16px 18px;}}
 .summary ul{{margin:10px 0 0;padding-left:20px;}} .summary li{{margin:6px 0;}}
 .note{{background:#1b2030;border:1px solid #30363d;border-left:4px solid #d29922;border-radius:8px;padding:12px 16px;margin:14px 0;font-size:13.5px;}}
 section.panel{{background:var(--panel);border:1px solid var(--border);border-radius:10px;margin:16px 0;overflow:hidden;}}
 .phead{{display:flex;justify-content:space-between;align-items:center;padding:11px 16px;border-bottom:1px solid var(--border);}}
 .ptitle{{font-weight:600;font-size:15.5px;}}
 .badge{{color:#fff;font-size:11px;padding:2px 10px;border-radius:20px;}}
 .pbody{{display:grid;grid-template-columns:minmax(320px,1.1fr) 1fr;gap:16px;padding:16px;}}
 @media (max-width:820px){{.pbody{{grid-template-columns:1fr;}}}}
 .shot img{{display:block;width:100%;height:auto;border:1px solid var(--border);border-radius:6px;background:#0b0e14;}}
 .why{{margin:0 0 12px;}} .why code{{color:var(--accent);}}
 table.kv{{width:100%;border-collapse:collapse;font-size:13px;}}
 table.kv td{{padding:6px 10px;border-bottom:1px solid var(--border);vertical-align:top;}}
 table.kv td:first-child{{color:var(--muted);white-space:nowrap;width:44%;}}
 ul.timeline{{list-style:none;margin:0;padding:0;}}
 ul.timeline li{{display:grid;grid-template-columns:210px 110px 1fr;gap:10px;align-items:start;padding:10px 8px;border-bottom:1px solid var(--border);}}
 @media (max-width:720px){{ul.timeline li{{grid-template-columns:1fr;gap:3px;}}}}
 .timeline .when{{font-variant-numeric:tabular-nums;font-size:13px;}}
 .timeline .tag{{border:1px solid;border-radius:20px;font-size:11px;padding:1px 8px;text-align:center;height:fit-content;}}
 .timeline .desc{{color:var(--muted);font-size:13.5px;}}
 .excluded{{color:var(--muted);font-size:13px;background:var(--panel);border:1px solid var(--border);border-radius:8px;padding:12px 14px;}}
 a.dashlink{{display:inline-block;background:#1f6feb;color:#fff;text-decoration:none;font-weight:600;padding:11px 18px;border-radius:8px;border:1px solid #388bfd;word-break:break-word;}}
 a.dashlink:hover{{background:#388bfd;}}
 .legend{{font-size:12.5px;color:var(--muted);margin:6px 0 0;}} .legend span{{display:inline-block;margin-right:14px;}}
 .legend i{{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:5px;vertical-align:middle;}}
 footer{{margin-top:40px;color:var(--muted);font-size:12.5px;border-top:1px solid var(--border);padding-top:14px;}}
</style></head><body><div class="wrap">
 <header>
   <h1>Revalidated Panels Report \u2014 <code>{VM}</code></h1>
   <div class="meta">
     <div>VM ARM ID: <code>{ARM_ID}</code></div>
     <div>Analysis window: {WINDOW}</div>
     <div>Source: Azure Managed Grafana \u2014 Virtual Machine Reboot Analyzer (fully-parameterized URL; {SCANNED} panels scanned, {len(PANELS)} relevant \u2014 {info_n} info, {event_n} event, {metric_n} metric)</div>
   </div>
 </header>

 <div class="note"><strong>Revalidation note:</strong> This run used the fully-parameterized dashboard URL
 (with <code>var-_vmId</code>, <code>var-_containerId</code>, <code>var-_regionShoebox</code>, etc.) and waited
 for every panel to finish loading. Panels that were empty in the earlier <code>var-_id</code>-only run \u2014
 Live Migration Events, Scheduled Events Detail, RCA Helper, VM Health Annotations, disk/network metrics \u2014
 now populate. The earlier "no live migrations" conclusion is <strong>corrected</strong>: there were
 <strong>two Infrastructure Defrag live migrations</strong> in-window.</div>

 <h2>Global summary</h2>
 <div class="summary">
   Of 50 dashboard panels scanned for 26\u201328 Jun 2026, <strong>{len(PANELS)} were relevant</strong>. Findings:
   <ul>
     <li><strong>Two platform live migrations</strong> (Infrastructure-initiated, TriggerType <em>Defrag</em>),
       both <strong>Completed / Succeeded</strong> with sub-second VM blackout (~0.80 s on 06-26 07:48 and
       ~0.95 s on 06-27 13:23). Each moved the VM to a new physical node and rack
       (6d389155 \u2192 026a845f \u2192 72a7cab6, cluster IAD01PrdApp45).</li>
     <li><strong>Host maintenance</strong> on both nodes (HostGateway, MetadataServer, HostGAPlugin agent
       upgrades and BscCertifier firmware), plus a backup RestorePoint operation on 06-28 \u2014 consistent with
       the defrag/maintenance driving the migrations.</li>
     <li><strong>Regional context:</strong> an East US VM/VMSS management-operation PIR (IcM 824520159)
       overlapped 06-26 evening; it affected control-plane operations, not this VM's uptime.</li>
     <li><strong>Resource behaviour:</strong> CPU MAX bursts to ~100%, memory pressure sustained at
       119\u2013121%, brief disk-latency spikes (~64 ms), large network spikes on 06-27, and a throughput drop
       on 06-28 ~08:00\u201310:00.</li>
   </ul>
   No reboots, no confirmed storage/disk errors (the Storage Errors panel lists disks but no timestamped fault),
   no disk-detach, and no ICM/SR records for this VM.
 </div>

 <h2>Relevant panels</h2>
 <p class="legend">
   <span><i style="background:{CAT['Info']}"></i>Info \u2014 always relevant</span>
   <span><i style="background:{CAT['Event']}"></i>Event \u2014 rows present</span>
   <span><i style="background:{CAT['Metric']}"></i>Metric \u2014 sustained-high / spikes / drops</span></p>
 {''.join(panel_block(p) for p in PANELS)}

 <h2>Timeline of relevant findings</h2>
 {timeline_block()}

 <h2>Panels reviewed but excluded (not relevant)</h2>
 <div class="excluded">{html.escape(EXCLUDED)}</div>

 <h2>Grafana dashboard</h2>
 <p>Open the live source dashboard (with this VM and time range pre-applied):</p>
 <p><a class="dashlink" href="{html.escape(DASH_URL)}" target="_blank" rel="noopener">
   \u2197 Open Virtual Machine Analyzer for {VM} in Azure Managed Grafana</a></p>

 <footer>Generated {datetime.now().strftime('%Y-%m-%d %H:%M')} \u00b7 Captured from Azure Managed Grafana
 (Virtual Machine Reboot Analyzer) via authenticated Microsoft Edge, waiting for all panels to load. Relevance rules:
 info always; events when rows present; metrics only when sustained-high or showing abnormal spikes/drops;
 tables flagged red / mentioning errors or failures.</footer>
</div></body></html>"""


def main():
    OUT.write_text(HTML, encoding="utf-8")
    print(f"Wrote {OUT} ({OUT.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
