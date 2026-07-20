"""Build the VM Reboot Analyzer RCA report for azlsapgvpdb02.

Reads captured panel PNGs from captures/<vm>/, resolves each by title-slug
(panel index is not stable across scrapes), tightens each image to just the
content band (top-left aligned, title kept, trailing blank/footer dropped), and
emits one self-contained HTML report: header, ordered screenshots
(Info/Event/Metric tags + minimal legends), global summary, anchored timeline,
and two RCA candidates (internal + customer-facing).

Image sizing rule: if the cropped image is wider than the report content width
it is scaled down proportionally to fit; otherwise it is shown at 80% of its
natural size (never enlarged).
"""
import base64
import io
import re
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).parent
VM = "azlsapgvpdb02"
CAP = ROOT / "captures" / VM
OUT = ROOT / f"report_{VM}.html"
REPORT_W = 1080  # px content width

ARM_ID = ("/subscriptions/c94548cf-d314-4bd5-abd2-eee92de2aab7/resourceGroups/"
          "AZ-RG-SAP-GVP-EastUS/providers/Microsoft.Compute/virtualMachines/azlsapgvpdb02")
WINDOW = "2026-07-07 00:00:00 &rarr; 2026-07-09 23:59:59 UTC"
CUSTOMER = "The Procter &amp; Gamble U.S. Business Services Company"
WIKI = "https://supportability.visualstudio.com/AzureIaaSVM/_wiki/wikis/AzureIaaSVM/500161/RCAs"

DASH_URL = (
    "https://asw-main-c9d6bfgzgnbydnae.eus2.grafana.azure.com/d/tictrm7/"
    "virtual-machine-reboot-analyzer?orgId=1"
    "&from=2026-07-07T00:00:00.000Z&to=2026-07-09T23:59:59.000Z&timezone=utc"
    "&var-_id=%2Fsubscriptions%2Fc94548cf-d314-4bd5-abd2-eee92de2aab7"
    "%2FresourceGroups%2FAZ-RG-SAP-GVP-EastUS%2Fproviders%2FMicrosoft.Compute"
    "%2FvirtualMachines%2Fazlsapgvpdb02"
)

