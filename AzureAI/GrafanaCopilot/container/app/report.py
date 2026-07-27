#!/usr/bin/env python3
"""Generic VM Reboot Analyzer report builder.

Consumes a scrape manifest (list of {index,title,no_data,text,file}) plus the
captured panel PNGs and emits one self-contained dark-theme HTML report in the
same style as the hand-authored reports: header, ordered Info/Event/Metric
screenshots with legends, a global summary, an anchored timeline, and two
heuristic RCA candidates (internal + customer-facing).

Because this runs headless in a container without an LLM in the loop, the
legends and RCA prose are generated programmatically from the panel text
(titles, event rows, detected signals). The RCA section is clearly labelled as
auto-generated and lists the signals it keyed off so an engineer can refine it.
"""
import base64
import io
import re
from html import escape
from pathlib import Path
from urllib.parse import unquote, urlparse, parse_qs

from PIL import Image

REPORT_W = 1080

METRIC_HINT = ("cpu", "memory", "ram", "disk", "iops", "bandwidth", "latency",
               "queue", "%", "consumed", "pressure")
EVENT_HINT = ("event", "reboot", "migration", "placement", "rca", "health",
              "schedule", "outage", "tor", "node")
ABNORMAL = ("error", "fail", "failure", "degraded", "impact", "freeze", "fault",
            "reboot", "unallocatable", "crash", "outage", "migration", "unhealthy",
            "outforrepair", "diagnosing")
WIKI = ("https://supportability.visualstudio.com/AzureIaaSVM/_wiki/wikis/"
        "AzureIaaSVM/500161/RCAs")
TAG_CLASS = {"Info": "tag-info", "Event": "tag-event", "Metric": "tag-metric"}
DATE_RE = re.compile(r"\b\d{2,4}[-/]\d{2}[-/]\d{2,4}[ T]\d{2}:\d{2}(?::\d{2})?")


# ---------------------------------------------------------------- URL parsing
def parse_context(url):
    q = parse_qs(urlparse(url).query)
    arm = unquote(q.get("var-_id", [""])[0])
    vm = arm.rstrip("/").split("/")[-1] if arm else "virtual-machine"
    frm, to = q.get("from", [""])[0], q.get("to", [""])[0]
    window = f"{frm} &rarr; {to}" if frm and to else "(time range in dashboard)"
    return {"arm": arm or "(unknown ARM id)", "vm": vm, "window": window}


# ---------------------------------------------------------------- image utils
def content_crop(im, thresh=24, pad=8, min_gap=90):
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


def prep_img(path):
    im = Image.open(path).convert("RGB")
    im = content_crop(im)
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode(), im.width


def display_width(w):
    return REPORT_W if w > REPORT_W else round(w * 0.8)


# ---------------------------------------------------------------- classification
def classify(title, text):
    t = (title or "").lower()
    body = (text or "").lower()
    if any(k in t for k in ("event", "reboot", "migration", "placement", "rca",
                            "health", "schedule", "outage", "tor", "annotation")):
        return "Event"
    if any(k in t for k in METRIC_HINT):
        return "Metric"
    if any(k in body for k in ABNORMAL):
        return "Event"
    return "Info"


def make_legend(title, text, tag):
    """Programmatic legend: title + up to two of the most abnormal / most
    informative lines from the panel text."""
    lines = [l.strip() for l in (text or "").splitlines() if l.strip()]
    lines = [l for l in lines if l.lower() != (title or "").lower()]
    picked = [l for l in lines if any(k in l.lower() for k in ABNORMAL)]
    if not picked:
        picked = lines[:2]
    picked = picked[:3]
    body = " &bull; ".join(escape(l[:180]) for l in picked)
    legend = f"<b>{escape(title or 'Panel')}</b>"
    if body:
        legend += f" &mdash; {body}"
    if tag == "Event" and "rca helper" in (title or "").lower():
        legend += (f'<br/>Customer-facing RCA messages: '
                   f'<a href="{WIKI}" target="_blank" rel="noopener">{WIKI}</a>')
    return legend


