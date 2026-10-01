---
name: vm-reboot-analyzer
description: >-
  Scrape an Azure Managed Grafana "Virtual Machine Reboot Analyzer" dashboard and
  produce a self-contained HTML RCA report explaining why a VM restarted, stopped,
  or became unresponsive. Captures the relevant panels as screenshots, builds a
  findings summary, a clickable timeline, and two RCA candidates (internal +
  customer-facing). WHEN: "why did my VM reboot", "VM restarted unexpectedly",
  "VM stopped / became unresponsive", "analyze reboot analyzer dashboard",
  "generate RCA for VM", "scrape Grafana VM dashboard", "reboot analyzer report",
  "live migration impact", "VM reboot root cause". Also exposed as a container
  service (POST a dashboard URL → async HTML report).
license: Internal use — Azure IaaS VM support.
---

# VM Reboot Analyzer

Understand **why a virtual machine restarted, stopped, or became unresponsive**
and produce a customer-ready RCA. Customers on sensitive workloads (e.g. SAP,
Pacemaker-clustered) raise tickets under *"VM restarted or stopped unexpectedly"*
whenever they notice odd behavior — even a 1-second infrastructure blip (such as
a Live Migration) can trigger a cluster failover.

## When to use this skill

Use it when the user provides a **Grafana "Virtual Machine Reboot Analyzer"
dashboard URL** (the VM ARM ID and time range are encoded in the URL) and wants
an analysis / RCA, or asks any reboot/outage/live-migration root-cause question
about an Azure VM. Input URL shape:

```
https://<stamp>.grafana.azure.com/d/tictrm7/virtual-machine-reboot-analyzer?orgId=1&from=<ISO>&to=<ISO>&timezone=utc&var-_id=<url-encoded ARM ID>
```

## Workflow

1. **Prepare and open once** — read the capture/report requirements and check
   local dependencies before launching a browser. Reuse an existing authorized
   Grafana session when available; otherwise open one persistent Edge context
   and one dashboard tab. Complete any required sign-in in that tab.
2. **Capture** — scrape the dashboard in that same context and tab, waiting for every panel to finish loading
   (up to ~3 min; a panel is loaded when it shows data *or* the text "No Data").
   Expand tall tables, de-stick headers, hide Grafana chrome, autocrop, and write
   `manifest.json` + `panel-NN-<slug>.png`. Verify table rows, column extents,
   headers, and absence of overlapping panels before ending capture. Perform
   any inspection, retry, or recapture in the existing tab, not a new browser.
   If a loaded panel explicitly shows **No Data**, record `status: no_data`,
   `no_data: true`, and `file: null`, then continue with the remaining panels.
   Do not capture, retry, reopen Grafana, or request authentication for that
   panel. No Data alone must not block report generation; list skipped panels
   in the global summary instead. A generic "Panel status" badge does not
   override an explicit No Data result, but actual query errors, timeouts,
   and unstable captures must still be reported as failures.
   See `PROMPT.md` § Capture Engine.
3. **Analyze & report** — resolve each PNG by title-slug, content-crop to the
   data band, and emit **one self-contained HTML report** (dark theme, base64
   images, 1080px content). See `PROMPT.md` § Report Generator for header, panel
   order, relevance rules, tags, summary, timeline, and the two RCA candidates.
   Build and validate the report locally from saved evidence; do not reopen
   Grafana for report generation or validation.
4. **Deliver** — return a link to `report_<vm>.html`; do not open it unless
   the user requests a preview. Close only the browser
   context created for this run, after all evidence checks and recaptures finish;
   leave a reused user-owned browser session open.

### Single-session policy (mandatory)

This section is the authentication/session policy for every workflow step,
helper script, and referenced prompt. The target is **one Grafana browser opening and at most one interactive
sign-in for the entire analysis**, not one per command or panel.

- Use one persistent Edge context with `.pw-profile-msedge` and one dashboard
  tab. Navigate to the requested Grafana URL once; reuse the live context and
  page for subsequent work. A cached profile is not a substitute for keeping
  the same browser session alive.
- Use the existing `enumerate_all.py` entry point rather than generating
  ad-hoc capture or inspection scripts for each analysis. It waits for stable
  rendered content, expands and validates tables, checks screenshots against
  extracted text, and retries failed panels once within the same session.
