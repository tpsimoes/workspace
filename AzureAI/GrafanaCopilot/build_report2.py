#!/usr/bin/env python3
"""Build a curated HTML report of RELEVANT Grafana panels for prdsapeccap04."""
import base64
import html
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).parent
CAP = BASE / "captures" / "all"
OUT = BASE / "prdsapeccap04-relevant-panels-report.html"

VM = "prdsapeccap04"
ARM_ID = ("/subscriptions/be9d60fb-f36a-4b27-bf41-aa14215b2724/resourceGroups/"
          "m1-rg-alz-esserp-saperpus-p-1/providers/Microsoft.Compute/virtualMachines/prdsapeccap04")
WINDOW = "2026-06-26 00:00:00 \u2192 2026-06-28 23:59:59 UTC"

CAT = {
    "Info":   "#1f6feb",
    "Event":  "#a371f7",
    "Metric": "#db6d28",
}


def img(fname):
    fp = CAP / fname
    if not fp.exists():
        return f'<div class="missing">Image not found: {fname}</div>'
    b64 = base64.b64encode(fp.read_bytes()).decode()
    return f'<img alt="{html.escape(fname)}" src="data:image/png;base64,{b64}"/>'


def kv_table(pairs):
    if not pairs:
        return ""
    rows = "".join(f"<tr><td>{html.escape(k)}</td><td>{html.escape(v)}</td></tr>" for k, v in pairs)
    return f'<table class="kv">{rows}</table>'


