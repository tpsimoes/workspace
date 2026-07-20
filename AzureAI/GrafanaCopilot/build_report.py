#!/usr/bin/env python3
"""Build a self-contained HTML RCA report embedding the captured Grafana panels."""
import base64
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).parent
CAP = BASE / "captures"
OUT = BASE / "vm-analyzer-report.html"

VM = "prdsapeccis03"
ARM_ID = ("/subscriptions/be9d60fb-f36a-4b27-bf41-aa14215b2724/resourceGroups/"
          "m1-rg-alz-esserp-saperpus-p-1/providers/Microsoft.Compute/virtualMachines/prdsapeccis03")
WINDOW = "Last 2 days \u2014 2026-06-30 ~14:36 \u2192 2026-07-02 ~14:36 UTC"

# Ordered panels to embed: (file, caption, finding-badge)
PANELS = [
    ("x-node-and-tor-placement.png", "Node and TOR Placement (&lt;60 Days)", "data"),
    ("x-scheduled-events-reboots.png", "Scheduled Events &amp; Reboots (timeline)", "info"),
    ("x-rca-helper-node-events-and-errors.png", "RCA Helper: Node Events and Errors", "empty"),
    ("x-node-storage-error-events.png", "Node Storage Error Events", "empty"),
    ("x-reboot-detail.png", "Reboot Detail", "empty"),
    ("x-scheduled-events-detail.png", "Scheduled Events Detail", "empty"),
    ("x-live-migration-events.png", "Live Migration Events", "empty"),
    ("x-vm-health-annotations.png", "VM Health Annotations", "empty"),
]

BADGE = {
    "data": ("Data present", "#1f6feb"),
    "info": ("Informational \u2014 no impact", "#9e6a03"),
    "empty": ("No data / no events", "#238636"),
}


def img_tag(fname):
    fp = CAP / fname
    if not fp.exists():
        return f'<div class="missing">Image not found: {fname}</div>'
    b64 = base64.b64encode(fp.read_bytes()).decode()
    return f'<img alt="{fname}" src="data:image/png;base64,{b64}"/>'


def panel_block(fname, caption, badge_key):
    label, color = BADGE[badge_key]
    return f"""
    <figure class="panel">
      <figcaption>
        <span class="cap">{caption}</span>
        <span class="badge" style="background:{color}">{label}</span>
      </figcaption>
      {img_tag(fname)}
    </figure>"""


FINDINGS_ROWS = [
    ("RCA Helper: Node Events and Errors", "Empty", "No platform-detected node events or errors"),
    ("Node Storage Error Events", "Empty", "No underlying storage/disk faults at the host"),
    ("Reboot Detail", "No data", "No host- or platform-initiated reboots"),
    ("Scheduled Events Detail", "Empty", "No executed scheduled (maintenance) events"),
    ("Live Migration Events", "Empty", "No live migrations"),
    ("VM Health Annotations", "Empty", "No platform health-impact annotations"),
    ("Scheduled Events &amp; Reboots (timeline)",
     "1 marker ~2026-07-01 14:00\u201315:00 UTC",
     "Scheduled-event notification only \u2014 no reboot, migration, or downtime resulted"),
]

PLACEMENT_ROWS = [
    ("Instance", "prdsapeccis03"),
    ("Data Center / Cluster", "MNZ22AzSet1 / MNZ22PrdApp42"),
    ("Node ID", "a1bfea08-1f04-2b4b-09c2-57b8ad818841"),
    ("Node IP", "100.118.3.18"),
    ("Container (VM) start time", "2026-04-03T14:48:59Z"),
    ("Last telemetry heartbeat", "2026-07-02T13:26:37Z"),
]


def rows(data):
    return "\n".join(f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in data)


def findings_rows(data):
    return "\n".join(
        f"<tr><td>{p}</td><td>{r}</td><td>{i}</td></tr>" for p, r, i in data)


HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>RCA Report \u2014 {VM}</title>
<style>
  :root {{ --bg:#0d1117; --panel:#161b22; --border:#30363d; --text:#e6edf3;
           --muted:#8b949e; --accent:#58a6ff; --green:#3fb950; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--text);
          font:15px/1.55 -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif; }}
  .wrap {{ max-width:1100px; margin:0 auto; padding:32px 24px 64px; }}
  header {{ border-bottom:1px solid var(--border); padding-bottom:20px; margin-bottom:28px; }}
  h1 {{ font-size:26px; margin:0 0 6px; }}
  h2 {{ font-size:19px; margin:34px 0 12px; border-left:3px solid var(--accent);
        padding-left:10px; }}
  .meta {{ color:var(--muted); font-size:13.5px; }}
  .meta code {{ color:var(--accent); word-break:break-all; }}
  .summary {{ background:var(--panel); border:1px solid var(--border);
              border-left:4px solid var(--green); border-radius:8px; padding:16px 18px; }}
  table {{ width:100%; border-collapse:collapse; margin:8px 0 4px; font-size:14px; }}
  th,td {{ text-align:left; padding:9px 12px; border-bottom:1px solid var(--border);
           vertical-align:top; }}
  th {{ color:var(--muted); font-weight:600; background:#11161d; }}
  td:first-child {{ color:var(--muted); white-space:nowrap; }}
  .grid {{ display:grid; grid-template-columns:1fr 1fr; gap:18px; margin-top:8px; }}
  @media (max-width:760px) {{ .grid {{ grid-template-columns:1fr; }} }}
  figure.panel {{ margin:0; background:var(--panel); border:1px solid var(--border);
                  border-radius:8px; overflow:hidden; }}
  figure.panel img {{ display:block; width:100%; height:auto; background:#0b0e14; }}
  figcaption {{ display:flex; justify-content:space-between; align-items:center;
               gap:10px; padding:9px 12px; border-bottom:1px solid var(--border);
               font-size:13.5px; }}
  figcaption .cap {{ font-weight:600; }}
  .badge {{ color:#fff; font-size:11px; padding:2px 8px; border-radius:20px;
            white-space:nowrap; }}
  .rc {{ background:var(--panel); border:1px solid var(--border); border-radius:8px;
         padding:16px 18px; }}
  ul {{ margin:8px 0; padding-left:22px; }}
  li {{ margin:6px 0; }}
  .missing {{ padding:24px; color:#f85149; }}
  footer {{ margin-top:40px; color:var(--muted); font-size:12.5px;
            border-top:1px solid var(--border); padding-top:14px; }}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>Root Cause Analysis \u2014 Virtual Machine <code>{VM}</code></h1>
    <div class="meta">
      <div>VM ARM ID: <code>{ARM_ID}</code></div>
      <div>Analysis window: {WINDOW}</div>
      <div>Data source: Azure platform telemetry \u2014 Virtual Machine Analyzer (Grafana)</div>
    </div>
  </header>

  <h2>Summary</h2>
  <div class="summary">
    Azure platform telemetry shows <strong>no node-level faults, host reboots, live
    migrations, or scheduled maintenance that caused downtime</strong> to this VM during
    the review window. The VM has run continuously on the same physical host since
    <strong>2026-04-03</strong> (~90 days uptime), which <strong>rules out the Azure
    infrastructure/host as the cause</strong> of any issue observed in this period.
  </div>

  <h2>Host / Node Placement</h2>
  <table>
    <thead><tr><th>Attribute</th><th>Value</th></tr></thead>
    <tbody>{rows(PLACEMENT_ROWS)}</tbody>
  </table>
  <p class="meta">A single, unchanged placement row confirms the VM was not moved to a
  different host or rack during the window.</p>

  <h2>Panel-by-panel findings (last 2 days)</h2>
  <table>
    <thead><tr><th>Panel</th><th>Result</th><th>Interpretation</th></tr></thead>
    <tbody>{findings_rows(FINDINGS_ROWS)}</tbody>
  </table>

  <h2>Grafana panels</h2>
  <div class="grid">
    {''.join(panel_block(*p) for p in PANELS)}
  </div>

  <h2>Root cause</h2>
  <div class="rc">
    No Azure platform-side root cause was identified. Infrastructure telemetry shows the
    host, storage, and platform maintenance subsystems were healthy and event-free for
    <code>{VM}</code> during the analysis window. The Azure platform is therefore
    <strong>excluded as a contributing factor</strong>.
  </div>

  <h2>Recommendation / Next steps</h2>
  <ul>
    <li>If an application or OS-level impact was experienced in this window, focus the
    investigation <strong>inside the guest</strong> (OS, SAP/application logs, in-guest
    patching or services) rather than the Azure host \u2014 no infrastructure disruption
    occurred.</li>
    <li>Treat the single scheduled-event notification (~2026-07-01) as
    <strong>informational, no impact</strong>; optionally correlate against in-guest logs
    at that timestamp to confirm no application-side reaction.</li>
    <li>To broaden the assessment, re-run over a 7-day window and include CPU/Memory and
    Disk panels for a fuller health picture.</li>
  </ul>

  <footer>
    Generated {datetime.now().strftime('%Y-%m-%d %H:%M')} \u00b7 Panels captured from Azure
    Managed Grafana (Virtual Machine Analyzer) via authenticated Microsoft Edge session.
  </footer>
</div>
</body>
</html>"""


def main():
    OUT.write_text(HTML, encoding="utf-8")
    print(f"Wrote {OUT} ({OUT.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