- Keep capture, validation, and corrective recapture in that one process.
  The entry point closes its own context only after validation completes or
  the run stops with an explicit error. A failure is not permission to rerun
  it automatically. For an already-authorized caller-owned Playwright context,
  use `capture_in_context(context, url, out_dir)`; it does not launch or close
  a browser. Do not launch separate processes for inspection or recapture.
- Do not start additional Azure CLI, Azure MCP, or other sign-in flows solely
  as preliminary checks for this dashboard-report workflow. Use dashboard
  evidence and existing authorized connections; report unavailable optional
  corroboration without repeatedly prompting for authentication.
- Do not use GitHub tools, GitHub API calls, or remote repository reads for
  this local Grafana workflow. Read the local skill, helpers, and saved evidence
  directly; do not request GitHub authentication or probe GitHub access.
- Do not switch between browser automation tools or browser profiles. Such
  switches can create separate sessions and new authorization prompts. Keep
  all Grafana work in the original Edge context and tab.
- Validate generated HTML and images locally. Do not open a separate browser
  tool session or request browser authorization just to preview the report;
  returning the verified local report link is sufficient.
- If authentication is required, ask the user once to complete it in the
  existing dashboard tab, then continue there. Never create another browser
  or login tab as an authentication retry.
- If Conditional Access, session expiry, or a browser failure makes reuse
  impossible, stop and explain the blocker before requesting another sign-in
  or opening a replacement browser. Do not bypass authentication controls or
  enter a repeated login/relaunch loop.

### Authentication versus tool approvals

GitHub authorization, Grafana/Entra sign-in, and command/browser-tool approval
prompts are different. This workflow does not need GitHub authorization.
Grafana sign-in is needed only when the reused session or cached profile is
not accepted. Tool approvals may still be required by the host application;
do not promise to suppress them or bypass them. Minimize unnecessary calls by
using the stable capture entry point and local report generation.

### Run (local, Playwright + Edge)

```powershell
python enumerate_all.py "<dashboard URL>" "captures\<vm>"
```

Run once. Exit code 0 means every panel was validated as data or No Data.
Exit code 1 means capture/session validation failed: inspect the error and any
partial `manifest.json`, and do not automatically open another session.
The manifest retains `index`, `title`, `text`, `no_data`, and `file`, and adds
`rows`, `status` (`data`, `no_data`, or `error`), and an error message on failure.
No Data/error entries have no screenshot. Existing unrelated output files are
not deleted; use only files referenced by the successful run's manifest.

Generate and validate the HTML locally from that manifest and its images, then
return the report link. `build_report_reboot.py` is a VM-specific example, not a
generic command: do not execute it unchanged for another VM. Report generation
must not launch Grafana, request GitHub access, or initiate another login.

### Run (container service, HTTPS on 443)

POST the dashboard URL; the server replies immediately with a preemptive
download URL and generates the report asynchronously:

```bash
docker build -t vmrca container/
docker run -p 443:443 -e PUBLIC_BASE_URL=https://myhost \
  -e GRAFANA_COOKIES="$(cat cookies.json)" vmrca
curl -k -X POST https://localhost/ -d '<dashboard URL>'
# → "Your report will soon be available at https://myhost/reports/<random>.html"
```

## Core rules (always apply)

- **Never rely on panel index** — Grafana returns panels in a different order on
  every scrape. Always resolve by title-slug.
- **"No Data" is never relevant** — never capture it, even for panels marked
  "capture always". Once loading finishes, record it as `no_data` and continue
  without a screenshot or retry; it must not fail the run. A generic
  "Panel status" badge alongside "No Data" is not a query failure. Explicit
  query errors and panels that have not finished loading are not No Data.
- **Full GUIDs everywhere** — whenever a VM / Node / Container ID is mentioned,
  use the complete GUID, never the 8-char prefix. Source full GUIDs from the
  **VM Placement** panel (e.g. `01ea29c8` → `01ea29c8-4e86-cb82-9ce0-6ed35c673d5b`).
- **No internal IDs in the customer-facing RCA**; present correlations and
  assumptions as such, state facts as facts.
- **Capture only the data band** — never pad a screenshot with blank panel area
  (blank area is allowed only to avoid including the Grafana overlay/toolbar).
- A panel that shows neither data nor "No Data" **errored** (red icon, top-left)
  — note it in the report summary.

## Panel order, relevance & tags