# Curated, ordered relevant panels.
PANELS = [
    {
        "file": "panel-01-virtual-machine-current-info-ignores-selected-time.png",
        "title": "Virtual Machine \u2014 Current Info",
        "cat": "Info",
        "why": "Identity panel (IDs, names, region, customer). Always relevant \u2014 establishes the "
               "asset under analysis and the current node/container it runs on.",
        "kv": [
            ("Resource Name", "prdsapeccap04"),
            ("Customer", "Medline Industries, LP"),
            ("Region", "useast (East US)"),
            ("Subscription", "M1-ALZ-ESSERP-P-1"),
            ("VirtualMachine Id", "6e965a4d-9d96-49ea-bb97-d866f1247659"),
            ("Current Container Id", "3853186b-f480-4f60-966c-b0ecfaafa186"),
            ("Current Node Id", "72a7cab6-98b6-66a2-79a4-4107f4fae86d"),
        ],
    },
    {
        "file": "panel-07-os-image-details.png",
        "title": "OS Image Details",
        "cat": "Info",
        "why": "Feature/configuration panel. Always relevant \u2014 documents OS billing/license and "
               "that this is a non-SAP-image, BYOS Linux VM not classified as Azure-supported image.",
        "kv": [
            ("SAP Image", "No"),
            ("OS Billing Type", "Linux_IaaS"),
            ("OS License Type", "NONE"),
            ("OS Image License", "BYOS"),
            ("OS Azure Supported", "No"),
        ],
    },
    {
        "file": "panel-03-installed-extensions.png",
        "title": "Installed Extensions",
        "cat": "Info",
        "why": "Feature panel. Always relevant \u2014 shows monitoring, run-command and "
               "Site Recovery / snapshot (backup & DR) extensions are installed.",
        "kv": [
            ("Monitoring", "MonitorX64Linux"),
            ("Run Command", "RunCommandLinux"),
            ("DR", "SiteRecovery-Linux, SiteRecovery-LinuxSLES15"),
            ("Backup", "VMSnapshotLinux"),
        ],
    },
    {
        "file": "panel-04-vm-tags.png",
        "title": "VM Tags",
        "cat": "Info",
        "why": "Tags panel \u2014 always relevant by rule. No tags are set on this VM "
               "(<code>{}</code>), which is itself worth noting for governance/ownership tracking.",
        "kv": [("tags", "{} (none set)")],
    },
    {
        "file": "panel-19-vm-placement.png",
        "title": "VM Placement",
        "cat": "Event",
        "why": "KEY FINDING. This ID/placement table lists rows, so it is relevant \u2014 and the rows "
               "show the VM's container was <strong>re-created twice inside the window</strong> "
               "(host/node changes on 2026-06-26 07:39 and 2026-06-27 13:13). A container "
               "re-creation means the VM was moved/rebuilt on a new physical node.",
        "kv": [
            ("Node until 2026-06-26 07:39", "6d389155\u2026 (in place since 2025-02-16)"),
            ("New node @ 2026-06-26 07:39:33", "026a845f\u2026 (container dbfef662\u2026)"),
            ("New node @ 2026-06-27 13:13:36", "72a7cab6\u2026 (container 3853186b\u2026, current)"),
            ("Cluster (all rows)", "IAD01PrdApp45"),
        ],
    },
    {
        "file": "panel-13-outages-impacting-virtual-machines-in-this-vm-s-su.png",
        "title": "Outages impacting Virtual Machines (subscription/region)",
        "cat": "Event",
        "why": "KEY FINDING. Event panel with a listed row \u2192 relevant. A regional Azure platform "
               "incident overlaps the window: East US VM/VMSS management-operation errors, with a "
               "red 'RCA/PIR' stage. Customer impact 17:43\u201322:40 UTC on 2026-06-26.",
        "kv": [
            ("Tracking ID", "ZH_0-XKZ"),
            ("IcM", "824520159"),
            ("Started", "2026-06-26 17:29:44 UTC"),
            ("Mitigated", "2026-06-27 02:01:20 UTC"),
            ("Stage", "RCA / PIR"),
            ("Title", "PIR \u2013 Azure VM Scale Sets and VM Management Operation Errors in East US"),
            ("Stated impact window", "17:43\u201322:40 UTC, 26 Jun 2026"),
        ],
    },
    {
        "file": "panel-15-cpu-avg.png",
        "title": "CPU % (Avg / Max)",
        "cat": "Metric",
        "why": "Relevant metric \u2014 abnormal spikes. The MAX series (yellow) repeatedly saturates to "
               "~100% (red threshold), with heavy sustained bursts on the morning of 2026-06-26 and "
               "a sharp 100% spike on 2026-06-28. Average stays low, indicating short but severe "
               "per-core saturation events rather than steady load.",
        "kv": [],
    },
    {
        "file": "panel-16-memory-pressure-max.png",
        "title": "% Memory Pressure (Max)",
        "cat": "Metric",
        "why": "Relevant metric \u2014 constantly high value. Memory pressure sits at "
               "<strong>119\u2013121%</strong> (above 100%) for the entire period it reports "
               "(from ~2026-06-27 12:00, aligned with the second container re-creation), indicating "
               "the guest is under sustained memory pressure.",
        "kv": [],
    },
]

TIMELINE = [
    ("2026-06-26 07:39:33 UTC", "Placement", "Container re-created on new node 026a845f\u2026 "
     "(host/node change #1; previous node in place since 2025-02-16)."),
    ("2026-06-26 ~06:00\u201312:00 UTC", "CPU", "Sustained bursts of CPU MAX saturating to ~100%."),
    ("2026-06-26 17:29:44 UTC", "Outage", "Regional incident ZH_0-XKZ (IcM 824520159) started \u2014 "
     "East US VM/VMSS management-operation errors."),
    ("2026-06-26 17:43\u201322:40 UTC", "Outage", "Stated customer-impact window for the East US incident."),
    ("2026-06-27 02:01:20 UTC", "Outage", "Incident recorded as mitigated (RCA/PIR)."),
    ("2026-06-27 13:13:36 UTC", "Placement", "Container re-created on new node 72a7cab6\u2026 "
     "(host/node change #2, current placement). Memory/RAM metrics begin reporting around this time."),
    ("2026-06-27 12:00 \u2192 end", "Memory", "Memory pressure remains high at 119\u2013121%."),
    ("2026-06-28 (late)", "CPU", "Sharp CPU MAX spike to ~100%."),
]

TL_COLOR = {"Placement": "#a371f7", "Outage": "#f85149", "CPU": "#db6d28", "Memory": "#d29922"}

