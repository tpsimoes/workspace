# Prompt — VM Reboot Analyzer RCA Report Generator

This is the consolidated prompt that generates the current solution (dashboard
scraper + self-contained HTML RCA report). It includes the base task plus every
refinement agreed during development.

---

## Role & Goal

You help understand **why a virtual machine restarted, stopped, or became
unresponsive**. Customers running sensitive workloads raise support tickets
under the category *"VM restarted or stopped unexpectedly"* whenever they notice
odd behavior (a warning, a reboot, a lock-up, a brief disruption). Many
infrastructure maintenance activities that normally go unnoticed (e.g. a Live
Migration) can still be felt by sensitive workloads — even a 1-second disruption
can trigger a cluster failover.

You are given a **Grafana "Virtual Machine Reboot Analyzer" dashboard URL**. The
VM ARM ID and the time range are encoded in the URL (the time range is also
shown at the top-right of the page). Scrape that dashboard, capture the relevant
panels as screenshots, and produce an HTML RCA report.

Input URL shape:
```
https://asw-main-c9d6bfgzgnbydnae.eus2.grafana.azure.com/d/tictrm7/virtual-machine-reboot-analyzer?orgId=1&from=<ISO>&to=<ISO>&timezone=utc&var-_id=<url-encoded ARM ID>
```

---

## Capture Engine (`enumerate_all.py`)

- Drive the dashboard with **Playwright + Microsoft Edge** (`channel="msedge"`,
  persistent profile `.pw-profile-msedge`, `no_viewport=True`). Conditional
  Access requires Edge with a cached, authenticated profile. Retry once on a
  flaky `TargetClosedError` at launch.
- Each panel is a `div.react-grid-item`. **Grafana returns panels in a different
  order on every scrape** — never rely on panel index; always resolve captures
  by title-slug.
- **Wait for each panel to finish loading** (up to ~3 minutes). A panel is
  loaded when it shows data **or** the text **"No Data"**. If it shows neither,
  it errored — it will have a small red icon in its top-left corner; remember it
  for the report.
- **Expand tall tables** before capture so all rows/columns are shown (not the
  clipped scroll viewport). Use explicit pixel heights (`height = scrollHeight`);
  never `height:auto` (it collapses the grid item to 0).
- **De-stick table headers**: when a scroll container is expanded, a
  `position:sticky` header drifts (behind the toolbar or to the bottom). Force
  every `sticky` descendant to `position:static` so the header renders at the
  top of the table and is captured with its columns.
- **Hide page chrome during the element screenshot** so the fixed Grafana
  toolbar (star / Copilot / info / Edit / Export / Share) and top nav don't bleed
  into a tall panel's capture: hide every `fixed`/`absolute`/`sticky` element and
  every `header`/`nav`/`[role=banner]` that is **not** inside a
  `div.react-grid-item` (`display:none` for out-of-flow, `visibility:hidden` for
  sticky). Restore afterwards in a `finally`.
- Autocrop each PNG. Write a `manifest.json` (index, title, `no_data`, text,
  file) alongside `panel-NN-<slug>.png`.

---

## Report Generator (`build_report_reboot.py`)

Read the captured PNGs, resolve each by title-slug, tighten each image to just
its content band, and emit **one self-contained HTML report** (dark theme,
base64-embedded images, content width 1080px).

### Header (top of report)
State the **VM ARM ID**, the **date range analyzed**, and the **customer name**.

### Image handling
- **Content-crop**: keep the title (top-left aligned) and the populated
  rows/graph; drop trailing blank area and any detached footer. A row counts as
  content only if it has several above-threshold pixels (so a lone 1-px table
  border in an empty region is not mistaken for content). Do **not** include
  blank area — if a panel is tall but only one row shows, capture only the
  portion with data.
- **Sizing**: if the cropped image is **wider** than the report content width,
  scale it down proportionally to fit; otherwise show it at **80%** of natural
  size. **Never enlarge.**
- **Full GUIDs everywhere**: whenever any UID is mentioned (VM Id, Node Id,
  Container Id, etc.), always use the **full** GUID, never the 8-char prefix.
  Source the full GUIDs from the **VM Placement** panel
  (e.g. `01ea29c8` → `01ea29c8-4e86-cb82-9ce0-6ed35c673d5b`).

### Screenshots — order, relevance rules, and tags
Place captured screenshots in **this order**. Tag each **Info**, **Event**, or
**Metric**. Give each a short legend explaining only *why it was captured / what
it shows* — no text that repeats the screenshot. If a scrollable panel couldn't
show everything, say so (without adding other text).

General relevance rules:
- Informational panels (IDs, features) → always relevant (context).
- Event-list panels → almost always relevant; if very long, focus on lines with
  abnormal words (error, fail, failure, degraded, impact, freeze…).
- Graph panels → relevant if values are constantly at/near max, or show
  spikes/blips/abnormal patterns.