# ---------------------------------------------------------------- signals / timeline
def extract_signals(manifest):
    real = [m for m in manifest if not m.get("no_data")]
    joined = "\n".join(m.get("text", "") for m in real).lower()
    # Outage only counts from an actual Outages *data* panel (titled, timestamped)
    # — not from a section-header row that merely says "Outages impacting ...".
    outage = any("outage" in (m.get("title", "") or "").lower()
                 and DATE_RE.search(m.get("text", "") or "") for m in real)
    return {
        "reboot": "reboot" in joined,
        "live_migration": "livemigration" in joined or "live migration" in joined,
        "degraded": "degraded" in joined or "unallocatable" in joined,
        "outage": outage,
        "hw_fault": "hardware" in joined or "fault" in joined,
        "customer_initiated": "iscustomerinitiatedoperation\":true" in joined
        or "customer initiated" in joined,
    }


def build_timeline(manifest):
    """Pair timestamps with abnormal event text. Grafana renders table cells on
    separate lines, so a date cell and its description cell are usually adjacent
    lines rather than the same line: carry the most recent timestamp forward and
    attach following abnormal-looking cells to it."""
    seen, rows = set(), []
    for m in manifest:
        if m.get("no_data"):
            continue
        anchor = f"p-{m['index']:02d}"
        cur_ts = None
        for line in (m.get("text", "") or "").splitlines():
            line = line.strip()
            if not line:
                continue
            mt = DATE_RE.search(line)
            if mt:
                cur_ts = mt.group(0)
                rest = line[mt.end():].strip(" |,-\t")
                if rest and any(k in rest.lower() for k in ABNORMAL):
                    _emit(seen, rows, cur_ts, rest, anchor)
                continue
            if cur_ts and any(k in line.lower() for k in ABNORMAL):
                _emit(seen, rows, cur_ts, line, anchor)
    rows.sort(key=lambda r: r[0])
    return rows[:40]


def _emit(seen, rows, ts, desc, anchor):
    key = (ts, desc[:60].lower())
    if key in seen:
        return
    seen.add(key)
    rows.append((ts, escape(desc[:200]), anchor))