EXCLUDED = ("VM Events, Previous Support Requests, ICMs, TOR Events, RCA Helper: Node Events, "
            "Node Storage Error Events, Scheduled Events & Reboots, Reboot Detail, "
            "Scheduled Events Detail, Live Migration Events, VM Health Annotations, Attached Disk, "
            "Disk Detach Operations, Storage Errors & Events, VM Sku Capacity, Node & TOR Placement "
            "(<60d), Microsoft App Links (empty / no-data / navigation-only), and Disk Queue/Latency, "
            "VM & per-LUN IOPS/Bandwidth, Network in/out, Portal bytes in/out (no data reported).")


def panel_block(p):
    color = CAT[p["cat"]]
    return f"""
    <section class="panel">
      <div class="phead">
        <span class="ptitle">{html.escape(p['title'])}</span>
        <span class="badge" style="background:{color}">{p['cat']}</span>
      </div>
      <div class="pbody">
        <div class="shot">{img(p['file'])}</div>
        <div class="detail">
          <p class="why">{p['why']}</p>
          {kv_table(p['kv'])}
        </div>
      </div>
    </section>"""


def timeline_block():
    items = ""
    for when, cat, desc in TIMELINE:
        c = TL_COLOR.get(cat, "#8b949e")
        items += f"""
        <li>
          <span class="dot" style="background:{c}"></span>
          <span class="when">{html.escape(when)}</span>
          <span class="tag" style="border-color:{c};color:{c}">{cat}</span>
          <span class="desc">{html.escape(desc)}</span>
        </li>"""
    return f'<ul class="timeline">{items}</ul>'