# Order follows the panel list in the task, VM Events first.
# (anchor, filename-slug, tag, legend, scrollable_note)
PANELS = [
    ("p-events", "panel-04-vm-events.png", "Event",
     "Impact counters are all &gt; 0 and frame the whole window: <b>Live Migration 1</b>, "
     "<b>Nodes Degraded 1</b>, <b>Placements 1</b>, <b>Scheduled Events 1</b>, VM CRUD 0.", False),
    ("p-info", "panel-01-virtual-machine-current-info.png", "Info",
     "Core identity &mdash; customer <b>P&amp;G U.S. Business Services</b>, subscription "
     "<b>PG-NA-ENTERPRISE-PROD-05</b>, region East US. VM Id <code>867dd53a-7c85-4d4e-9e40-d5399fc27bb5</code>, current node "
     "<code>df6c4d5b-0ce9-2abf-17ee-78022e30d2ed</code>, container <code>9ab33c60-0988-46f2-8738-e9af15e99f64</code>: the IDs used to correlate the events "
     "below.", False),
    ("p-features", "panel-05-vm-details-features.png", "Info",
     "SKU <b>Standard_M32bds_v3</b> (large-memory M-series, typical of an in-memory / Oracle "
     "database tier) and <b>LiveMigration Eligible: Yes</b> &mdash; the platform is permitted to "
     "live-migrate this VM off a faulty host.", False),
    ("p-os", "panel-06-os-image-details.png", "Info",
     "OS billing type <b>Linux_IaaS_Oracle</b> &mdash; a Linux VM running an Oracle database "
     "(BYOS). A sensitive, stateful DB workload.", False),
    ("p-ext", "panel-02-installed-extensions.png", "Info",
     "Extensions installed on the VM (monitoring / backup agents).", False),
    ("p-tags", "panel-03-vm-tags.png", "Info",
     "Tags identify a <b>production SAP database</b>: <code>resource_set_name = Azure SAP Prod</code>, "
     "<code>Stage = Prod</code>, <code>Sox_Criticality = Yes</code>, <code>Regulated_System = Yes</code>, "
     "Data Classification <b>Highly Restricted</b>, application <b>Supply Chain (NA)</b>, managed by "
     "SAP CTE DBA groups. A critical, regulated, disruption-sensitive system.", True),
    # Outages -> No data (never captured); CPU & Memory -> discarded as normal.
    ("p-placement", "panel-14-vm-placement.png", "Event",
     "<b>Two</b> placement rows &mdash; the VM moved between nodes. It ran on node "
     "<code>01ea29c8-4e86-cb82-9ce0-6ed35c673d5b</code> since 2026-05-06, then was re-placed on node <code>df6c4d5b-0ce9-2abf-17ee-78022e30d2ed</code> at "
     "<b>2026-07-08 20:50:23</b> (container <code>9ab33c60-0988-46f2-8738-e9af15e99f64</code>). A second placement line = "
     "disruption.", False),
    ("p-tor", "panel-16-node-and-tor-placement-60-days.png", "Info",
     "Node/TOR history (&lt;60 days) corroborating the move: current node <code>df6c4d5b-0ce9-2abf-17ee-78022e30d2ed</code> "
     "since 2026-07-08 20:50, previously <code>01ea29c8-4e86-cb82-9ce0-6ed35c673d5b</code> since 2026-05-06.", True),
    ("p-rca", "panel-17-rca-helper-node-events-and-errors-check-https-supp.png", "Event",
     "Infrastructure event chain. Red row: node <code>01ea29c8-4e86-cb82-9ce0-6ed35c673d5b</code> (the node the VM was running "
     "on) went <b>NodeHealth: Degraded &rarr; Unallocatable at 2026-07-08 20:35</b>. At 20:50 the VM "
     "was placed on <code>df6c4d5b-0ce9-2abf-17ee-78022e30d2ed</code>; at 20:51 a <b>LiveMigration</b> workflow (Freeze on "
     "Network/Disk/Compute/OS) executed. Customer-facing RCA messages: "
     f"<a href=\"{WIKI}\" target=\"_blank\" rel=\"noopener\">{WIKI}</a>", True),
    ("p-sched-graph", "panel-19-scheduled-events-reboots.png", "Event",
     "Timeline view: one scheduled event (orange bar) around 2026-07-08 20:50&ndash;21:17 and "
     "<b>no reboot dots</b> &mdash; a maintenance event with no OS reboot.", False),
    # Reboot Detail -> No data (never captured).
    ("p-sched-detail", "panel-21-scheduled-events-detail.png", "Event",
     "The scheduled event decoded: <b>Type LiveMigration</b>, Initiator <b>Infrastructure</b>, window "
     "2026-07-08 20:51:23&ndash;21:17:03, <b>Freeze</b> on Disk/Network/Compute/OS &mdash; "
     "platform-initiated, not customer-initiated.", False),
    ("p-lm", "panel-22-live-migration-events.png", "Event",
     "Live migration completed <b>2026-07-08 21:16:16</b>. TriggerType <b>UnallocatableNode</b>, reason "
     "<b>&quot;Bad hardware health&quot;</b> / &quot;1093 Nodes with Soft Errors &hellip; Fatal HW "
     "repair&quot;. <b>IsCustomerInitiatedOperation: false</b>, isGuestOsCrash: false &mdash; a "
     "reactive platform migration off failing hardware.", False),
    ("p-health", "panel-23-vm-health-annotations.png", "Event",
     "Controller annotations: at <b>20:35&ndash;20:36</b> "
     "<b>VirtualMachinePossiblyDegradedDueToHardwareFailure</b> (degraded / memory / crashes); at "
     "<b>21:10</b> <b>LiveMigrationSucceeded</b> with a blackout of <b>~1.8 s</b> (TriggerType "
     "UnallocatableNode).", False),
    ("p-queue", "panel-25-data-os-temp-disk-queue-length.png", "Metric",
     "Disk queue length shows scattered transient spikes crossing the 10 threshold band (peaks ~27, "
     "~26) spread across the whole window &mdash; not sustained and <b>not</b> time-correlated with "
     "the 20:50&ndash;21:17 migration. Included so a storage cause can be ruled out.", False),
    ("p-latency", "panel-26-data-os-temp-disk-latency-in-milliseconds.png", "Metric",
     "Disk latency is low (&lt;5 ms baseline) with isolated transient spikes (30&ndash;44 ms) across "
     "the window, none aligned to the incident time. No sustained pressure.", False),
]