# ---------------------------------------------------------------- RCA text
def rca_blocks(ctx, sig):
    facts = []
    if sig["degraded"]:
        facts.append("a host node was reported Degraded / Unallocatable")
    if sig["live_migration"]:
        facts.append("a live migration was executed")
    if sig["reboot"]:
        facts.append("a reboot was recorded")
    if sig["outage"]:
        facts.append("a regional outage overlapped the window")
    if not facts:
        facts.append("no obvious infrastructure event was detected in the captured panels")
    fact_str = "; ".join(facts)

    if sig["reboot"] and (sig["live_migration"] or sig["degraded"]):
        hypo = ("The most likely explanation is a <b>platform-driven relocation</b>: a host "
                "health problem led the platform to live-migrate and/or reboot the VM.")
        cust_summary = ("your virtual machine was briefly restarted while the platform relocated "
                        "it to alternative hardware as an automated protective maintenance action.")
        cust_cause = ("The physical host began to show indicators of a hardware issue, so the "
                      "platform automatically moved the workload to healthy hardware; this "
                      "involved a brief restart and/or a short pause.")
    elif sig["live_migration"] or sig["degraded"]:
        hypo = ("The most likely explanation is a <b>live migration off unhealthy hardware</b> "
                "(no OS reboot recorded); the short migration freeze is the probable trigger.")
        cust_summary = ("your virtual machine was briefly paused while the platform relocated it "
                        "to alternative hardware as an automated protective maintenance action.")
        cust_cause = ("The physical host showed early indicators of a hardware issue; the platform "
                      "live-migrated the workload to healthy hardware, which involves a very short "
                      "pause while memory and state are transferred.")
    elif sig["outage"]:
        hypo = ("A <b>regional/platform outage</b> overlapped the analysis window and is the most "
                "likely contributor to the disruption.")
        cust_summary = ("your virtual machine was affected by a platform issue in the region "
                        "during the reported period.")
        cust_cause = ("A platform issue in the region overlapped the reported time; engineering is "
                      "the authoritative source for the outage scope and resolution.")
    else:
        hypo = ("No decisive infrastructure signal was found in the captured panels. Further "
                "investigation at the guest-OS / application layer is required.")
        cust_summary = ("we did not identify a platform-side cause within the captured telemetry "
                        "for the reported period.")
        cust_cause = ("No platform outage or platform-initiated reboot was identified in the "
                      "captured telemetry; further investigation of the guest operating system and "
                      "application is recommended.")

    internal = f"""
<p><b>Auto-generated from captured telemetry &mdash; validate before sending.</b> Detected signals:
{escape(fact_str)}.</p>
<p><b>Most likely hypothesis.</b> {hypo}</p>
<p><b>Customer context.</b> VM <code>{escape(ctx['vm'])}</code> &mdash; ARM id
<code>{escape(ctx['arm'])}</code>. Review the VM Details / Tags panels above for workload
sensitivity (SAP, production, SOX/regulated) as those raise the perceived impact of even short
pauses.</p>
<p><b>Suggested further investigation.</b> (1) Confirm the exact time the customer observed the
disruption and correlate with the timeline above. (2) Pull guest-OS and application/cluster logs
around the event window for fencing, failover or I/O-freeze messages. (3) If a live migration
occurred, verify whether a cluster manager (e.g. Pacemaker) reacted to the blackout. (4) Rule out
performance causes using the metric panels.</p>"""

    customer = f"""
<p><b>Summary.</b> During the reported period, {cust_summary}</p>
<p><b>Root Cause.</b> {cust_cause}</p>
<p><b>Customer Impact.</b> A brief interruption during the reported period. For most workloads this
is a short, one-off event; highly sensitive clustered or high-availability configurations may react
more visibly (for example by initiating a failover). We recommend reviewing application and cluster
logs around this time to confirm whether any such failover was triggered.</p>"""
    return internal, customer, fact_str


# ---------------------------------------------------------------- assembly
def panel_block(anchor, path, tag, legend):
    data, w = prep_img(path)
    style = f"width:{display_width(w)}px;max-width:100%;"
    return f"""
    <section class="panel" id="{anchor}">
      <span class="tag {TAG_CLASS[tag]}">{tag}</span>
      <div class="legend">{legend}</div>
      <img src="data:image/png;base64,{data}" alt="{anchor}" style="{style}"/>
    </section>"""


def build_html(url, cap_dir, manifest):
    cap_dir = Path(cap_dir)
    ctx = parse_context(url)
    sig = extract_signals(manifest)

    blocks, nodata, captured = [], [], 0
    for m in manifest:
        title = m.get("title") or f"Panel {m['index']}"
        if m.get("no_data"):
            nodata.append(escape(title))
            continue
        if not m.get("file"):
            continue
        path = cap_dir / m["file"]
        if not path.exists():
            continue
        tag = classify(title, m.get("text", ""))
        legend = make_legend(title, m.get("text", ""), tag)
        blocks.append(panel_block(f"p-{m['index']:02d}", path, tag, legend))
        captured += 1

    panels_html = "".join(blocks)
    tl = build_timeline(manifest)
    tl_rows = "".join(
        f'<tr><td class="tl-ts">{ts}</td><td>{desc}</td>'
        f'<td><a href="#{a}">view&nbsp;&rarr;</a></td></tr>' for ts, desc, a in tl
    ) or '<tr><td colspan="3">No timestamped abnormal events were extracted.</td></tr>'
    nodata_html = "".join(f"<li>{n}</li>" for n in nodata) or "<li>None</li>"
    internal, customer, fact_str = rca_blocks(ctx, sig)

    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>VM Reboot Analyzer RCA &mdash; {escape(ctx['vm'])}</title>