Place screenshots in this exact order; tag each **Info**, **Event**, or
**Metric**; give each a short legend saying only *why captured / what it shows*.

1. **VM Events** (Event) — capture when any counter > 0.
2. **Virtual Machine – Current Info** (Info) — IDs + customer name. Always.
3. **VM Details (Features)** (Info) — SAP image ⇒ sensitive workload. Always.
4. **OS Image Details** (Info) — Linux vs Windows. Always.
5. **Installed Extensions** (Info) — Always.
6. **VM Tags** (Info) — infer criticality (prd/prod/production, SOX, app name).
   Always; show `Name`/`Value` headers.
7. **Outages** (Event) — regional VM outages. Always, unless No Data.
8. **CPU & Memory** (Metric) — only on constant-high / spikes / blips / abnormal.
9. **VM Placement** (Info) — 2+ lines = VM moved nodes (disruption). Always.
   Source of full GUIDs.
10. **Node and TOR Placement (<60 days)** (Info) — Always.
11. **RCA Helper: Node Events and Errors** (Event) — infra events tied to the VM;
    node-ID lines relevant only if the VM was on that node at that timestamp.
    Always; include the wiki link
    `https://supportability.visualstudio.com/AzureIaaSVM/_wiki/wikis/AzureIaaSVM/500161/RCAs`
    in the legend.
12. **Reboots & Scheduled Events** (all Event, when they contain data):
    Scheduled Events & Reboots; Reboot Detail; Scheduled Events Detail; Live
    Migration Events (show headers: `EventTime, EventType, ASW_Wiki,
    FailureReason, RCALevel1, RCALevel2, message, Diagnostics, ASI Link`); VM
    Health Annotations. All "capture always".
13. **Disk Metrics** (Metric) — queue length, latency, bandwidth %, IOPS %;
    capture on sustained-high / spikes / blips / odd patterns.

## Report deliverables

- **Header**: VM ARM ID, date range analyzed, customer name.
- **Screenshots**: ordered as above, content-cropped, ≤1080px (scale down to fit,
  else 80% of natural size, never enlarge), each with its Info/Event/Metric tag
  and legend.
- **Global summary**: findings; which panels read "No Data"; which were discarded
  as not relevant; which errored.
- **Timeline**: timestamp, type, description — with HTML anchors jumping to the
  supporting screenshot.
- **Two RCA candidates**: Internal (detailed, most-likely hypothesis + what else
  to investigate) and Customer-facing (formal; Summary, Root Cause, Resolution,
  Customer Impact — skip Resolution when not applicable).

## Interpretation aids

**If there is a reboot**: severe infra failure/outage (Reboot Detail hints);
reboot as part of a Live Migration (rare); OS/workload crash (high
CPU/mem/disk/IOPS, or an infra event that snowballed on overlapping timestamps);
customer-initiated — but orchestrated clusters (Pacemaker) can **fence** a VM over
a brief blip, so a live-migration-adjacent "customer initiated" reboot is a strong
indicator (common with SAP); otherwise Reboot Detail is the best clue.

**No reboot (stopped / unresponsive)**: outage, performance overload, platform
(storage/compute/TOR/network) issues, live-migration blackout (worse for
large-memory/sensitive workloads), or other maintenance — **state the time
ranges** for each so the engineer can correlate with what the customer reports.

## Reference files

- `PROMPT.md` — capture/report specification. Authentication and browser
  lifecycle follow the single-session policy in this file.
- `enumerate_all.py` — Playwright + Edge capture engine.
- `build_report_reboot.py` — self-contained HTML report generator.
- `container/` — Dockerfile + HTTPS service (POST URL → async HTML report);
  `container/app/scrape.py` (Selenium/Chromium port), `report.py`, `server.py`.

## Authentication

Azure Managed Grafana is behind Conditional Access. Local runs use Edge with a
cached authenticated profile (`.pw-profile-msedge`) and must follow the
single-session policy above. Reuse cached authentication without prompting
when valid; otherwise complete sign-in once in the existing dashboard tab.
Conditional Access may require reauthentication, so a single sign-in is a
workflow target, not a guarantee that overrides tenant policy.

Do not export, print, or copy browser tokens/cookies to avoid a sign-in prompt.
The container needs
`GRAFANA_COOKIES` (JSON cookie array) — without it the scraper only reaches the
login page. Use only an explicitly configured, authorized container credential
source; do not switch to the container as an authentication workaround.