DISCARDED = [
    ("CPU % (Avg)", "Low utilisation ~1&ndash;8% with one minor spike to ~12%. No sustained load."),
    ("% Memory Pressure (Max)", "Max ~10%, well within normal. No pressure."),
    ("Ram size and Available ram (Max)", "~125 GB free of 275 GB throughout &mdash; ample headroom."),
    ("VM Bandwidth Consumed %", "Low single-digit % of the VM cap; no saturation."),
    ("VM IOPS Consumed %", "0&ndash;3% of the VM cap; far from saturation."),
    ("Data and OS Disk Bandwidth Consumed % (per Lun)", "Peaks ~27%, mostly &lt;10%; no LUN saturation."),
    ("Data and OS Disk IOPS Consumed % (per Lun)", "Peaks ~15%, mostly &lt;10%; no LUN saturation."),
]

NODATA = [
    ("Outages", "No regional VM outage overlapped the window."),
    ("Reboot Detail", "No OS reboot was recorded for the VM in the window."),
]

TIMELINE = [
    ("2026-07-08 20:35", "Node degraded",
     "Host node <code>01ea29c8-4e86-cb82-9ce0-6ed35c673d5b</code> flagged NodeHealth Degraded &rarr; Unallocatable due to "
     "hardware failure (memory / crashes).", "p-rca"),
    ("2026-07-08 20:36", "Node degraded",
     "Second VirtualMachinePossiblyDegradedDueToHardwareFailure annotation (LiveMigration eligible).",
     "p-health"),
    ("2026-07-08 20:50:23", "Placement / migration start",
     "VM re-placed on healthy node <code>df6c4d5b-0ce9-2abf-17ee-78022e30d2ed</code> (container <code>9ab33c60-0988-46f2-8738-e9af15e99f64</code>); live "
     "migration begins.", "p-placement"),
    ("2026-07-08 20:51:23", "Scheduled event",
     "Infrastructure-initiated LiveMigration scheduled event opens (Freeze Disk/Net/Compute/OS), "
     "est. window to 21:17:03.", "p-sched-detail"),
    ("2026-07-08 21:10", "Migration blackout",
     "LiveMigrationSucceeded &mdash; VM frozen for ~1.8 s during cutover.", "p-health"),
    ("2026-07-08 21:16:16", "Migration completed",
     "Live migration Completed. Root cause UnallocatableNode / bad hardware health.", "p-lm"),
]

TAG_CLASS = {"Info": "tag-info", "Event": "tag-event", "Metric": "tag-metric"}


def content_crop(im, thresh=24, pad=8, min_gap=90):
    """Trim to the populated content band, keeping the title at the top-left.
    After autocrop an over-tall panel may still contain a large interior black
    gap followed by a detached footer row. Find the largest interior near-black
    run; if big enough and below real content, cut at its start so the image
    hugs just the title + populated rows/graph."""
    g = im.convert("L")
    w, h = g.size
    px = g.load()

    def row_has_content(y):
        n = 0
        for x in range(0, w, 3):
            if px[x, y] > thresh:
                n += 1
                if n >= 4:
                    return True
        return False

    rows = [row_has_content(y) for y in range(h)]
    top = next((y for y in range(h) if rows[y]), None)
    if top is None:
        return im
    last = next((y for y in range(h - 1, -1, -1) if rows[y]), top)

    best_start, best_len = None, 0
    run_start, run = None, 0
    for y in range(top, last + 1):
        if not rows[y]:
            if run_start is None:
                run_start = y
            run += 1
        else:
            if run > best_len:
                best_len, best_start = run, run_start
            run_start, run = None, 0

    bottom = last + 1
    if best_start is not None and best_len >= min_gap and best_start - top >= 30:
        bottom = best_start

    t = max(0, top - pad)
    b = min(h, bottom + pad)
    if b - t < 20 or (t == 0 and b == h):
        return im
    return im.crop((0, t, w, b))