HTML = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Relevant Panels Report \u2014 {VM}</title>
<style>
 :root{{--bg:#0d1117;--panel:#161b22;--border:#30363d;--text:#e6edf3;--muted:#8b949e;--accent:#58a6ff;}}
 *{{box-sizing:border-box;}}
 body{{margin:0;background:var(--bg);color:var(--text);font:15px/1.55 -apple-system,Segoe UI,Roboto,Arial,sans-serif;}}
 .wrap{{max-width:1120px;margin:0 auto;padding:32px 24px 64px;}}
 header{{border-bottom:1px solid var(--border);padding-bottom:20px;margin-bottom:26px;}}
 h1{{font-size:25px;margin:0 0 6px;}}
 h2{{font-size:19px;margin:36px 0 14px;border-left:3px solid var(--accent);padding-left:10px;}}
 .meta{{color:var(--muted);font-size:13.5px;}} .meta code{{color:var(--accent);word-break:break-all;}}
 .summary{{background:var(--panel);border:1px solid var(--border);border-left:4px solid #d29922;border-radius:8px;padding:16px 18px;}}
 .summary ul{{margin:10px 0 0;padding-left:20px;}} .summary li{{margin:6px 0;}}
 section.panel{{background:var(--panel);border:1px solid var(--border);border-radius:10px;margin:16px 0;overflow:hidden;}}
 .phead{{display:flex;justify-content:space-between;align-items:center;padding:11px 16px;border-bottom:1px solid var(--border);}}
 .ptitle{{font-weight:600;font-size:15.5px;}}
 .badge{{color:#fff;font-size:11px;padding:2px 10px;border-radius:20px;}}
 .pbody{{display:grid;grid-template-columns:minmax(320px,1.15fr) 1fr;gap:16px;padding:16px;}}
 @media (max-width:820px){{.pbody{{grid-template-columns:1fr;}}}}
 .shot img{{display:block;width:100%;height:auto;border:1px solid var(--border);border-radius:6px;background:#0b0e14;}}
 .why{{margin:0 0 12px;}} .why code{{color:var(--accent);}}
 table.kv{{width:100%;border-collapse:collapse;font-size:13.5px;}}
 table.kv td{{padding:6px 10px;border-bottom:1px solid var(--border);vertical-align:top;}}
 table.kv td:first-child{{color:var(--muted);white-space:nowrap;width:42%;}}
 ul.timeline{{list-style:none;margin:0;padding:0;}}
 ul.timeline li{{display:grid;grid-template-columns:190px 92px 1fr;gap:10px;align-items:start;padding:10px 8px;border-bottom:1px solid var(--border);position:relative;}}
 @media (max-width:720px){{ul.timeline li{{grid-template-columns:1fr;gap:3px;}}}}
 .timeline .when{{color:var(--text);font-variant-numeric:tabular-nums;font-size:13.5px;}}
 .timeline .tag{{border:1px solid;border-radius:20px;font-size:11px;padding:1px 8px;text-align:center;height:fit-content;}}
 .timeline .desc{{color:var(--muted);font-size:13.5px;}} .timeline .dot{{display:none;}}
 .excluded{{color:var(--muted);font-size:13px;background:var(--panel);border:1px solid var(--border);border-radius:8px;padding:12px 14px;}}
 footer{{margin-top:40px;color:var(--muted);font-size:12.5px;border-top:1px solid var(--border);padding-top:14px;}}
 .legend{{font-size:12.5px;color:var(--muted);margin:6px 0 0;}}
 .legend span{{display:inline-block;margin-right:14px;}} .legend i{{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:5px;vertical-align:middle;}}
</style></head><body><div class="wrap">
 <header>
   <h1>Relevant Panels Report \u2014 <code>{VM}</code></h1>
   <div class="meta">
     <div>VM ARM ID: <code>{ARM_ID}</code></div>
     <div>Analysis window: {WINDOW}</div>
     <div>Source: Azure Managed Grafana \u2014 Virtual Machine Analyzer (50 panels scanned, {len(PANELS)} relevant)</div>
   </div>
 </header>

 <h2>Global summary</h2>
 <div class="summary">
   Of 50 dashboard panels scanned for the window, <strong>{len(PANELS)} were relevant</strong>.
   The VM (<code>prdsapeccap04</code>, East US, customer Medline Industries) shows three notable
   things during 26\u201328 Jun 2026:
   <ul>
     <li><strong>Two host/node changes</strong> \u2014 the underlying container was re-created on
       2026-06-26 07:39 and again 2026-06-27 13:13 (VM Placement), meaning the VM was rebuilt on
       new physical nodes twice within the window.</li>
     <li><strong>A regional Azure platform incident</strong> (IcM 824520159, PIR) affecting East US
       VM/VMSS management operations, with stated impact 17:43\u201322:40 UTC on 2026-06-26 \u2014 overlapping
       this VM's subscription/region.</li>
     <li><strong>Resource strain</strong> \u2014 CPU MAX repeatedly saturates to ~100% (notably 06-26
       morning and a 06-28 spike) and memory pressure stays high at 119\u2013121% from 06-27 onward.</li>
   </ul>
   No reboots, live-migration, storage errors, disk-detach, or ICM/SR records were listed, and disk,
   network and IOPS/bandwidth metric panels reported no data.
 </div>

 <h2>Relevant panels</h2>
 <p class="legend">
   <span><i style="background:{CAT['Info']}"></i>Info \u2014 always relevant</span>
   <span><i style="background:{CAT['Event']}"></i>Event \u2014 relevant because rows are listed</span>
   <span><i style="background:{CAT['Metric']}"></i>Metric \u2014 relevant due to sustained-high / spikes</span>
 </p>
 {''.join(panel_block(p) for p in PANELS)}

 <h2>Timeline of relevant findings</h2>
 {timeline_block()}

 <h2>Panels reviewed but excluded (not relevant)</h2>
 <div class="excluded">{html.escape(EXCLUDED)}</div>

 <footer>
   Generated {datetime.now().strftime('%Y-%m-%d %H:%M')} \u00b7 Panels captured from Azure Managed
   Grafana (Virtual Machine Analyzer) via authenticated Microsoft Edge session. Relevance applied per
   rules: info panels always; event panels only when rows are listed; metric panels only when
   sustained-high or showing abnormal spikes/drops; tables flagged red / errors / failures.
 </footer>
</div></body></html>"""


def main():
    OUT.write_text(HTML, encoding="utf-8")
    print(f"Wrote {OUT} ({OUT.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