- **A panel reading "No Data" is never relevant — never capture it**, even where
  a panel is marked "capture always".

Panels (with capture criteria):
1. **VM Events** — overall impact counters. Capture when any counter > 0.
2. **Virtual Machine – Current Info** — VM/container/node IDs + customer name. Capture always.
3. **VM Details (Features)** — SKU/features; a SAP image implies a sensitive workload. Capture always.
4. **OS Image Details** — Linux vs Windows, OS type. Capture always.
5. **Installed Extensions** — extensions on the VM. Capture always.
6. **VM Tags** — customer tags; infer workload & criticality (words like prd/prod/production, SOX, regulated, data classification, application name). Capture always. Show the `Name`/`Value` column headers.
7. **Outages** — outages impacting VMs in the region. Capture always (unless No Data).
8. **CPU & Memory** (CPU%, % Memory Pressure, RAM size/available) — Metric. Capture only on constant-high values, spikes, blips, or abnormal patterns.
9. **VM Placement** — every placement of this VM. 1 line with a `Container creation` before the window = normal; 2+ lines = the VM moved nodes (disruption). Capture always. (Source of full GUIDs.)
10. **Node and TOR Placement (<60 days)** — which TOR a node sits in. 1 old line = normal. Capture always.
11. **RCA Helper: Node Events and Errors** — infrastructure events tied to the VM. Lines mentioning the VM or container ID are top-relevance; node-ID lines are relevant only if the VM was on that node at that timestamp (check placements; an 8-char node prefix still matches). Reveals node degradation/unallocatable, live migrations, storage issues, etc. Capture always. **Include the wiki link from the panel title in the legend** (`https://supportability.visualstudio.com/AzureIaaSVM/_wiki/wikis/AzureIaaSVM/500161/RCAs`).
12. **Reboots & Scheduled Events** section — all relevant when they contain data:
    - **Scheduled Events & Reboots** — timeline: event duration (yellow/orange bar) + reboots (red dots). Capture always.
    - **Reboot Detail** — when/why/how long a reboot happened. Capture always.
    - **Scheduled Events Detail** — event type, timing, expected impact. Capture always.
    - **Live Migration Events** — live migration details. Capture always. Show the column headers (`EventTime, EventType, ASW_Wiki, FailureReason, RCALevel1, RCALevel2, message, Diagnostics, ASI Link`).
    - **VM Health Annotations** — internal controller labels applied to the VM. Capture always.
13. **Disk Metrics** section (queue length, latency, bandwidth %, IOPS %) — Metric. Capture on sustained-high values, spikes, blips, or odd patterns.

### Global summary
After the screenshots: summarize findings; state what wasn't found (which panels
read "No Data"), which panels were discarded as not relevant, and whether any
panel showed an error (red icon).

### Timeline
Build a timeline of each documented finding: timestamp, type, description. Use
HTML anchors so clicking a timeline entry jumps to the supporting screenshot.

### Two RCA candidates
The analysis exists because a customer raised *"VM restarted or stopped
unexpectedly."*

1. **Internal RCA** — the most logical/likely explanation; detailed; include
   customer context where possible; suggest what else to investigate.

2. **Customer-facing RCA** — formal tone; avoid sounding definitive except for
   facts; present correlations/assumptions as such; **no internal system
   details/IDs**; avoid assumptions from customer context (only obvious tags).
   Short paragraphs: **Summary, Root Cause, Resolution, Customer Impact** (skip
   Resolution when not applicable / unknown).

### Interpretation aids (typical scenarios)

**If there is a reboot:**
- Severe infrastructure failure or outage (see Reboot Detail hints).
- Reboot as part of a Live Migration (rare, but happens).
- OS-level/workload crash (high CPU/mem/disk/IOPS, or an infra event that
  snowballed if timestamps overlap perfectly).
- Customer-initiated — but note orchestrated clusters (e.g. Pacemaker) can fence
  a VM over even a brief blip; a live-migration-adjacent "customer initiated"
  reboot (fencing acts on the customer's behalf) is a good indicator (common with
  SAP).
- Not enough info: nothing abnormal in metrics and no infra event → Reboot
  Detail is the best clue; "customer initiated" needs further investigation
  (fencing? OS logs?).

**No reboot (VM stopped / became unresponsive):**
- Outage disrupted stability → state the time ranges.
- Performance (high CPU/mem, long disk queues, IOPS overload) → state ranges.
- Platform issues (storage/compute/TOR/network) → state ranges.
- Live migration blackout — generally tolerated, but large-memory / sensitive
  workloads can snowball.
- Maintenance activities (repairs, etc.) → state ranges.
- Not enough info → investigate OS / application / external dependencies.

---

## Run

```powershell
python enumerate_all.py "<dashboard URL>" "captures\<vm>"
python build_report_reboot.py          # writes report_<vm>.html
Start-Process report_<vm>.html
```