def resolve_file(fn):
    """Match by title-slug (filename minus 'panel-NN-'); indices are unstable."""
    want = re.sub(r"^panel-\d+-", "", fn)
    for p in sorted(CAP.glob("panel-*.png")):
        if re.sub(r"^panel-\d+-", "", p.name) == want:
            return p
    return CAP / fn


def prep_img(fn):
    im = Image.open(resolve_file(fn)).convert("RGB")
    im = content_crop(im)
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode(), im.width


def display_width(w):
    """Wider than the report -> scale down to fit. Otherwise -> 80% (never enlarge)."""
    return REPORT_W if w > REPORT_W else round(w * 0.8)


def panel_block(anchor, fn, tag, legend, scroll):
    data, w = prep_img(fn)
    style = f"width:{display_width(w)}px;max-width:100%;"
    note = ('<div class="scrollnote">Source panel is scrollable &mdash; not all rows/columns may be '
            'visible in this capture.</div>') if scroll else ""
    return f"""
    <section class="panel" id="{anchor}">
      <span class="tag {TAG_CLASS[tag]}">{tag}</span>
      <div class="legend">{legend}</div>
      <img src="data:image/png;base64,{data}" alt="{anchor}" style="{style}"/>
      {note}
    </section>"""


def main():
    panels_html = "".join(panel_block(*p) for p in PANELS)
    tl_rows = "".join(
        f'<tr><td class="tl-ts">{ts}</td><td class="tl-type">{ty}</td>'
        f'<td>{desc}</td><td><a href="#{a}">view&nbsp;&rarr;</a></td></tr>'
        for ts, ty, desc, a in TIMELINE)
    discarded_html = "".join(f"<li><b>{n}</b> &mdash; {r}</li>" for n, r in DISCARDED)
    nodata_html = "".join(f"<li><b>{n}</b> &mdash; {r}</li>" for n, r in NODATA)

    html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>VM Reboot Analyzer RCA &mdash; {VM}</title>
