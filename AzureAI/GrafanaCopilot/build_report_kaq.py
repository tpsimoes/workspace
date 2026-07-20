"""Build the VM Reboot Analyzer RCA report for azlsapkaqdb06.

Reads captured panel PNGs from captures/<vm>/, resolves each by title-slug
(panel index is not stable across scrapes), tightens each image to just the
content band (top-left aligned, title kept, trailing blank/footer dropped), and
emits one self-contained HTML report: header, ordered screenshots
(Info/Event/Metric tags + minimal legends), global summary, anchored timeline,
and two RCA candidates (internal + customer-facing).

This VM DID reboot (unlike azlsapgvpdb02): a predicted memory hardware fault on
the source host triggered a reactive live migration, and the VM was restarted
(~1 min) via a rebootful host-environment update while landing on the target
host. All node/container/VM IDs are quoted as full GUIDs (sourced from the VM
Placement and Current Info panels).

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
VM = "azlsapkaqdb06"
CAP = ROOT / "captures" / VM
OUT = ROOT / f"report_{VM}.html"
REPORT_W = 1080  # px content width

ARM_ID = ("/subscriptions/c94548cf-d314-4bd5-abd2-eee92de2aab7/resourceGroups/"
          "AZ-RG-SAP-KAQ-EastUS/providers/Microsoft.Compute/virtualMachines/azlsapkaqdb06")
WINDOW = "2026-07-07 00:00:00 &rarr; 2026-07-09 23:59:59 UTC"
CUSTOMER = "The Procter &amp; Gamble U.S. Business Services Company"
WIKI = "https://supportability.visualstudio.com/AzureIaaSVM/_wiki/wikis/AzureIaaSVM/500161/RCAs"

# Full GUIDs (from VM Placement / Current Info panels)
VM_ID = "5634283c-d1cc-4186-ac37-6878e183935f"
SRC_NODE = "55f0378e-29d8-7595-d123-9f1dfa9a5046"      # faulty source host
SRC_CONT = "d338c642-59a8-4a3b-97d2-c418da575b48"
DST_NODE = "4566616c-b55f-a597-da36-305020a925e9"      # healthy destination host
DST_CONT = "b03127fd-9c69-490e-bd49-b69f8fce73d2"

DASH_URL = (
    "https://asw-main-c9d6bfgzgnbydnae.eus2.grafana.azure.com/d/tictrm7/"
    "virtual-machine-reboot-analyzer?orgId=1"
    "&from=2026-07-07T00:00:00.000Z&to=2026-07-09T23:59:59.000Z&timezone=utc"
    "&var-_id=%2Fsubscriptions%2Fc94548cf-d314-4bd5-abd2-eee92de2aab7"
    "%2FresourceGroups%2FAZ-RG-SAP-KAQ-EastUS%2Fproviders%2FMicrosoft.Compute"
    "%2FvirtualMachines%2Fazlsapkaqdb06"
)

# Order follows the panel list in the task, VM Events first.
# (anchor, filename-slug, tag, legend, scrollable_note)
PANELS = [
    ("p-events", "panel-04-vm-events.png", "Event",
     "Impact counters frame the whole window and a reboot did occur: <b>Reboots 1</b>, "
     "<b>Nodes Degraded 2</b>, <b>Live Migration 1</b>, <b>Placements 1</b>, "
     "<b>Scheduled Events 1</b>, VM CRUD 0. (Grafana truncates the labels in this narrow "
     "panel; the values 1&nbsp;/&nbsp;1&nbsp;/&nbsp;2&nbsp;/&nbsp;1&nbsp;/&nbsp;1&nbsp;/&nbsp;0 are "
     "Placements&nbsp;/&nbsp;Live&nbsp;Migration&nbsp;/&nbsp;Nodes&nbsp;Degraded&nbsp;/&nbsp;"
     "Scheduled&nbsp;Events&nbsp;/&nbsp;Reboots&nbsp;/&nbsp;VM&nbsp;CRUD.)", False),
    ("p-info", "panel-01-virtual-machine-current-info.png", "Info",
     "Core identity &mdash; customer <b>P&amp;G U.S. Business Services</b>, subscription "
     "<b>PG-NA-ENTERPRISE-PROD-05</b>, region <b>useast</b>. VirtualMachine Id "
     f"<code>{VM_ID}</code>, current node <code>{DST_NODE}</code>, container "
     f"<code>{DST_CONT}</code>, tenant <code>e8fd089b-37ee-4314-b626-95e10d1c8969</code>: the IDs "
     "used to correlate the events below.", False),
    ("p-features", "panel-05-vm-details-features.png", "Info",
     "SKU <b>Standard_M128ds_v2</b> (large-memory M-series, a database tier), "
     "<b>SAP Certified Sku: Yes</b>, in an <b>Availability Set</b> and <b>Proximity Placement "
     "Group</b>, Accelerated Networking on, and <b>LiveMigration Eligible: Yes</b> &mdash; the "
     "platform is permitted to live-migrate this VM off a faulty host.", False),
    ("p-os", "panel-06-os-image-details.png", "Info",
     "OS billing type <b>Linux_IaaS_Software_suse_sles_sap</b> (BYOS) &mdash; a Linux VM running "
     "<b>SUSE Linux Enterprise Server for SAP Applications</b>. A sensitive, stateful DB workload.", False),
    ("p-ext", "panel-02-installed-extensions.png", "Info",
     "Extensions installed on the VM &mdash; <b>SAPExtensions</b> (confirms an SAP workload), "
     "RunCommandLinux and PuppetEnterpriseAgent (configuration management).", False),
    ("p-tags", "panel-03-vm-tags.png", "Info",
     "Tags identify a <b>non-production (QA) SAP system</b>: <code>resource_set_name = Azure SAP "
     "Non-prod</code>, <code>Stage = QA</code>, <code>Application_Name = KAQ</code>, "
     "<code>Business_Criticality = 3 - less critical</code>. Still governance-sensitive: "
     "<code>Sox_Criticality = Yes</code>, <code>Regulated_System = Yes</code>, Data Classification "
     "<b>Highly Restricted</b>, owned by <b>GTO SAP CTR TECH EXPERTISE</b> / SAP CTE DBA groups.", True),
    # Outages -> No data (never captured); CPU & Memory + bandwidth/IOPS -> discarded as normal.
    ("p-placement", "panel-14-vm-placement.png", "Event",
     "<b>Two</b> placement rows &mdash; the VM moved between hosts. It ran on node "
     f"<code>{SRC_NODE}</code> (container <code>{SRC_CONT}</code>) since 2026-03-25 14:21:07, then "
     f"was re-placed on node <code>{DST_NODE}</code> (container <code>{DST_CONT}</code>) at "
     "<b>2026-07-07 22:17:21</b>. A second placement line = a relocation / disruption.", False),
    ("p-tor", "panel-16-node-and-tor-placement-60-days.png", "Info",
     f"Node/TOR history (&lt;60 days) corroborating the move: current node <code>{DST_NODE}</code> "
     "(IP 10.253.38.67, TOR iad20-0101-0709-07t0) since 2026-07-07 22:17, previously "
     f"<code>{SRC_NODE}</code> (IP 10.253.37.66, TOR iad20-0101-0709-05t0). Both in DataCenter "
     "IAD20AzSet1 / Cluster IAD20PrdApp22.", True),
    ("p-rca", "panel-17-rca-helper-node-events-and-errors-check-https-supp.png", "Event",
     "Infrastructure event chain (07-07). Red rows: source node "
     f"<code>{SRC_NODE}</code> (the node the VM was running on) went <b>NodeHealth: Degraded &rarr; "
     "Unallocatable at 22:06</b>; at 22:17 the VM was placed on <code>" + DST_NODE + "</code>; at "
     "22:19 an <b>Infrastructure LiveMigration</b> workflow ran (Freeze on "
     "Network/Disk/Compute/OS). The source node then <b>Faulted (FaultCode 10038)</b> at 23:09 and "
     "was sent <b>OutForRepair</b> at 23:20. Customer-facing RCA messages: "
     f"<a href=\"{WIKI}\" target=\"_blank\" rel=\"noopener\">{WIKI}</a>", True),
    ("p-sched-graph", "panel-19-scheduled-events-reboots.png", "Event",
     "Timeline view: one scheduled event (orange bar) on 2026-07-07 ~22:19&ndash;23:01 with a "
     "<b>red reboot dot inside it</b> &mdash; the reboot happened <b>during</b> the live-migration "
     "scheduled event, strongly implying the two are related.", False),
    ("p-reboot", "panel-20-reboot-detail.png", "Event",
     "The reboot decoded: <b>2026-07-07 22:52:50 &rarr; 22:53:51 (~1 min)</b>. "
     "RCA_CSS <b>Planned.RootHEUpdate Rebootful.Out_of_band_HE_update_by_BatchingManager</b> and "
     "TM_RCA <b>Unplanned.ContainerFault.LiveMigration TriggerType,UnallocatableNode</b> &mdash; a "
     "rebootful host-environment (node OS image) update tied to the migration off the unallocatable "
     "host. Detail: node OS image update WAOS_WS19H ...20348.1075 &rarr; ...26102.1083.", True),
    ("p-sched-detail", "panel-21-scheduled-events-detail.png", "Event",
     "The scheduled event decoded: <b>Type LiveMigration</b>, Initiator <b>Infrastructure</b>, "
     "window 2026-07-07 22:19:06&ndash;23:01:02, <b>Freeze</b> on Disk/Network/Compute/OS, estimated "
     "5&nbsp;min but actual <b>42&nbsp;min</b>, ImpactState ApprovalRequested &mdash; "
     "platform-initiated, not customer-initiated.", False),
    ("p-lm", "panel-22-live-migration-events.png", "Event",
     "Live migration <b>Completed 2026-07-07 23:00:16</b>. RCA <b>UnallocatableNode: Bad hardware "
     "health</b>, reason <b>&quot;1083 Samsung CB2 prediction &hellip; RuleType: Failure "
     "Prediction&quot;</b>, &quot;Final memory transfer pass (source node)&quot;. "
     "<b>IsCustomerInitiatedOperation: false</b>, isGuestOsCrash: false. Session "
     "<code>ec3dc32f-2294-43fa-87dd-bbaeeefcb76b</code>, HyperVVMId "
     f"<code>0039b729-a799-4511-9add-963c1f6398e2</code>, destination node <code>{DST_NODE}</code> "
     "&mdash; a reactive platform migration off failing hardware.", True),
    ("p-health", "panel-23-vm-health-annotations.png", "Event",
     "Controller annotations: at <b>22:06&ndash;22:07</b> "
     "<b>VirtualMachinePossiblyDegradedDueToHardwareFailureLiveMigrationEligible</b> (degraded / "
     "memory / crashes); at <b>22:54</b> <b>LiveMigrationSucceeded</b> with a guest blackout of "
     "<b>~2.581&nbsp;s</b> (TriggerType UnallocatableNode).", False),
    ("p-queue", "panel-25-data-os-temp-disk-queue-length.png", "Metric",
     "Disk queue length is flat &lt;10 for almost the entire window with a single isolated spike to "
     "~145 on <b>2026-07-09 ~06:00</b> &mdash; <b>well after</b> the 07-07 incident and <b>not</b> "
     "correlated with it. Included so a storage cause for the reboot can be ruled out.", False),
    ("p-latency", "panel-26-data-os-temp-disk-latency-in-milliseconds.png", "Metric",
     "Disk latency is low (&lt;5 ms baseline) with the same isolated spike (~265 ms) on "
     "2026-07-09 ~06:00, post-incident. VM IOPS consumption peaked at only ~3% throughout, so the "
     "VM was never near its storage limits &mdash; no sustained pressure.", False),
]

DISCARDED = [
    ("CPU % (Avg)", "Low utilisation, mostly &lt;5% with a few brief spikes (max ~34% once). No sustained load."),
    ("% Memory Pressure (Max)", "Stable at ~72&ndash;76% with no spikes at the incident time. No memory crisis in-guest."),
    ("Ram size and Available ram (Max)", "RamSize ~2&nbsp;TB with stable available memory throughout &mdash; no abnormal drop."),
    ("VM Bandwidth Consumed %", "Low single-digit % of the VM cap; no saturation."),
    ("VM IOPS Consumed %", "0&ndash;3% of the VM cap; far from saturation."),
    ("Data and OS Disk Bandwidth Consumed % (per Lun)", "Low throughout; no LUN saturation."),
    ("Data and OS Disk IOPS Consumed % (per Lun)", "Low throughout; no LUN saturation."),
]

NODATA = [
    ("Outages", "No regional VM outage overlapped the window."),
]

TIMELINE = [
    ("2026-07-07 22:06", "Node degraded",
     f"Host node <code>{SRC_NODE}</code> flagged NodeHealth Degraded &rarr; Unallocatable "
     "(memory hardware fault / crashes; predicted failure).", "p-rca"),
    ("2026-07-07 22:06&ndash;22:07", "Node degraded",
     "VirtualMachinePossiblyDegradedDueToHardwareFailureLiveMigrationEligible annotations "
     "(degraded / memory / crashes).", "p-health"),
    ("2026-07-07 22:17:21", "Placement / migration start",
     f"VM re-placed on healthy node <code>{DST_NODE}</code> (container <code>{DST_CONT}</code>); "
     "live migration begins.", "p-placement"),
    ("2026-07-07 22:19:06", "Scheduled event",
     "Infrastructure-initiated LiveMigration scheduled event opens (Freeze Disk/Net/Compute/OS), "
     "window to 23:01:02 (actual ~42 min).", "p-sched-detail"),
    ("2026-07-07 22:52:50", "Reboot",
     "VM restarted (~1 min, to 22:53:51) via a rebootful host-environment (node OS image) update "
     "&mdash; RCA_CSS Planned.RootHEUpdate, TM_RCA LiveMigration/UnallocatableNode.", "p-reboot"),
    ("2026-07-07 22:54", "Migration blackout",
     "LiveMigrationSucceeded &mdash; guest frozen for ~2.581 s during cutover.", "p-health"),
    ("2026-07-07 23:00:16", "Migration completed",
     "Live migration Completed. Root cause UnallocatableNode / bad hardware health.", "p-lm"),
    ("2026-07-07 23:09&ndash;23:20", "Node repaired",
     f"Source node <code>{SRC_NODE}</code> Faulted (FaultCode 10038) then sent OutForRepair.", "p-rca"),
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
  <div class="verdict"><b>Most likely hypothesis:</b> The host running the VM
  (node <code>{SRC_NODE}</code>) showed a <b>predicted memory hardware failure</b> and was declared
  <b>Unallocatable</b>. Azure <b>reactively live-migrated</b> the VM to a healthy host
  (<code>{DST_NODE}</code>); during that relocation the VM was <b>restarted for ~1&nbsp;minute at
  22:52:50 UTC</b> (rebootful host-environment update) and additionally experienced a ~2.6&nbsp;s
  migration freeze &mdash; the direct explanation for the customer-reported restart.</div>
</div>

<h2>Captured panels</h2>
{panels_html}

<h2>Global summary</h2>
<p>On <b>2026-07-07</b> the physical host running <code>{VM}</code> (node
<code>{SRC_NODE}</code>) developed a <b>hardware fault (predicted memory failure &mdash; &ldquo;1083
Samsung CB2 prediction&rdquo;, crashes)</b> and was marked <b>Degraded &rarr; Unallocatable at
22:06</b>. The Azure platform reacted by <b>live-migrating the VM to a healthy node</b>
(<code>{DST_NODE}</code>): placement at <b>22:17:21</b>, an Infrastructure-initiated LiveMigration
scheduled event (Freeze all) from <b>22:19:06</b> to <b>23:01:02</b>. During the relocation the VM was
<b>restarted for ~1&nbsp;minute (22:52:50&rarr;22:53:51)</b> via a rebootful host-environment
(node&nbsp;OS image) update, and the migration cutover froze the guest for <b>~2.581&nbsp;s at
22:54</b>; the migration <b>Completed at 23:00:16</b> (root cause &ldquo;UnallocatableNode / bad
hardware health&rdquo;). The faulty source node was subsequently <b>Faulted (FaultCode 10038)</b> and
sent <b>OutForRepair</b>. This is a <b>QA / non-production SAP database</b> (application KAQ, SUSE SLES
for SAP), but still SOX-regulated and Highly Restricted, so even a short pause plus a 1-minute restart
is clearly noticed.</p>
<p><b>Panels that returned &ldquo;No data&rdquo;</b> (not captured):</p>
<ul>{nodata_html}</ul>
<p><b>Panels discarded as not relevant</b> (captured but normal &mdash; no sustained high values at
the incident time; the only disk spike was on 2026-07-09, well after the event):</p>
<ul>{discarded_html}</ul>
<p><b>Error panels:</b> none &mdash; every panel either rendered data or explicitly showed
&ldquo;No data&rdquo;; no error (red-icon) panels were observed in the final capture set.</p>

<h2>Timeline of findings</h2>
<table><thead><tr><th>Timestamp (UTC)</th><th>Type</th><th>Description</th><th></th></tr></thead>
<tbody>{tl_rows}</tbody></table>

<h2>RCA candidate 1 &mdash; internal</h2>
<div class="rca intern">
<p><b>Most likely explanation.</b> The host node the VM was running on
(<code>{SRC_NODE}</code>) triggered a <b>predicted memory hardware failure</b> (Live Migration Events
FailureReason &ldquo;1083 Samsung CB2 prediction &hellip; RuleType: Failure Prediction&rdquo;) and was
declared <b>NodeHealth Degraded &rarr; Unallocatable at 22:06 on 2026-07-07</b>, later Faulted
(FaultCode 10038) and OutForRepair. The platform reactively live-migrated the VM to healthy node
<code>{DST_NODE}</code> (container <code>{DST_CONT}</code>): placement 22:17:21, Infrastructure
LiveMigration scheduled event 22:19:06&ndash;23:01:02 (Freeze all, estimated 5&nbsp;min but actual
~42&nbsp;min). The Scheduled Events &amp; Reboots graph shows a <b>reboot dot inside the scheduled-event
bar</b>: the VM was <b>restarted 22:52:50&rarr;22:53:51 (~1&nbsp;min)</b>, attributed by Reboot Detail
to <code>Planned.RootHEUpdate&nbsp;Rebootful.Out_of_band_HE_update_by_BatchingManager</code>
(a rebootful node-OS-image update, WAOS_WS19H ...20348.1075&rarr;...26102.1083) and by TM_RCA to
<code>Unplanned.ContainerFault.LiveMigration&nbsp;TriggerType,UnallocatableNode</code>. The migration
cutover then froze the guest for <b>~2.581&nbsp;s at 22:54</b> and Completed at 23:00:16.
<code>IsCustomerInitiatedOperation=false</code>, <code>isGuestOsCrash=false</code> &mdash; this was a
platform-driven event, not a guest crash or a customer restart.</p>
<p><b>Customer context.</b> <code>{VM}</code> is a large-memory <code>Standard_M128ds_v2</code>
running <b>SUSE SLES for SAP on Linux</b>, tagged <b>Azure SAP Non-prod</b> / <code>Stage=QA</code>,
application <b>KAQ</b>, <code>Business_Criticality = 3 - less critical</code>, but still
<b>SOX-regulated</b> and <b>Highly Restricted</b>, administered by GTO SAP CTE DBA teams. Even though
this is QA, a ~1-minute restart plus a ~2.6&nbsp;s freeze is unambiguously visible; on clustered SAP
DB workloads a live-migration blackout can also prompt a cluster manager (e.g. Pacemaker) to fence or
fail over, which can surface as an additional unexpected stop.</p>
<p><b>Ruled-out factors.</b> No regional outage overlapped the window. In-guest performance was not
implicated: CPU mostly &lt;5%, memory pressure stable at ~72&ndash;76%, RAM available stable, disk
BW/IOPS in the low single digits. The only disk queue/latency spike (~145 / ~265&nbsp;ms) occurred on
<b>2026-07-09 ~06:00</b>, well after the incident, and is not correlated.</p>
<p><b>Suggested further investigation.</b> (1) Confirm the exact time the customer observed the restart
and correlate against the <b>22:52:50&ndash;22:53:51 UTC</b> reboot and the <b>22:54</b> cutover freeze.
(2) Clarify with the Live Migration / Host-Environment teams whether the rebootful HE update was
inherent to landing on the updated target host or a separately-scheduled concurrent update, since the
1-minute restart is the bulk of the customer-perceived impact. (3) Pull guest OS and SAP/cluster logs
around 2026-07-07 22:50&ndash;23:01 UTC for fencing, failover or I/O-freeze messages. (4) Review why
the migration ran ~42&nbsp;min against a 5-min estimate (large 2&nbsp;TB memory footprint).</p>
</div>

<h2>RCA candidate 2 &mdash; customer-facing (draft)</h2>
<div class="rca cust">
<p><b>Summary.</b> On 7 July 2026, at approximately 22:52&ndash;22:53 UTC, your virtual machine was
briefly restarted (about one minute) while the Azure platform relocated it to alternative, updated
physical hardware as an automated protective maintenance action. Around the same window the virtual
machine also experienced a very short pause of approximately two to three seconds during the
relocation.</p>
<p><b>Root Cause.</b> The physical host on which the virtual machine was running began to show early
indicators of a hardware (memory) issue. To protect the workload, Azure automatically live-migrated the
virtual machine to healthy hardware running an updated host platform. As part of moving to that updated
hardware, the virtual machine underwent a brief restart, and the migration itself involved a short
pause while memory and state were transferred. No platform outage was detected in the region during
this period.</p>
<p><b>Resolution.</b> The virtual machine was successfully relocated to healthy, updated hardware and
the affected host was taken out of service for repair. No customer action is required, and the virtual
machine has been operating normally since.</p>
<p><b>Customer Impact.</b> A brief restart of approximately one minute, together with a short pause of
a few seconds, around 22:52&ndash;22:54 UTC on 7 July 2026. For most workloads this is a brief,
one-off interruption; however, sensitive clustered or high-availability database configurations may
also react to such an event &mdash; for example by initiating a failover. We recommend reviewing
application and cluster logs around this time to confirm whether any such failover was triggered.</p>
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