<style>
  :root{{--bg:#0d1117;--panel:#161b22;--line:#30363d;--fg:#e6edf3;--muted:#8b949e;
        --info:#1f6feb;--event:#a371f7;--metric:#db6d28;}}
  *{{box-sizing:border-box}}
  body{{margin:0;background:var(--bg);color:var(--fg);
       font:15px/1.55 -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif}}
  .wrap{{max-width:{REPORT_W}px;margin:0 auto;padding:32px 22px 80px}}
  h1{{font-size:22px;margin:0 0 6px}}
  h2{{font-size:18px;margin:38px 0 14px;padding-bottom:6px;border-bottom:1px solid var(--line)}}
  .head{{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:18px 20px}}
  .head .row{{display:flex;gap:10px;margin:4px 0;flex-wrap:wrap}}
  .head .k{{color:var(--muted);min-width:120px}}
  code{{background:#21262d;padding:1px 5px;border-radius:4px;font-size:12.5px;word-break:break-all}}
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
  .legend{{margin-top:8px;color:var(--fg)}} .legend a{{word-break:break-all}}
  ul{{margin:8px 0 0;padding-left:20px}} li{{margin:5px 0}}
  table{{width:100%;border-collapse:collapse;margin-top:10px;font-size:13.5px}}
  th,td{{text-align:left;padding:8px 10px;border-bottom:1px solid var(--line);vertical-align:top}}
  th{{color:var(--muted);font-weight:600}}
  .tl-ts{{white-space:nowrap;color:#79c0ff;font-variant-numeric:tabular-nums}}
  a{{color:#58a6ff;text-decoration:none}} a:hover{{text-decoration:underline}}
  .rca{{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:6px 18px 14px}}
  .rca.cust{{border-left:4px solid var(--info)}} .rca.intern{{border-left:4px solid var(--event)}}
  .dashwrap{{margin-top:40px;text-align:center}}
  a.dashlink{{display:inline-block;background:var(--info);color:#fff;font-weight:600;
             padding:11px 22px;border-radius:8px;text-decoration:none}}
  footer{{margin-top:26px;color:var(--muted);font-size:12px;text-align:center}}
</style></head><body><div class="wrap">

<h1>Virtual Machine Reboot Analyzer &mdash; RCA</h1>
<div class="head">
  <div class="row"><span class="k">ARM Id</span><code>{escape(ctx['arm'])}</code></div>
  <div class="row"><span class="k">Time range</span><span>{ctx['window']}</span></div>
  <div class="verdict"><b>Detected signals:</b> {escape(fact_str)}.</div>
</div>

<h2>Captured panels ({captured})</h2>
{panels_html}

<h2>Global summary</h2>
<p>{captured} relevant panel(s) were captured for <code>{escape(ctx['vm'])}</code>. Panels that
returned &ldquo;No data&rdquo; were skipped. Signals detected in the panel text:
{escape(fact_str)}.</p>
<p><b>Panels that returned &ldquo;No data&rdquo;:</b></p>
<ul>{nodata_html}</ul>

<h2>Timeline of findings</h2>
<table><thead><tr><th>Timestamp</th><th>Event (extracted)</th><th></th></tr></thead>
<tbody>{tl_rows}</tbody></table>

<h2>RCA candidate 1 &mdash; internal</h2>
<div class="rca intern">{internal}</div>

<h2>RCA candidate 2 &mdash; customer-facing (draft)</h2>
<div class="rca cust">{customer}</div>

<div class="dashwrap">
  <a class="dashlink" href="{escape(url)}" target="_blank" rel="noopener">
    Open full Virtual Machine Reboot Analyzer dashboard &rarr;</a>
</div>
<footer>Auto-generated from Virtual Machine Reboot Analyzer captures &middot;
{escape(ctx['vm'])}</footer>
</div></body></html>"""