<style>
  :root{{--bg:#0d1117;--panel:#161b22;--line:#30363d;--fg:#e6edf3;--muted:#8b949e;
        --info:#1f6feb;--event:#a371f7;--metric:#db6d28;}}
  *{{box-sizing:border-box}}
  body{{margin:0;background:var(--bg);color:var(--fg);
       font:15px/1.55 -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif}}
  .wrap{{max-width:{REPORT_W}px;margin:0 auto;padding:32px 22px 80px}}
  h1{{font-size:22px;margin:0 0 6px}}
  h2{{font-size:18px;margin:38px 0 14px;padding-bottom:6px;border-bottom:1px solid var(--line)}}
  h3{{font-size:15px;margin:18px 0 6px;color:var(--fg)}}
  .head{{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:18px 20px}}
  .head .row{{display:flex;gap:10px;margin:4px 0;flex-wrap:wrap}}
  .head .k{{color:var(--muted);min-width:120px}}
  code{{background:#21262d;padding:1px 5px;border-radius:4px;font-size:12.5px}}
  .verdict{{margin-top:14px;padding:12px 14px;border-left:4px solid var(--metric);
           background:#1c1712;border-radius:6px}}
  .panel{{background:var(--panel);border:1px solid var(--line);border-radius:10px;
         padding:14px 16px 16px;margin:16px 0}}
  .panel img{{height:auto;border-radius:6px;margin-top:10px;border:1px solid var(--line);
             background:#000;display:block}}
  .tag{{display:inline-block;font-size:11px;font-weight:700;letter-spacing:.04em;
       text-transform:uppercase;padding:2px 9px;border-radius:20px;color:#fff}}
  .tag-info{{background:var(--info)}} .tag-event{{background:var(--event)}}
  .tag-metric{{background:var(--metric)}}
  .legend{{margin-top:8px;color:var(--fg)}}
  .legend a{{word-break:break-all}}
  .scrollnote{{margin-top:8px;color:var(--muted);font-size:12.5px;font-style:italic}}
  ul{{margin:8px 0 0;padding-left:20px}} li{{margin:5px 0}}
  table{{width:100%;border-collapse:collapse;margin-top:10px;font-size:13.5px}}
  th,td{{text-align:left;padding:8px 10px;border-bottom:1px solid var(--line);vertical-align:top}}
  th{{color:var(--muted);font-weight:600}}
  .tl-ts{{white-space:nowrap;color:#79c0ff;font-variant-numeric:tabular-nums}}
  .tl-type{{white-space:nowrap;color:var(--event);font-weight:600}}
  a{{color:#58a6ff;text-decoration:none}} a:hover{{text-decoration:underline}}
  .rca{{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:6px 18px 14px}}
  .rca.cust{{border-left:4px solid var(--info)}}
  .rca.intern{{border-left:4px solid var(--event)}}
  .rca p{{margin:8px 0}}
  .dashwrap{{margin-top:40px;text-align:center}}
  a.dashlink{{display:inline-block;background:var(--info);color:#fff;font-weight:600;
             padding:11px 22px;border-radius:8px;text-decoration:none}}
  footer{{margin-top:26px;color:var(--muted);font-size:12px;text-align:center}}
</style></head><body><div class="wrap">

<h1>Virtual Machine Reboot Analyzer &mdash; RCA</h1>
<div class="head">
  <div class="row"><span class="k">ARM Id</span><code>{ARM_ID}</code></div>
  <div class="row"><span class="k">Time range</span><span>{WINDOW}</span></div>
  <div class="row"><span class="k">Customer</span><span>{CUSTOMER}</span></div>
  <div class="verdict"><b>Most likely hypothesis:</b> No OS reboot and no regional outage occurred.
  The VM was <b>reactively live-migrated</b> off a host node that failed a hardware health check
  (memory faults) and was declared <b>Unallocatable</b>, incurring a ~1.8&nbsp;s freeze &mdash; the
  most probable trigger for the customer-perceived &ldquo;stop&rdquo;.</div>
</div>

<h2>Captured panels</h2>
{panels_html}

<h2>Global summary</h2>
<p>On <b>2026-07-08</b> the physical host running <code>azlsapgvpdb02</code> (node
<code>01ea29c8-4e86-cb82-9ce0-6ed35c673d5b</code>) developed a <b>hardware fault (memory errors / crashes)</b> and was marked
<b>Degraded &rarr; Unallocatable at 20:35</b>. The Azure platform reacted by <b>live-migrating the
VM to a healthy node</b> (<code>df6c4d5b-0ce9-2abf-17ee-78022e30d2ed</code>): placement at <b>20:50:23</b>, an
Infrastructure-initiated LiveMigration scheduled event (Freeze all) from <b>20:51:23</b>, a cutover
freeze of <b>~1.8&nbsp;s at 21:10</b>, and completion at <b>21:16:16</b> (root cause
&ldquo;UnallocatableNode / bad hardware health&rdquo;). This is a production P&amp;G SAP Oracle DB
(SOX-regulated, Highly Restricted), so even a sub-2&nbsp;second freeze can be felt.</p>
<p><b>Panels that returned &ldquo;No data&rdquo;</b> (not captured):</p>
<ul>{nodata_html}</ul>
<p><b>Panels discarded as not relevant</b> (captured but normal &mdash; no sustained high values; any
spikes were transient and not time-correlated with the migration):</p>
<ul>{discarded_html}</ul>
<p><b>Error panels:</b> none &mdash; every panel either rendered data or explicitly showed
&ldquo;No data&rdquo;; no error (red-icon) panels were observed.</p>

<h2>Timeline of findings</h2>
<table><thead><tr><th>Timestamp (UTC)</th><th>Type</th><th>Description</th><th></th></tr></thead>
<tbody>{tl_rows}</tbody></table>

<h2>RCA candidate 1 &mdash; internal</h2>
<div class="rca intern">
<p><b>Most likely explanation.</b> There was <b>no reboot</b> (Reboot Detail = No data; no red dots on
the Scheduled Events &amp; Reboots graph) and <b>no outage</b> in region East US. The one impactful
event was a <b>platform-initiated live migration</b>: the host node the VM was running on
(<code>01ea29c8-4e86-cb82-9ce0-6ed35c673d5b</code>) failed a hardware health check (memory faults / crashes) and was declared
<b>Degraded &rarr; Unallocatable at 20:35 on 2026-07-08</b>. The VM was reactively migrated to a
healthy node (<code>df6c4d5b-0ce9-2abf-17ee-78022e30d2ed</code>): placement 20:50:23, Infrastructure LiveMigration scheduled
event 20:51:23&ndash;21:17:03 (Freeze all), a measured guest freeze of <b>~1.8&nbsp;s at 21:10</b>,
and completion 21:16:16. TriggerType <code>UnallocatableNode</code>, RCA
&ldquo;Bad hardware health&rdquo;; <code>IsCustomerInitiatedOperation=false</code>,
<code>isGuestOsCrash=false</code>.</p>
<p><b>Customer context.</b> <code>azlsapgvpdb02</code> is a large-memory <code>Standard_M32bds_v3</code>
running an <b>Oracle database on Linux</b>, tagged <b>Azure SAP Prod</b> / <code>Stage=Prod</code>,
<b>SOX-regulated</b>, <b>Highly Restricted</b>, supporting the <b>Supply Chain (NA)</b> application and
administered by SAP CTE DBA teams. Clustered/HA database workloads of this kind are highly sensitive
to even sub-second pauses: a ~1.8&nbsp;s live-migration blackout can be enough for a cluster manager
(e.g. Pacemaker) or the database's own HA layer to interpret the freeze as a node failure and
fence/fail over the node &mdash; which surfaces to the customer as an unexpected stop, and can even
appear later as a &ldquo;customer initiated&rdquo; restart if a fencing agent acted.</p>
<p><b>Ruled-out factors.</b> Performance was not implicated: CPU ~1&ndash;8%, memory pressure &le;10%,
~125&nbsp;GB RAM free, disk BW/IOPS consumption in the low single digits; disk queue/latency showed
only isolated transient spikes unrelated to the migration time.</p>
<p><b>Suggested further investigation.</b> (1) Confirm the exact time the customer observed the
disruption and correlate against the <b>~21:10 UTC</b> cutover. (2) Pull guest OS and Oracle/cluster
logs around 2026-07-08 21:05&ndash;21:20 UTC for fencing, failover, evictions or I/O-freeze messages.
(3) Verify whether an HA/cluster fencing action occurred and, if so, tune cluster/corosync timeouts to
tolerate short live-migration blackouts. (4) Check for any dependency on external services that could
have compounded the pause.</p>
</div>

<h2>RCA candidate 2 &mdash; customer-facing (draft)</h2>
<div class="rca cust">
<p><b>Summary.</b> On 8 July 2026, at approximately 21:10 UTC, your virtual machine was briefly paused
while the Azure platform relocated it to alternative physical hardware as an automated protective
maintenance action. The virtual machine was not restarted by the platform and remained available
before and after the operation.</p>
<p><b>Root Cause.</b> The physical host on which the virtual machine was running began to show early
indicators of a hardware issue. To protect the workload, Azure automatically live-migrated the virtual
machine to healthy hardware. Live migration involves a very short pause (in this case approximately two
seconds) while memory and state are transferred. No platform outage was detected in the region during
this period, and no platform-initiated operating-system reboot occurred.</p>
<p><b>Resolution.</b> The virtual machine was successfully relocated to healthy hardware and the
affected host was taken out of service. No customer action is required, and the virtual machine
continues to run normally.</p>
<p><b>Customer Impact.</b> A single, brief pause of approximately two seconds around 21:10 UTC on
8 July 2026. For most workloads this is transparent; however, highly sensitive clustered or
high-availability configurations may react to such a brief pause &mdash; for example by initiating a
failover &mdash; which could be perceived as an unexpected stop. We recommend reviewing application and
cluster logs around this time to confirm whether any such failover was triggered.</p>
</div>

<div class="dashwrap">
  <a class="dashlink" href="{DASH_URL}" target="_blank" rel="noopener">
    Open full Virtual Machine Reboot Analyzer dashboard &rarr;</a>
</div>

<footer>Generated from Virtual Machine Reboot Analyzer captures &middot; {VM} &middot; {WINDOW}</footer>
</div></body></html>"""

    OUT.write_text(html, encoding="utf-8")
    print(f"Wrote {OUT}  ({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
