---
name: review-reporter
description: "Prepare report content for Monthly Review Meetings: collect KPI data (CSAT, IR, Case Volume, Day to Close), organize highlights/lowlights, Customer Support Stories, and Executive Escalation summaries. Trigger when users mention “monthly review,” “monthly report,” “KPI,” “CSAT,” “highlight lowlight,” “executive escalation,” or “reporting to leadership.” Also supports RCA Standardization Reports, manager/directs DTC comparisons, anonymized engineer comparisons, top support paths, and top customers."
---

# Skill: Review Reporter

## Report options and request routing

Offer these options when the user requests a report without specifying its type:

| Option | Purpose | Workflow |
|--------|---------|----------|
| Monthly Review / MOR | Monthly KPI summary, highlights/lowlights, support stories, and escalations | Monthly Review structure and dashboard collection workflow below |
| CPE Insight | Survey cases, CSAT, and customer verbatim | CPE Insight section |
| IR Missing Insight | Initial-response missed cases | IR Missing Insight section |
| SE Members Performance | Engineer case-performance metrics | SE Members Performance section |
| US / Costa Rica Engineer KPI Comparison | Country/cohort and fiscal-year comparison with engineer drill-down | US / Costa Rica comparison sections |
| **RCA Standardization Report** | Manager/directs support-path and customer analysis, anonymized engineer DTC comparison, and aggregated manager comparison for `All` | [RCA Standardization Report](#rca-standardization-report) |

- If the user already names a report, select it directly; do not ask them to choose again.
- Route requests for "RCA report", "RCA standardization", manager/directs DTC comparisons, or redacted engineer support-path comparisons to **RCA Standardization Report**.
- RCA Standardization is a standalone report option, not a required MOR tab. Use its existing local HTML/JS/KQL refresh workflow; do not collect unrelated MOR dashboard or Cowork data.
- For RCA requests, use the ASW Engineers roster and manager dropdown, including `All`. Preserve the documented redaction, weighted aggregation, collapsed sections, sorting, source DFM links, and `.xlsx` exports.
- Confirm the reporting period if it is unspecified. The existing implementation is FY27 YTD; do not relabel that snapshot as another fiscal year without updating the query, date range, and output metadata.

## Report Structure

The Monthly Review report contains the following sections:

### 1. KPI Dashboard Summary

> **Execution order**: (1) Validate filters → (2) Wait for data refresh → (3) Extract data. Complete all three steps in order; do not skip any. If the dashboard is inaccessible, notify the user and ask whether to use the last exported data.

Metrics to collect:

| KPI | Description | Source |
|-----|------|------|
| CSAT | Customer satisfaction score | Survey Dashboard |
| IR (Initial Response) | Initial response time | Case Management System |
| Case Volume | Case count (open / closed / in progress) | Case Management System |
| Day to Close | Average number of days to close | Case Management System |
| Backlog | Number of pending cases | Case Management System |

Output format: table + monthly trend (compared with the previous month ↑↓)

### 2. Highlight / Lowlight

**Highlights** (this month's achievements):
- Successful resolution of a major customer issue
- Outstanding performance by team members
- Process improvement results
- Successful cross-team collaboration

**Lowlights** (items requiring attention):
- KPIs that missed their targets and analysis of the reasons
- Staffing / resource bottlenecks
- Obstacles that require leadership assistance to remove

### 3. Customer Support Story

- Select 1–2 of the month's most representative support cases
- Structure: issue context → challenge → action → outcome → customer feedback

### 4. Executive Escalation

If there was an Executive Escalation this month, report it separately:
- Case summary (customer, issue, and scope of impact)
- Current status / resolution
- Lessons Learned

---

## Dashboard Data Collection Guidelines

### Data Acquisition Methods (Method Selection)

MOR data sources use different acquisition methods, with clearly defined responsibilities:

| # | Data source | Purpose | Acquisition method | Executor |
|---|--------|------|---------|--------|
| 1 | **Commercial Insights+ V2 Semantic Model** | 19 KPIs (Dashboard 1: Quality + Operational Metrics) | Cowork `asw-team-kpi-monthly` skill runs DAX through Fabric AI Hub MCP | **Cowork** |
| 2 | **Commercial Insights+ V2** (IR Missed subset) | IR Missing case details (including Time to IR, Verbatim, SE Manager) | IR Missed pattern in Cowork `asw-team-kpi-monthly` skill | **Cowork** |
| 3 | **OpEx Overall PCY Level A&I+DTP** (Power BI msit) | 5 OpEx metrics (Case Assignment / Backlog) | Playwright + external Edge (this SKILL, Step 1B) | **This Agent** |
| 4 | **Kusto — CPE Survey** | CPE Insight data (CSAT, Verbatim, AgentName) | Kusto MCP (`mcp_kusto_kusto_query`) | **This Agent** |

> **Why Dashboard 1 / IR Missing are assigned to Cowork**: The `Commercial Insights+ V2 Dataset` is in the `CESBIDataset_Commercial_PROD` workspace, where the personal `az login` identity (`jacobw@microsoft.com`) currently lacks Build permission. Direct calls to the Power BI REST API `executeQueries` return `PowerBIEntityNotFound`. Cowork's `pbi_fabricaihub` MCP uses a privileged service principal and can read across tenants; execution takes 30–60 seconds (compared with 10–15 minutes using Playwright). If personal Build permission is granted in the future, or VS Code Copilot gains access to Fabric AI Hub MCP, consider moving Cowork's role back to this Agent.

---

### Method A: Cowork Data Import (Dashboard 1 + IR Missing)

**Procedure** (preparation before each MOR):

1. In Cowork, run the following two commands (performed by the user):
   ```
   Cowork > Run asw-team-kpi-monthly for FY<current>, export KPI by Month
   Cowork > Run asw-team-kpi-monthly for FY<current>, export IR Missed cases
   ```
2. The user **copies** the `.xlsx` files produced by Cowork and any corresponding `.json` files **to** `C:\GitHubCopilot\IronMan\Output\Cowork\`
3. This Agent reads the latest files in that folder and assembles the report; **there is no need to reopen Dashboard 1 / IR Missed Reasons Dashboard**

**File Placement Contract (Cowork Intake Contract)**:

| Filename (Glob) | Contents | Read method |
|--------------|------|---------|
| `Output/Cowork/asw_kpi_by_month_FY*.xlsx` | One sheet, `KPI by Month`, with 19 KPI columns and one row per FM | `openpyxl` / `pandas.read_excel` |
| `Output/Cowork/asw_kpi_by_month_FY*.json` (optional) | Raw output from the Cowork DAX runner (`meta` + `rows`) | `json.load` |
| `Output/Cowork/asw_ir_missed_FY*.xlsx` | 4 sheets: `FY<NN> IR Missed`, `By Customer`, `By Owner`, `By Severity` | `openpyxl` / `pandas.read_excel` |
| `Output/Cowork/asw_ir_missed_FY*.json` (optional) | Three-query merged JSON (dims + verbatim + owner_manager map) | `json.load` |

**File selection rule**: If multiple timestamped versions exist for the same FY, **select the filename that sorts last lexicographically** (Cowork filenames typically include `_YYYYMMDD`). If both an xlsx and json exist, prefer the xlsx (Cowork standardizes the column semantics).

**Sheet / Column Mapping**:

*`KPI by Month` sheet* → Maps directly to the “Dashboard 1 — Quality Metrics table” + “Operational Metrics table” in this SKILL. Column order and names are defined in the Cowork skill (see the 19-KPI table in Cowork `asw-team-kpi-monthly` SKILL); this Agent does not need to remap them. Read from Jul in the current FY through the latest month with data.

*`FY<NN> IR Missed` sheet* (12 columns): `SR ID | Customer | Service | SR Owner | SE Manager | Initial Severity | Region | Created Date | Closed Date | Time to IR (mins) | CSAT | Verbatim`

| HTML field in SKILL | Cowork field | Notes |
|-------------------|-------------|------|
| Case ID | `SR ID` | Store the 16-digit value as TEXT |
| Customer | `Customer` | Already the Top Parent Organization Name |
| Service | `Service` | Service Offering Master name |
| SE Manager | `SE Manager` | Cowork has resolved the owner alias to the manager email |
| Created | `Created Date` | Display as `yyyy-mm-dd` |
| Closed | `Closed Date` | Same as above |
| Initial Severity | `Initial Severity` | `A`/`B`/`C` (Sev A in bold red) |
| TTMS (mins) | `Time to IR (mins)` | **Semantic note**: total minutes, not over-SLA; append `data as reported by Power BI` when displaying |
| Region | `Region` | Customer Region |

> **Important semantic note**: Cowork's `Time to IR (mins)` has the same meaning as the `TTMS` field used by the original SKILL (Time To Meet SLA in minutes), but the Semantic Model has no SLA target data. Therefore, this value **is the raw IR time in minutes, not the number of minutes over SLA**. Add this note to the IR Missing Insight page footer: `Time to IR reflects total minutes to initial response; SLA overage cannot be computed from the source model.`

**Fallback conditions**:

Switch to Method B (Playwright) if any of the following occurs:

1. `Output/Cowork/asw_kpi_by_month_FY*.xlsx` is missing or more than 30 days old
2. The Cowork file exists but is missing KPI columns (for example, a new KPI was not synchronized or a column name does not match)
3. The user requests that data be pulled again from the dashboard

---

### Method B (Fallback): Playwright + CES BI Hub

> **When to use**: When Cowork data is unavailable. Perform all filter validation, iframe operations, and two-minute waits below **only when using Method B**; when using Method A, **skip them entirely**.

### Dashboard 1: CSS - A&I and DTP (Playwright)

| Item | Details |
|------|------|
| **Name** | CSS - A&I and DTP |
| **Platform** | CES BI Hub |
| **URL** | https://cesbihub.microsoft.com/User/groups/10/report/81538463-21f0-45bc-8f08-71d5dc9ccc48/0/0?reportTab=ReportSectiond24dca6cf2e742181ba9 |
| **Required filter** | Channel Function Detail = **ASW_SAPEpicEsc** (see the Filter Validation Checklist below) |
| **Refresh wait** | After selecting the filter, wait **2 minutes** before extracting data |

#### Filter Validation Checklist (required each time; follow the order below exactly)

> **📅 Current Fiscal Year**: Determine dynamically based on the report run date. If the date is **on or after July 1**, the next Microsoft Fiscal Year has begun. For example, for MOR runs after 2026/7/1, the current fiscal year is **FY2027** (Jul 2026 – Jun 2027).
>
> Microsoft fiscal-year rule: The FY starts on **July 1** each year and ends on June 30 of the following year. The fiscal-year number is the ending year (for example, FY2027 = 2026/7/1 – 2027/6/30). **Starting each July 1, switch the MOR `Time Fiscal Year` filter to the new fiscal year**. Therefore, starting 2026/7/1, select **FY2027**; do not keep FY2026 or include both FYs.

After opening Dashboard 1, complete the following four validations **in order**:

1. ✅ **Channel Function Detail** → shows `is ASW_SAPEpicEsc`
2. ✅ **Time LastTwelveMonths** → shows `is (All)` (no checkboxes selected)
3. ✅ **Time LastSixMonths** → shows `is (All)` (no checkboxes selected)
4. ✅ **Time Fiscal Year** → shows `is FY2027` (current FY only; must not include FY2026)

If any item does not match, correct it and wait 2 minutes before extracting data.

#### Collect KPI List (19 items)

| # | KPI | Table location | Target | Direction |
|---|-----|---------|--------|----------|
| 1 | CSAT 5 * Avg | Key Metrics by Date (upper table) | ≥ 4.8 | High Good |
| 2 | DSAT | Key Metrics by Date (upper table) | < 2% | Low Good |
| 3 | CSAT Surveys | Key Metrics by Date (upper table) | - | - |
| 4 | CSAT Response Rate | Key Metrics by Date (upper table) | - | - |
| 5 | % CritSit | Key Metrics by Date (upper table) | - | - |
| 6 | % IR Met | Key Metrics by Date (upper table) | ≥ 99% | High Good |
| 7 | IPD Created | Key Metrics by Date (lower table) | vs Total | High Good |
| 8 | IPD Closed | Key Metrics by Date (lower table) | - | - |
| 9 | Open Cases | Key Metrics by Date (lower table) | - | - |
| 10 | Created Cases | Key Metrics by Date (lower table) | - | - |
| 11 | Closed Cases | Key Metrics by Date (lower table) | - | - |
| 12 | CSS TMPI | Key Metrics by Date (lower table) | - | - |
| 13 | Avg DTC | Key Metrics by Date (lower table) | ≤ 12 days | Low Good |
| 14 | Backlog Count | Key Metrics by Date (lower table) | - | - |
| 15 | Backlog DtC | Key Metrics by Date (lower table) | - | - |
| 16 | Collaboration Tasks | Key Metrics by Date (lower table) | - | - |
| 17 | Post IR Transfer % | Key Metrics by Date (lower table) | - | - |
| 18 | % Transfer | Key Metrics by Date (lower table) | - | - |
| 19 | % SR Closed in less than 7 Days | Key Metrics by Date (lower table) | ≥ 50% | High Good |

#### Procedure

> **🚨 CRITICAL — Filter setup is a BLOCKING step: complete all four validations before extracting any data.**

1. Open the URL (the bookmark includes some filter settings)
2. Wait for the PBI iframe to finish loading (until `[role="grid"]` appears)
3. **[BLOCKING] Run the Filter Validation Checklist in order; all four checks must pass before continuing:**

   **Step 3a — Channel Function Detail**
   - Confirm the restatement shows `is ASW_SAPEpicEsc`
   - If not, expand the Filter Card restatement and select `ASW_SAPEpicEsc`

   **Step 3b — Time LastTwelveMonths**
   - Confirm the restatement shows `is (All)`
   - If not, click the Clear filter button (`[aria-label="Clear filter"]`) to clear it

   **Step 3c — Time LastSixMonths**
   - Confirm the restatement shows `is (All)`
   - If not, click the Clear filter button (`[aria-label="Clear filter"]`) to clear it

   **Step 3d — Time Fiscal Year (⚠️ the bookmark may default to `FY 2027 or FY 2026`; correct it manually)**
   - Confirm the restatement shows **only** `is FY2027` (must not include FY2026)
   - After the bookmark loads, the restatement is usually `is FY 2027 or FY 2026`; **this does not pass validation**
   - **Correction steps**:
     1. Click Clear filter (eraser button `[aria-label="Clear filter"]`) to clear the current selection
     2. Click the expand button for the `Time Fiscal Year` filter card (`aria-label="Time Fiscal Year Expand or collapse filter card"`) to expand that Filter Card
     3. In the expanded checkbox list, select `FY 2027` (confirm `aria-checked="true"`)
     4. Confirm that `FY 2026` is not selected (if visible, confirm `aria-checked="false"`)
   - **Validation**: the restatement becomes `is FY2027` (without `or FY 2026`)

4. **[BLOCKING] After changing filters, wait 2 minutes (120 seconds)** for the data refresh to complete
   - Use `page.waitForTimeout(120000)` or an equivalent method
   - **Do not extract any data during the wait**
5. Extract the **full FY data** from both “Key Metrics by Date” tables in the Power BI iframe
6. Collect all values and the Total for each KPI from FM Jul through the current month
   - Microsoft's Fiscal Year runs Jul–Jun (FY 2027 = FM Jul 2026 through FM Jun 2027)
   - If the fiscal year is not yet complete, data extends only through the current month (for example, in July 2026 there is only Jul, one month; in May 2027 there are Jul–May, 11 months)
   - Total is the cumulative value for the available months, not a full 12 months
   - **The Total column is the FY2027 YTD value** (because only FY2027 is selected in the filter, Total = current fiscal-year cumulative value)

---

### Dashboard 2: OpEx Overall PCY Level

| Item | Details |
|------|------|
| **Name** | OpEx Overall PCY Level A&I+DTP |
| **Platform** | Power BI (msit.powerbi.com) |
| **URL** | https://msit.powerbi.com/groups/me/reports/97cef847-3bf0-445c-b4b6-5e4f7e29fc8d/238752830e2a8090a3ca?experience=power-bi |
| **Required filter** | Select **A&I-Azure-ASW Epic and SAP** as the only Staff Group (do not select multiple groups) |
| **Refresh wait** | After confirming the filter, wait **2 minutes** before extracting data |
| **Note** | This dashboard defaults to showing only the previous six months; no additional time filter is needed |

#### KPI List to Collect (5 items from the Metric Trend View table)

| # | KPI | Category | Target |
|---|-----|----------|--------|
| 1 | % Hours out of Queue (WFM + VDM) | Case Assignment | ≤ 4.0% (Low Good) |
| 2 | Accept Rate (WFM + VDM) | Case Assignment | ≥ 1.8 (High Good) |
| 3 | % Case Assignment >= 1 | Case Assignment | ≥ 85.0% (High Good) |
| 4 | Quick Ownership Change % (0-15 Mins) | Case Assignment | ≤ 2.0% (Low Good) |
| 5 | % Cases Closed within 7 days | Backlog Management | ≥ 50.0% |

#### Procedure

1. Open the URL
2. If an account selection page appears, select `jacobw@microsoft.com`
3. **[Required]** Confirm that the only selection in the Staff Group dropdown on the left is `A&I-Azure-ASW Epic and SAP`
   - **How to select**: Find the `<span>` element in the Slicer with class `slicerText` and text `A&I-Azure-ASW Epic and SAP`. Confirm it is the only selected item; if any other item is selected, deselect it and leave only this item selected.
4. After confirming the filter, wait **2 minutes** for the data refresh to complete, then extract KPI data
5. Find the “Metric Trend View” table near the bottom of the page
6. Extract the past six months of data for the five KPIs (the dashboard's default display range)

---

## Output Specifications

### HTML Report Format

- **Save location**: `C:\GitHubCopilot\IronMan\Output\monthly_review_{month}{year}.html`
- **Time zone label**: Use **UTC+8** for the header date and time, in the format `YYYY-MM-DD HH:MM (UTC+8)`
- **Tab structure**: The HTML report uses tabs and includes the following:

| Tab | Name | Contents |
|-----|------|------|
| Home | MOR Summary Report | KPI Dashboard summary, trend tables, MoM Summary, Business Analysis |
| Tab 1 | CPE Insight | All Survey Case details, grouped by AgentAlias (source: Kusto Query) |
| Tab 2 | IR Missing Insight | Current fiscal-year IR Missing case details (source: Dashboard IR Missed Reasons + Kusto Query) |
| Tab 3 | SE Members Performance | Case-performance summary for each SE in FY26 (source: Kusto Query) |

#### US / Costa Rica Engineer KPI Comparison (standalone HTML report)

When the user requests a comparison of US / Costa Rica Engineers, FY tabs, Engineer-by-Engineer drill-down, or Customer Outreach / CaaS Lead impact, produce a standalone, self-contained HTML report:

- **Filename**: `us_cr_engineer_kpi_comparison_FY26_FY27.html`
- **Reference implementation**: `review-reporter/us_cr_engineer_kpi_comparison_FY26_FY27.html`
- **Tabs (fixed at 4)**:

| Tab | Name | Contents |
|-----|------|------|
| 1 | FY26 | Individual FY26 KPIs, team weighted averages, within-period relative individual rankings, Engineer drill-down |
| 2 | FY27 YTD | Individual FY27 YTD KPIs, team weighted averages, within-period relative individual rankings, Engineer drill-down |
| 3 | FY26 vs FY27 | Side-by-side KPIs, DTC/DTS/≤7d changes, cross-FY improvement rankings and conclusions |
| 4 | Customer Outreach / CaaS Lead | CaaS Lead roles, Customer assignments, Program maturity, FY27 Customer portfolio stats, Engineer / Customer drill-down |

> This report is an in-depth analysis of a specific cohort within SE Members Performance; it does not replace the main MOR report. The UI must retain search, Country filter, column sorting, Expand All, keyboard-operable drill-down, and light/dark theme.

#### MOR Summary Report Page Structure
  1. Executive Summary Cards (key KPI snapshot; values show each KPI's **year-to-date Total**, with a MoM change arrow)
  2. Business Analysis (Highlights / Lowlights / Recommendations)
  3. Dashboard 1 tables (Quality Metrics + Operational Metrics, with the full FY trend; show 🟢🟡🔴 indicators for KPIs with targets)
  4. Dashboard 2 tables (Actuals vs Targets + the past six months of Metric Trend View data)
  5. Month-over-Month Summary (previous month vs current month, including Change and Trend direction)

#### Executive Summary Cards List (9 items)

| # | Card name | Source | Status determination |
|---|-----------|------|-------------|
| 1 | CSAT 5★ Avg | Dashboard 1 — Key Metrics by Date (upper table) | ≥ 4.5 Green / ≥ 4.0 Yellow / < 4.0 Red |
| 2 | % IR Met | Dashboard 1 — Key Metrics by Date (upper table) | ≥ 95% Green / ≥ 90% Yellow / < 90% Red |
| 3 | Created Cases | Dashboard 1 — Key Metrics by Date (lower table) | Informational only; no status |
| 4 | Closed Cases | Dashboard 1 — Key Metrics by Date (lower table) | Informational only; no status |
| 5 | Avg DTC | Dashboard 1 — Key Metrics by Date (lower table) | ≤ 10 Green / ≤ 15 Yellow / > 15 Red |
| 6 | % CritSit | Dashboard 1 — Key Metrics by Date (upper table) | ≤ 15% Green / ≤ 20% Yellow / > 20% Red |
| 7 | DSAT | Dashboard 1 — Key Metrics by Date (upper table) | ≤ 1% Green / ≤ 2% Yellow / > 2% Red |
| 8 | % Cases Closed within 7 days | **Dashboard 2** — Actuals \|\| Benchmarks \|\| Variance table | ≥ 50% Green / ≥ 40% Yellow / < 40% Red |
| 9 | Post IR Transfer % | Dashboard 1 — Key Metrics by Date (lower table) | ≤ 20% Green / ≤ 25% Yellow / > 25% Red |

> **Note**: `% Cases Closed within 7 days` is the only Executive Summary Card from Dashboard 2.
> Its value comes from the **Actual Value** column for the `% Cases Closed within 7 days` row
> in Dashboard 2's “Actuals || Benchmarks || Variance” matrix table; the target is **50.0%**.

#### Executive Summary Cards — MoM Change Display Rules

The `.trend` area at the bottom of each card shows the **current month vs. previous month change**, in the format: `{arrow} {±value} vs {previous month}`

- **Arrow direction**: `↑` = value increased, `↓` = value decreased, `→` = unchanged
- **Arrow color** (improvement or deterioration is determined by KPI Direction):
  - **High Good** (CSAT, % IR Met, Created/Closed Cases, % Closed ≤7d): ↑ green = improved; ↓ red = worsened
  - **Low Good** (Avg DTC, % CritSit, DSAT, Post IR Transfer %): ↓ green = improved; ↑ red = worsened
  - **Informational only** (Created Cases, Closed Cases): use gray (`#6b7280`) arrows; do not judge as good or bad
- **Change value format**: `+X.X` or `-X.X` (floating point); `+N` or `-N` (integer)
- **Example**: `<span style="color:#dc3545;font-weight:600;">↑ +4.1</span> <span style="color:#94a3b8;">vs Apr</span>`

#### MoM Change Data Mapping (update monthly)

| # | Card name | Direction | Calculation |
|---|-----------|-----------|----------|
| 1 | CSAT 5★ Avg | high | Current-month CSAT - previous-month CSAT |
| 2 | % IR Met | high | Current-month % - previous-month % |
| 3 | Created Cases | neutral | Current month - previous month |
| 4 | Closed Cases | neutral | Current month - previous month |
| 5 | Avg DTC | low | Current month - previous month |
| 6 | % CritSit | low | Current-month % - previous-month % |
| 7 | DSAT | low | Current-month % - previous-month % (use 0 if there is no data) |
| 8 | % Closed ≤7d | high | Current-month % - previous-month % |
| 9 | Post IR Transfer % | low | Current-month % - previous-month % |

#### Business Analysis Rules

The Business Analysis section is **between the Executive Summary Cards and the Dashboard 1 tables** and provides KPI insights from the Business Owner's perspective.

##### Structure

```html
<div class="analysis-grid">
    <div class="analysis-box highlight-box"><h4>🟢 Highlights</h4><ul>...</ul></div>
    <div class="analysis-box lowlight-box"><h4>🔴 Lowlights / Areas of Concern</h4><ul>...</ul></div>
    <div class="analysis-box recommend-box" style="grid-column: span 2;"><h4>💡 Recommendations</h4><ul>...</ul></div>
</div>
```

##### Highlight Determination Rules (outstanding current-month performance)

For KPIs with a target, list the KPI as a Highlight when the current-month value meets or exceeds the target:

| KPI | Highlight condition | Additional condition |
|-----|----------------|----------|
| CSAT 5★ Avg | Current month ≥ 4.8 | — |
| % IR Met | Current month ≥ 99% | — |
| Avg DTC | Current month ≤ 12 | — |
| % Cases Closed ≤7d | Current month ≥ 50% | — |
| IPD Created | Current month ≥ YTD Total (average) | Or shows an upward trend over the past 3 months |

##### Lowlight Determination Rules (requires attention this month)

For KPIs with a target, list the KPI as a Lowlight when the current-month value misses the target or its trend is declining:

| KPI | Lowlight condition | Additional condition |
|-----|---------------|----------|
| CSAT 5★ Avg | Current month < 4.8 | Or shows a downward trend over the past 3 months |
| % IR Met | Current month < 99% | — |
| Avg DTC | Current month > 12 | Or shows an upward trend over the past 3 months |
| % Cases Closed ≤7d | Current month < 50% | Or shows a downward trend over the past 3 months |
| IPD Created | Current month < YTD Total (average) | Or shows a downward trend over the past 3 months |

- **Trend determination**: Use the most recent 3 months (M-2, M-1, M); label a trend when values move in the same direction for all 3 months or show a notable fluctuation
- **Partial-month data**: If the current month is incomplete (mid-month report), add the note `⚠️ partial month data`

##### Recommendation Writing Principles

- Write from the **Business Owner** perspective and focus on actionable recommendations
- Provide a corresponding recommendation for each Lowlight KPI
- Include: root-cause investigation directions, short-term mitigations, and long-term improvement goals
- For KPIs that consistently meet their targets, recommend maintaining and reinforcing current practices
- Format: `<strong>{Recommendation title}</strong> — {specific details}`

#### CPE Insight Page Structure

- **Data source**: Kusto Query (see `kusto_query` Skill → `references/catalog-custom.md` §ASW CPE Survey)
- **Cluster**：`supportrptwus3prod.westus3.kusto.windows.net` / `KPISupportData`
- **Team-member filtering**: Look up the `AgentAlias` field in the `ASWStakeholder` table and include Surveys only for ASW team members
- **Exclusion list**: Exclude members who have left ASW; currently excluded: `zhaobo`
- **Time range**: The **entire current Fiscal Year (FY)**, filtering on FY start and end dates using `CreatedDateTime` (for example, FY2027 = `2026-07-01` through `2027-06-01`). **Do not limit the data to a single month**; the CPE Insight page must show all Survey records for the full year
- **Data condition**: `isnotempty(TotalCustomerSATScore)` (include only cases with a CSAT score)

##### Kusto Query

```kql
let ASWNames = cluster('bedrock.eastus.kusto.windows.net').database("CSI").ASWStakeholder
| where Role == "Engineer" | where BusinessUnit == "CSS-ASW" | where IsEnable == 'True'
| project AgentAlias, AgentName;
AllCloudsSupportIncidentWithReferenceModelVNext
| where CreatedDateTime >= datetime(_fy_start) and CreatedDateTime < datetime(_fy_end)
| where AgentAlias in (ASWNames | project AgentAlias)
| where AgentAlias !in ('zhaobo','wessm','priyakumar','nmutya','francescav','joaguas','rtjoanda','','') // Exclude members who have left ASW
| where isnotempty(TotalCustomerSATScore)
| lookup ASWNames on AgentAlias
| project IncidentId, Customer_TPName, ServiceName, ClosedDateTime, TotalCustomerSATScore, SurveyVerbatims, CreatedDateTime, AgentAlias, AgentName, Customer_TPID, RegionName
| order by ClosedDateTime desc
```

> **`_fy_start` / `_fy_end` parameters**: Start and end dates for the current Fiscal Year. FY2027 = `2026-07-01` / `2027-06-01`. The query covers CPE Surveys from every month in the full fiscal year.

##### Output Fields (11 columns)

| # | Field name | Description |
|---|----------|------|
| 1 | IncidentId | Case ID |
| 2 | Customer_TPName | Customer name |
| 3 | ServiceName | Service / product name |
| 4 | ClosedDateTime | Case close date and time |
| 5 | TotalCustomerSATScore | CSAT score (1–5) |
| 6 | SurveyVerbatims | Customer written feedback |
| 7 | CreatedDateTime | Case creation date and time |
| 8 | AgentAlias | Engineer alias |
| 9 | AgentName | Engineer name (SE Name), sourced from the `ASWStakeholder` table |
| 10 | Customer_TPID | Customer TPID |
| 11 | RegionName | Customer region |

##### Page Display Rules

- **Table layout**: Combine all Surveys into one table (no grouping)
- **Column order**: Case ID, Customer, Service, AgentAlias, SE Name, CSAT, Verbatim, Closed, Created, Region
- **Default sort**: Sort by `ClosedDateTime` descending (most recent date first)
- **Sortable columns**: Add client-side sorting to **SE Name** (string), **CSAT** (number), and **Closed** (date); clicking a column header toggles ascending / descending order
- **Sorting UI**: Show sort-direction arrows (↑ ascending / ↓ descending) in column headers, highlight on hover, and mark Closed as `desc` by default
- **CSAT score indicators**: 5 = 🟢, 4 = 🟡, 1–3 = 🔴

#### IR Missing Insight Page Structure

- **Purpose**: List detailed information for all IR Missing (Initial Response target missed) cases in the current fiscal year
- **Data sources**:
  1. **Dashboard (IR Missed Reasons)**: Extract Service Request Numbers with `Is IR Met = No` from the “Service Request IR Missed Reasons” table in CES BI Hub
  2. **Kusto Query**: Query case details using the extracted Case IDs

##### Dashboard: IR Missed Reasons (Playwright — fallback only)

> **The default source is the Cowork import file**: `Output/Cowork/asw_ir_missed_FY*.xlsx` (Method A) already contains all IR Missing details (Time to IR, Verbatim, SE Manager), so there is no need to scroll the dashboard. IR Missing is defined as `'Service Request'[Is IR Met] = "No"` (from the Semantic Model, not determined by Kusto). Use the Playwright workflow below only when the Cowork file is unavailable.

| Item | Details |
|------|------|
| **Name** | CSS - A&I and DTP (IR Missed Reasons tab) |
| **Platform** | CES BI Hub |
| **URL** | `https://cesbihub.microsoft.com/User/groups/10/report/81538463-21f0-45bc-8f08-71d5dc9ccc48/0/0?reportTab=ReportSection157aebf13d4b20b43fc5` |
| **Required filter** | Same as Dashboard 1: Channel Function Detail = `ASW_SAPEpicEsc`; Time Fiscal Year = current fiscal year |
| **Filter validation** | See Step 3a–3d below under “Procedure” |

##### Procedure

> **🚨 CRITICAL — The following filter setup is a BLOCKING step: complete every check and wait 2 minutes before extracting data.**

1. Open the URL (using Edge)
2. Wait for the PBI iframe to finish loading
3. **[BLOCKING] Run the Filter Validation Checklist in order (all four checks must pass):**

   **Step 3a — Channel Function Detail**
   - Confirm the restatement shows `is ASW_SAPEpicEsc`
   - If not, expand the Filter Card restatement and select `ASW_SAPEpicEsc`

   **Step 3b — Time LastTwelveMonths**
   - Confirm the restatement shows `is (All)`
   - If not, click the Clear filter button (`[aria-label="Clear filter"]`) to clear it

   **Step 3c — Time LastSixMonths (⚠️ defaults to `is Yes`; must be cleared)**
   - Click the Clear filter button (`[aria-label="Clear filter"]`) → the restatement changes to `is (All)`
   - **If not cleared, 40–50% of cases will be omitted**

   **Step 3d — Time Fiscal Year (⚠️ the bookmark may default to include the prior FY; correct it)**
   - Confirm the restatement shows **only** `is FY2027` (must not include FY2026)
   - **Correction steps**:
     1. First click Clear filter (eraser button `[aria-label="Clear filter"]`) to clear the current selection
     2. Click the expand button (`aria-label="Time Fiscal Year Expand or collapse filter card"`) to expand the card
     3. Select `FY 2027` (confirm `aria-checked="true"`)
     4. Confirm `FY 2026` is not selected (if visible, confirm `aria-checked="false"`)
   - **Validation**: the restatement is `is FY2027` (without `or FY 2026`)

4. **Set the page Slicers** (these differ from the Filter Pane; these are filters on the page):
   1. Channel Function Detail Slicer → search for `ASW_SAP` → select `ASW_SAPEpicEsc`
   2. Fiscal Year Slicer → select only `FY 2027`
5. **[BLOCKING] Wait 2 minutes (120 seconds)** for Data Refresh — `page.waitForTimeout(120000)`
6. **Validate `scrollHeight`**: continue if ≥ 25000px; if < 18000px, return to Step 3 and repeat
7. Find the “Service Request IR Missed Reasons” table (`[role="grid"]`)
8. **Sort by clicking the `Is IR Met` column header** so `No` values appear at the top (click once for ascending order; `No` < `Yes`, so `No` comes first)
9. Scroll the `.mid-viewport` div in increments (400px each), collect the rows, and extract **Service Request Number**. Stop when `Is IR Met` changes from `No` to `Yes`, indicating that all IR Missing cases have been collected
10. **Validate the results**: confirm that cases cover all months starting in Jul (not only the most recent six months)

##### Kusto Query

Use the IR Missing Case ID list extracted from the dashboard to query case details:

```kql
let ASWNames = cluster('bedrock.eastus.kusto.windows.net').database("CSI").ASWStakeholder
| where Role == "Engineer" | where BusinessUnit == "CSS-ASW"
| project AgentAlias, AgentName;
let IRMissingCases = dynamic([_caseIds]); // Case ID list extracted from the dashboard
database('KPISupportData').AllCloudsSupportIncidentWithReferenceModelVNext
| where IncidentId in (IRMissingCases)
| lookup ASWNames on AgentAlias
| project IncidentId, Customer_TPName, ServiceName, AgentAlias, AgentName, CreatedDateTime, ClosedDateTime, InitialSeverity, TTMS, RegionName
| order by CreatedDateTime desc
```

> **`_caseIds` parameter**: The IR Missing Case ID list extracted from the Dashboard's “Service Request IR Missed Reasons” table, formatted as a KQL dynamic array (for example: `'2604010030001234', '2603150040005678'`)
> **Note**: The `IsIrMet` field in the Kusto table is an empty string; the Dashboard (PBI Model) calculates the IR Missing status. Therefore, the Kusto Query does not need a `| where IsIrMet == 'No'` filter; use only the Case IDs extracted from the dashboard.

##### Output Fields (10 columns)

| # | Field name | Description |
|---|----------|------|
| 1 | IncidentId | Case ID |
| 2 | Customer_TPName | Customer name |
| 3 | ServiceName | Service / product name |
| 4 | AgentAlias | Engineer alias |
| 5 | AgentName | Engineer name (SE Name) |
| 6 | CreatedDateTime | Case creation date |
| 7 | ClosedDateTime | Case close date |
| 8 | InitialSeverity | Initial severity |
| 9 | TTMS | Time To Meet SLA (minutes) |
| 10 | RegionName | Customer region |

##### Page Display Rules

- **Table layout**: Combine all IR Missing cases into one table
- **Column order**: Case ID, Customer, Service, SE Manager, Created, Closed, Initial Severity, TTMS, Region
- **Hidden columns**: Do not display Agent (AgentAlias) or SE Name (AgentName) in the table
- **SE Manager column**: Use the `AGENT_MANAGER_MAP` dictionary to map AgentAlias to the SE Manager name (source: the `Manager` field in the `bedrock.CSI.ASWStakeholder` table); for agents absent from the mapping, use the `DEFAULT_SE_MANAGER` default value (`Unknown`)
- **Sort**: Sort by `CreatedDateTime` descending (most recent date first)
- **Layout**: At the top of the page, use a horizontal flex layout (left column 320px + right column flex:1). The left column contains Summary Cards (2×2 grid) + an Avg TTMS by Severity statistics panel; the right column contains an SVG trend chart. Place a full-width data table below.

#### SE Members Performance Page Structure

- **Data source**: Kusto Query (combines case metrics + CPE Survey + IR Missing + ASWStakeholder)
- **Cluster / Database**: `supportrptwus3prod.westus3.kusto.windows.net` / `KPISupportData` (case metrics + CSAT); `bedrock.eastus.kusto.windows.net` / `CSI` (Stakeholder metadata)
- **Fiscal-year range**: **FY26** (`2025-07-01` through `2026-06-30`), filtered by `CreatedDateTime`
- **Member filter**: `bedrock.CSI.ASWStakeholder | where Role == "Engineer" and BusinessUnit == "CSS-ASW"`
- **Exclusion list**: Exclude members who have left ASW (same as CPE Insight)

##### Field Specifications (10 columns)

| # | Field name | Description | Source |
|---|----------|------|------|
| 1 | SE Name | Engineer's full name | `ASWStakeholder.AgentName` |
| 2 | SE Manager Name | Name of the engineer's Manager | `ASWStakeholder.Manager` |
| 3 | Case Assignments | Total cases assigned during that FY | `count()` per AgentAlias |
| 4 | Avg DTS | Average Day to Start (days from case assignment to the SE's first contact) | `avg(DayToSchedule)` |
| 5 | Avg DTC | Average Day to Close (days to close) | `avg(DayToClose)` |
| 6 | % Closed ≤7d | Percentage of cases closed within 7 days | `countif(DayToClose <= 7) / count()` |
| 7 | SE Country | Engineer's country | `ASWStakeholder.Country` |
| 8 | CSAT Avg | Average CSAT score (1–5) from received Surveys | `avg(TotalCustomerSATScore)` |
| 9 | Surveys Count | Number of CSAT Surveys received | `countif(isnotempty(TotalCustomerSATScore))` |
| 10 | IR SLA Missed | Number of cases that missed the Initial Response SLA | From IR Missing data (Cowork xlsx or Dashboard); join by AgentAlias |

##### Kusto Query

```kql
// FY26: 2025-07-01 ~ 2026-06-30
let fy_start = datetime(2025-07-01);
let fy_end   = datetime(2026-07-01);
let ASWMembers = cluster('bedrock.eastus.kusto.windows.net').database("CSI").ASWStakeholder
| where Role == "Engineer" and BusinessUnit == "CSS-ASW"
| where AgentAlias !in ('zhaobo') // Exclude members who have left ASW
| project AgentAlias, AgentName, Manager, Country;
let CaseSummary =
    AllCloudsSupportIncidentWithReferenceModelVNext
    | where CreatedDateTime >= fy_start and CreatedDateTime < fy_end
    | where AgentAlias in (ASWMembers | project AgentAlias)
    | summarize
        CaseAssignments   = count(),
        AvgDTS            = round(avg(todouble(DayToSchedule)), 1),
        AvgDTC            = round(avg(todouble(DayToClose)), 1),
        PctClosedIn7d     = round(countif(DayToClose <= 7) * 100.0 / count(), 1),
        CSATAvg           = round(avg(iff(isnotempty(TotalCustomerSATScore), todouble(TotalCustomerSATScore), real(null))), 2),
        SurveysCount      = countif(isnotempty(TotalCustomerSATScore))
      by AgentAlias;
CaseSummary
| lookup ASWMembers on AgentAlias
| project AgentAlias, AgentName, Manager, CaseAssignments,
          AvgDTS, AvgDTC, PctClosedIn7d, Country, CSATAvg, SurveysCount
| order by AgentName asc
```

> **IR SLA Missed** column: In the Cowork xlsx (`asw_ir_missed_FY26.xlsx`), count by `SR Owner` (AgentAlias) from the `FY26 IR Missed` sheet, then join the result to the query above. If the Cowork file is unavailable, use the Case ID list extracted from the Dashboard IR Missed Reasons and aggregate counts by `AgentAlias`.

##### Page Display Rules

- **Table layout**: One summary table (one row per SE, sorted by SE Name ascending)
- **Default sort**: SE Name ascending
- **Sortable columns**: Every column supports sorting by clicking its header
- **Number formats**:
  - Avg DTS / Avg DTC: one decimal place (for example, `8.3`)
  - % Closed ≤7d: one decimal place as a percentage (for example, `62.5%`)
  - CSAT Avg: two decimal places (for example, `4.75`)
  - IR SLA Missed: integer
- **Color indicators (CSAT Avg)**: 5★=🟢 / 4★=🟡 / ≤3★=🔴 (same rounding-to-integer determination as the CPE Insight badge rules)
- **Color indicators (% Closed ≤7d)**: ≥50%=🟢 / 40–49%=🟡 / <40%=🔴
- **Color indicators (IR SLA Missed)**: 0=🟢 / 1=🟡 / ≥2=🔴
- **Missing data display**: Show gray `-` for CSAT Avg when there are no Surveys and for AvgDTS / AvgDTC when there is no value
- **Summary Cards (top of page)**:
  - Total SE Members (total number of members)
  - Total Case Assignments (total cases for the team)
  - Team Avg CSAT (team average CSAT)
  - Team Avg DTC (team average DTC)
  - Total IR SLA Missed (team total of cases that missed the IR SLA)
  - Team % Closed ≤7d (team percentage of cases closed within 7 days)

#### ASW Engineers

| #  | Engineer Alias | Manager Alias |
|:--:|:--------------:|:-------------:|
| A  |     dantes     |     noambi    |
| B  |    frcardos    |     noambi    |
| C  |    gapetres    |     noambi    |
| D  |    joacarva    |     noambi    |
| E  |    joaguas     |     noambi    |
| F  |    jogoncal    |     noambi    |
| G  |   landreazzi   |     noambi    |
| H  |    pedmarqu    |     noambi    |
| I  |   rubensousa   |     noambi    |
| J  |  tiagosimoes   |     noambi    |
| K  |    alkassap    |     bjames    |
| L  |     anrod      |     bjames    |
| M  |     brwurz     |     bjames    |
| N  |   cschriever   |     bjames    |
| O  |    diambroi    |     bjames    |
| P  |   ejohnston    |     bjames    |
| Q  |    ivayala     |     bjames    |
| R  |    shaddala    |     bjames    |
| S  |    shjoyce     |     bjames    |
| T  |      sish      |     bjames    |
| U  |   tholliday    |     bjames    |
| V  |  andreikovacs  |     jacobw    |
| W  |    aneculae    |     jacobw    |
| X  |    jakelin     |     jacobw    |
| Y  |    shussein    |     jacobw    |
| Z  |     takin      |     jacobw    |
| AA |  tiberiuvlad   |     jacobw    |
| AB |    alveleri    |    nasaggu    |
| AC |  ayonbanerjee  |    nasaggu    |
| AD |    chmarri     |    nasaggu    |
| AE |    fmirdhe     |    nasaggu    |
| AF |    ldondeti    |    nasaggu    |
| AG |    niljain     |    nasaggu    |
| AH |  npericherla   |    nasaggu    |
| AI |     padias     |    nasaggu    |
| AJ |    saadury     |    nasaggu    |
| AK |   vjanapati    |    nasaggu    |
| AL |  kiranchinta   |     dhanat    |
| AM |    jiedong     |     xinxia    |

#### RCA Standardization Report

- Output: `rca_standardization_FY27.html`, with `rca_standardization.js`, the generated `rca_standardization_FY27.data.js`, and `vendor/exceljs.min.js` in the same report folder. Open locally in a browser; no server or runtime CDN/network dependency is required. ExcelJS 4.4.0 and its MIT license are bundled locally; rebuild the vendor bundle with `npm ci` then `npm run vendor`.
- Refresh: run `.\refresh_rca_standardization.ps1` after signing in to Azure CLI with access to both source databases. The script runs `rca_standardization_FY27.kql`, rejects partial query failures, and preserves the last successful export on query failure.
- Period: FY27 created tickets, `2026-07-01 <= CreatedDateTime < 2027-07-01`. This is a point-in-time YTD snapshot, not an automatic live connection.
- Manager alias dropdown: `All`, `noambi`, `bjames`, `jacobw`, `nasaggu`, `dhanat`, `xinxia`. Default: `noambi`. Every report section is recomputed for the chosen scope; `All` ranks the combined cohort, not a concatenation of each manager's top 10.
- Cohort: use the ASW Engineers table above, including the explicit user-provided directs. Do not apply unrelated departures/exclusion lists to this report. Ownership uses the current incident owner, with the latest FY27 CSI snapshot as replacement when `AgentAlias` is unavailable. Select the latest snapshot before filtering its owner to the roster.
- Count each nonempty `IncidentId` once using the latest `ModifiedDateTime` record. Counts describe tickets owned by the cohort, not who submitted the ticket or historical engineer assignments.
- All report sections (KPI summary, support paths, customers, engineer comparison, and source/methodology) start collapsed. Use native, keyboard-accessible `details` / `summary` controls. Changing filters must preserve the user's expanded/collapsed sections.
- Top 10 support paths: group by the distinct pair `[SapSupportPathL2, SapSupportPathL3]`, select the 10 highest ticket counts, break count ties by L2 then L3. Display those same 10 pairs by unrounded Avg DTC descending initially; missing values stay last. Every column is sortable in both directions, with an `aria-sort` indicator. The `#` column is the initial DTC-descending position and stays stable when sorting. Manager changes reset the default sort; column sorting must not change the comparison dropdown selection or its path membership. Include ticket count, Avg DTC, valid DTC records, Avg CSAT, survey records, and the top engineer for that pair. Blank paths remain visible as `Unknown / not classified`.
- Top 10 customers: group by `Customer_TPID` plus `Customer_TPName`, rank by ticket count descending, then name/TPID for deterministic ties. Missing customer names display `Unknown / not available`.
- DTC: `todouble(DTC)` on closed tickets (`ClosedDateTime` present), excluding missing, nonnumeric, or negative values. Compute averages from sum / valid-record count; display one decimal day.
- CSAT: follow the requested average of `TotalCustomerSATScore`, including only valid 1-5 scores; display two decimals. Missing or masked survey fields display `No data`, never zero. `SurveysCount` counts valid scored ticket records, not all survey events.
- Comparison: for a specific manager, title the section `Engineer DTC comparison (Identities Redacted)` and show one row per engineer with tickets. For `All`, title it `Manager DTC comparison (Aggregated)` and show one row per manager, aggregating its directs using sums / valid-record counts. Never average engineer averages. Apply this behavior across all paths and each selected top-10 path pair. Hide zero-ticket rows in the UI and Excel exports; keep rows with tickets but no valid DTC, unranked. Rank by lowest unrounded Avg DTC; exact ties share a rank. No minimum sample threshold is imposed; always show DTC record counts. Zero-ticket engineers still count in roster membership summary cards.
- Hover, focus, or click a comparison DTC record count to show all contributing case IDs and DTC values. A manager row includes all its directs; an engineer row includes only that engineer. Apply both path levels when a path is selected. Retrieve `CaseUri` alongside the deduplicated incident, never construct a DFM URL from the numeric case ID. Each ID links to its source-provided HTTPS `onesupport.crm.dynamics.com` URL in a new tab with `noopener noreferrer`; missing/invalid links explicitly display `DFM link unavailable`. Zero DTC records explicitly show no cases. Escape dismisses the popup; it remains open while hovered or focused. Case lists use the same closed/valid/non-negative DTC predicate as the averages. Refresh rejects incomplete case-list counts; missing/inconsistent details are an explicit error.
- Excel export links create genuine `.xlsx` workbooks locally, honoring current manager/path filters and displayed order. Support-path exports include the sorted top 10; comparison exports include positive-ticket engineer rows or aggregated manager rows for `All`, plus a separate `DTC cases` worksheet. Case IDs remain text, with source DFM hyperlinks when available and an explicit cell note when unavailable. Include report period, filter selection, provenance, and definitions. Averages use guarded formulas, valid denominators, and cached results; missing metrics remain `No data`. Display one decimal for DTC, two for CSAT, and use Calibri throughout.
- Redaction: use the stable `#` labels from the ASW Engineers table (`Engineer A` through `Engineer AM`) in tables, charts, and exports. Never reassign labels by ranking or manager. For Noam (`noambi`), `dantes` always displays as `Engineer A`; if its DTC is lowest for the Linux VM restart/stop pair, show `Engineer A` as the top engineer. All equally lowest engineers are shown for ties.
- The exported report data must contain only anonymized engineer labels, never engineer aliases or names. DTC drill-down and engineer workbooks now include internal support case IDs; share the report bundle and exports only with authorized recipients. The local KQL roster is a maintenance input, not part of the shareable report bundle.
- Interpret path categories as recurring support scenarios, not validated root causes. State source, period, refresh timestamp, ownership semantics, missing metrics, and denominator rules in the report.
- Verification: `npm test`, then check collapsed sections, manager/path filters, all column sorts, hover/focus case lists, and both Excel downloads in a browser. Tests include real-data case-count/sum parity and workbook serialization/reload with cached formula results, no-data rows, zero DTC, filter scope, sort order, and string case IDs.

#### US / Costa Rica Cohort and FY Comparison Requirements

##### Authoritative Cohort

Unless the user provides an updated roster, the US / Costa Rica report must use the following aliases. **Do not** substitute `ASWStakeholder.Region == "America"`, because America also includes non-target members such as Brazil, Portugal, Spain, and India.

```kql
let USEngineers = dynamic([
  "alkassap","brwurz","cschriever","diambroi","ejohnston","ivayala",
  "landreazzi","shaddala","shjoyce","sish","takin","tholliday"
]);
let CostaRicaEngineers = dynamic(["anrod"]);
```

| Country | Alias | Display Name |
|---------|-------|--------------|
| USA | alkassap | Alex Kassap |
| USA | brwurz | Brian Wurzbacher |
| USA | cschriever | Curtis Schriever |
| USA | diambroi | Didier Ambroise |
| USA | ejohnston | Elliott Johnston |
| USA | ivayala | Ivan Ayala |
| USA | landreazzi | Lucas Andreazzi |
| USA | shaddala | Shiva Addala |
| USA | shjoyce | Sheetal Joyce |
| USA | sish | Siddharth Sharma |
| USA | takin | Tanner King |
| USA | tholliday | Taylor Holliday |
| Costa Rica | anrod | Angelica Rodriguez |

##### Live Schema Drift (verified 2026-10)

The following assumptions in the previous `SE Members Performance` query are no longer valid:

- `bedrock.CSI.ASWStakeholder.Country` **has been removed**; only `Region` / `Zone` are currently available, so Country must use the authoritative alias roster above.
- `AllCloudsSupportIncidentWithReferenceModelVNext.AgentAlias` and `CoalescedAgentAlias` are empty in the current view and cannot be used to join directly to Engineer.
- `DayToSchedule` / `DayToClose` have been replaced by the string fields `DTS` / `DTC`; use `todouble(DTS)` / `todouble(DTC)`.
- Survey fields such as `TotalCustomerSATScore` are masked as empty under the current Kusto identity; FY27 CSAT must display `No data`, not 0.

##### Ownership Replacement Join (authoritative method)

1. **FY26 ownership**：`bedrock.CSI.SupportRequestHistory_Snapshot_Table2`
   - Created: `TicketCreatedDateTime`
   - Case ID: `SupportTicketId`
   - Owner: `CaseOwnerAlias`
   - For each case, use `summarize arg_max(dataRefreshDateTime, CaseOwnerAlias) by SupportTicketId`
2. **FY27 ownership**：`bedrock.CSI.SupportRequestHistory_Snapshot_Table3`
   - Created: `todatetime(CreatedDateTime_UTC)`
   - Case ID: `IncidentId`
   - Owner: `CaseOwner`
   - For each case, use `summarize arg_max(dataRefreshDateTime, CaseOwner) by IncidentId`
3. Join the two ownership results on `IncidentId`:
   `supportrptwus3prod.KPISupportData.AllCloudsSupportIncidentWithReferenceModelVNext`
4. Metrics:
   - `AvgDTS = avg(todouble(DTS))`
   - `AvgDTC = avg(todouble(DTC))`
   - `% Closed ≤7d = dcountif(IncidentId, todouble(DTC) <= 7) / dcount(IncidentId)`
   - Calculate DTS / DTC averages using only non-null metric records; include `DTSRecords` / `DTCRecords` when displaying them.
5. Engineers in the roster with no matching ownership (for example, current `brwurz`) must still be shown, but all metrics must display **No data**; do not treat them as 0 or include them in rankings.

##### Team Rollup and Scoring

- Team Avg DTS: weight by `DTSRecords`.
- Team Avg DTC: weight by `DTCRecords`.
- Team % Closed ≤7d: weight by `CaseAssignments`.
- Team CSAT: weight by survey count; display `No data` when FY27 survey data is masked.
- **FY26 ranking**: equally weighted average of cohort min-max normalized scores for Avg DTC / Avg DTS (lower is better) and Closed ≤7d / CSAT (higher is better).
- **FY27 ranking**: equally weighted average of Avg DTC / Avg DTS (lower is better) and Closed ≤7d (higher is better); exclude CSAT when unavailable.
- **FY26 vs FY27 improvement ranking**: independently min-max normalize `FY26 DTC - FY27 DTC`, `FY26 DTS - FY27 DTS`, and `FY27 ≤7d - FY26 ≤7d`, then take their equally weighted average.
- Rankings are **relative scores within the cohort**, not target-based performance ratings. Report conclusions must include supporting metric evidence and state that these rankings do not replace formal performance evaluations.

#### Customer Outreach / CaaS Lead Tab Requirements

##### Roles and Expected Impact

CaaS Lead 2.0 shifts SAP / EPIC support from reactive incident handling to a proactive, insight-driven KnowMe workload experience. Always display these four roles at the top of the tab:

1. **Know the customer**: maintain workload architecture, customer context, support history, risks, and Wiki / Plan of Record.
2. **Connect stakeholders**: establish a cadence with CSAM / CSA / ACE / CSI / Product Engineering / Customer.
3. **Turn cases into insight**: analyze case patterns and customer pain points, using Grafana / Zebra AI to drive proactive action.
4. **Improve support readiness**: prepare for Change Events, routing / monitoring, and reduce customer effort for critical incidents.

##### Assignment Sources and Interpretation

1. **Current master**: the `FOCUS` list in `asw_caas_lead/scripts/generate_dashboard_v1.py` (Customer, TPID, Workload, Lead, Stage, Contract, Program indicators).
2. **Role / deliverable definitions**:
   - `asw_caas_lead/references/project_charter_digest.md`
   - `asw_caas_lead/references/stakeholder_deck_digest.md`
3. **Legacy assignments** (must remain labeled Legacy; do not merge into the current focus master):
   - Curtis Schriever → Sealed Air（TPID `706691`）
   - Taylor Holliday → Mondelez（TPID `18214815`）
4. **Live TPID additions** (from FY27 Kusto customer name resolution):
   - Siddharth Sharma → General Motors（TPID `641658`）
   - Sheetal Joyce → CVS（TPID `782348`）
5. `Medline` is assigned to both Alex Kassap (co-lead) and Shiva Addala (primary):
   - The assignment rollup may count two assignments.
   - Program-level unique-customer cases / closed **must only be counted once**; do not double-count them.

##### Current 13-Person Cohort Assignments

| Engineer | Customer(s) |
|----------|-------------|
| Alex Kassap | Nike; Medline (co-lead) |
| Angelica Rodriguez | TJU |
| Brian Wurzbacher | Brown University |
| Curtis Schriever | Sealed Air (Legacy) |
| Didier Ambroise | University of Kentucky; Ascension Health |
| Elliott Johnston | UTMB |
| Ivan Ayala | PepsiCo |
| Lucas Andreazzi | Shell; Petrobras |
| Shiva Addala | Medline (primary) |
| Sheetal Joyce | CVS |
| Siddharth Sharma | General Motors |
| Tanner King | MichMed; Mt. Sinai |
| Taylor Holliday | Mondelez (Legacy) |

##### Customer Stats Query and Presentation

- Case source: `AllCloudsSupportIncidentWithReferenceModelVNext`, filtered by FY27 `CreatedDateTime` + `Customer_TPID`.
- Lead-owned cases: use the latest ownership from `SupportRequestHistory_Snapshot_Table3`, where `CaseOwner == LeadAlias`.
- Display for each customer:
  - Cases / Closed
  - Avg DTC
  - % Closed ≤7d
  - CritSit count
  - Initial Severity A count
  - Lead-owned cases
  - Top `SapSupportPathL2`
  - Top `SapSupportPathL3`
  - Workload / TPID / Engagement Stage / MC Contract / current-vs-legacy status
  - Case Insight / +AI / Wiki-PoR / Success Stories / Change Events / Executive Escalations
- Engineer rows show assignment count, workload mix, assignment-level case exposure, weighted Avg DTC, weighted ≤7d, CritSit / Sev A, and Stage.
- CaaS portfolio sorting may use case exposure, but the title must state that this is not an individual performance ranking.

##### Causality and Data-Quality Guardrails

- Customer KPIs describe the CaaS Lead's **portfolio environment**; they do not mean that the Lead alone caused a customer outcome.
- Only `Lead-owned cases` can be stated as direct case ownership; even with zero such cases, stakeholder engagement, Wiki, PoR, case analysis, or change-event work may still have been completed.
- Clearly label Current / Legacy / Co-lead / Primary lead.
- Show 0 / No data for onboarding customers without a TPID or not yet routed; do not remove them.
- Program indicators are manual / master-list tallies; Customer operational KPIs are Kusto observations. Do not combine them into a single "impact score."
- Report conclusions separately describe:
  1. Customer support exposure / outcome
  2. Program maturity / deliverable completion
  3. Next-action opportunity

---

- **KPI Target color-coding rules** (apply to Dashboard 1 KPIs with a Target):
  - 🟢 = Meets target (at or above Target)
  - 🟡 = Near target (below Target but within a 5% gap)
  - 🔴 = Below target (more than 5% below Target)
  - Calculate the 5% gap using 5% of the Target value as the threshold (for example, for Target ≥ 4.8, 5% = 0.24 and the Yellow range is 4.56–4.79).
  - Always use traffic-light indicators (🟢🟡🔴); do not use text symbols (✓/⚠/✗).
  - Always display KPI values in **black**, with the indicator after the value (for example, `4.86 🟢`, `4.67 🟡`, `4.50 🔴`).
  - **Indicator placement**: show indicators only after monthly values; **do not show an indicator in the Total column** (Total is a fiscal-year cumulative value, not a single-month indicator).
  - **Applicable KPI list**:
    | KPI | Target | Direction |
    |-----|--------|-----------|
    | CSAT 5★ Avg | ≥ 4.8 | high (higher is better) |
    | % IR Met | ≥ 99% | high |
    | Avg Day to Close | ≤ 12 | low (lower is better) |
    | % Cases Closed ≤7d | ≥ 50% | high |
- **vs Total indicator rules** (for KPIs without an explicit Target that use Total as the baseline, such as IPD Created):
  - 🟢 = Monthly value ≥ Total (at or above the average level)
  - 🟡 = Monthly value is below Total, but the gap is within 5%
  - 🔴 = Monthly value is more than 5% below Total
  - Do not apply color coding to the Total column itself.
  - Display "vs Total" in the Target column.
- **KPIs without indicators**: do not apply color coding to KPIs whose Target and Direction are both `-`.
- **Trend indicator rules** (for MoM Summary, etc.):
  - 🟢 Green = improving / on target
  - 🟡 Orange = near target / monitor
  - 🔴 Red = below target / immediate action required
- **The footer** must specify:
  - Filter conditions used for each dashboard
  - Data date (Data as of)
  - Report generation time (UTC+8)

---

## Standard HTML Report Template

The following is the standard format template for MOR Summary Report HTML output. Future monthly reports should follow this structure, replacing only the data.

### Overall Structure

```
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>MOR Summary Report - {Month} {Year} | ASW SAP & Epic Support</title>
  <style>/* Shared CSS (see Design System) */</style>
</head>
<body>
  <div class="header">(Report header)</div>
  <div class="tab-nav">(4 tab-navigation buttons)</div>
  <div id="tab-mor" class="tab-panel active">(Tab 1: MOR Summary Report)</div>
  <div id="tab-cpe" class="tab-panel">(Tab 2: CPE Insight)</div>
  <div id="tab-irmissing" class="tab-panel">(Tab 3: IR Missing Insight)</div>
  <div id="tab-sembers" class="tab-panel">(Tab 4: SE Members Performance)</div>
  <script>/* switchTab function */</script>
</body>
</html>
```

### Design System (CSS Variables and Shared Styles)

```css
:root {
    --green: #28a745;    /* Meets target */
    --yellow: #ffc107;   /* Near target */
    --red: #dc3545;      /* Below target */
    --blue: #0078d4;     /* Microsoft Blue, primary color */
    --dark: #1a1a2e;     /* Title / dark background */
    --card-bg: #ffffff;
    --bg: #f4f6f9;       /* Page background */
    --text: #333333;
    --border: #e0e0e0;
}
```

**Main component classes**:

| CSS Class | Purpose |
|-----------|------|
| `.header` | Dark banner at the top of the page (gradient: `--dark` → `#16213e`) |
| `.tab-nav` / `.tab-btn` | Tab-switching button row |
| `.tab-panel` | Tab content area (shown when `.active`) |
| `.section` / `.section-title` | Section heading (blue underline) |
| `.cards` / `.card` | Executive Summary KPI cards (grid layout, left-side color band) |
| `.card.green` / `.card.yellow` / `.card.red` | Card color-band variants |
| `.table-wrapper` / `table` | Data table (rounded white background, hover highlight) |
| `.highlight-col` | Current-month column (yellow background, bold) |
| `.total-col` | Total column (green background, bold) |
| `.badge` / `.badge-green` / `.badge-yellow` / `.badge-red` | CSAT score badges (5★=green, 4★=yellow, ≤3★=red) |
| `.analysis-grid` / `.analysis-box` | Business Analysis section (2-column grid) |
| `.highlight-box` / `.lowlight-box` / `.recommend-box` | Analysis section color bands (green/red/blue) |
| `.cpe-summary-cards` / `.cpe-card` | CPE / IR Missing summary cards (top color band, not left-side) |
| `th.sortable` / `.asc` / `.desc` | Sortable column headers (hover highlight, direction arrow indicator) |
| `.verbatim-col` | Verbatim column (`white-space: normal`, allowing automatic line wrapping) |
| `.footer` | Footer (data source, Filter, date) |

### Header Section

```html
<div class="header">
    <h1>MOR Summary Report — {Month} {Year}</h1>
    <div class="subtitle">ASW SAP &amp; Epic Escalation Support | Asia Region</div>
    <div class="meta">
        <span>Fiscal Year: FY{YYYY} (Jul {YYYY-1} – Jun {YYYY})</span> |
        <span>Report Period: FM Jul {YYYY-1} – FM {Month} {Year} ({N} months)</span>
    </div>
</div>
```

### Tab Navigation

```html
<div class="tab-nav">
    <button class="tab-btn active" onclick="switchTab('mor')">MOR Summary Report</button>
    <button class="tab-btn" onclick="switchTab('cpe')">CPE Insight</button>
    <button class="tab-btn" onclick="switchTab('irmissing')">IR Missing Insight</button>
    <button class="tab-btn" onclick="switchTab('sembers')">SE Members Performance</button>
</div>
```

### Tab 1: MOR Summary Report Structure

Include the following six sections in order:

#### 1. Executive Summary Cards (9 cards)

```html
<div class="section">
    <h2 class="section-title">Executive Summary (Year-to-Date Total)</h2>
    <div class="cards">
        <div class="card {color}">
            <div class="label">{KPI Name}</div>
            <div class="value">{YTD Total value}</div>
            <div class="trend">FY{YY} YTD</div>
        </div>
        <!-- Repeat for 9 cards, referring to the Executive Summary Cards list -->
    </div>
</div>
```

- `{color}` = `green` | `yellow` | `red` (according to the Status determination rules), or omit it for an informational card.

#### 2. Business Analysis

```html
<div class="analysis-grid">
    <div class="analysis-box highlight-box">
        <h4>🟢 Highlights</h4>
        <ul><li><strong>{Title}</strong> — {Description}</li>...</ul>
    </div>
    <div class="analysis-box lowlight-box">
        <h4>🔴 Lowlights / Areas of Concern</h4>
        <ul><li><strong>{Title}</strong> — {Description}</li>...</ul>
    </div>
    <div class="analysis-box recommend-box" style="grid-column: span 2;">
        <h4>💡 Recommendations</h4>
        <ul><li><strong>{Title}</strong> — {Description}</li>...</ul>
    </div>
</div>
```

- Highlights / Lowlights occupy one column each (2-column grid).
- Recommendations span both columns (`grid-column: span 2`).

#### 3. Dashboard 1 — Quality Metrics Table

```html
<div class="section">
    <h2 class="section-title">Dashboard 1 — Quality Metrics (FY{YYYY})</h2>
    <div class="table-wrapper">
        <table>
            <thead>
                <tr>
                    <th>KPI</th><th>Target</th>
                    <th>Jul</th><th>Aug</th>...<th class="highlight-col">{Current month}</th>
                    <th class="total-col">Total</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>{KPI Name}</td>
                    <td style="font-weight:600;color:#555;">{Target value}</td>
                    <td>{Monthly value} {indicator}</td>
                    ...
                    <td class="highlight-col">{Current-month value} {indicator}</td>
                    <td class="total-col">{Total value} {indicator}</td>
                </tr>
            </tbody>
        </table>
    </div>
</div>
```

- **Quality Metrics KPIs** (6 items, from the upper table): CSAT 5★ Avg, DSAT, CSAT Surveys, CSAT Response Rate, % CritSit, % IR Met
- **Operational Metrics KPIs** (12 items, from the lower table): IPD Created, IPD Closed, Open Cases, Created Cases, Closed Cases, CSS TMPI, Avg DTC, Backlog Count, Backlog DtC, Collaboration Tasks, Post IR Transfer %, % Transfer
- Mark the last month with data for the fiscal year using the `highlight-col` class.
- Add a `⚠️` notice for "partial-month data" (for example, mid-month data).

#### 4. Dashboard 2 — OpEx Metric Trend View Table

Includes two subtables:
- **Primary OpEx Metrics (5 items with a Target)**: columns = Category | KPI | Target | Most recent 6 months
- **Additional OpEx Metrics (6 items without a Target)**: columns = Category | KPI | Most recent 6 months

Follow these with the **FYTD Actuals vs Benchmarks** table:

```html
<table>
    <thead>
        <tr><th>KPI</th><th>Actual</th><th>Target</th><th>Variance</th><th>Status</th></tr>
    </thead>
    <tbody>
        <tr>
            <td>{KPI Name}</td>
            <td>{Actual value}</td>
            <td>{Target value}</td>
            <td class="improved|declined">{Variance}</td>
            <td>🟢 Met | 🔴 Not Met</td>
        </tr>
    </tbody>
</table>
```

#### 5. Month-over-Month Summary Table

```html
<table class="mom-table">
    <thead>
        <tr><th>KPI</th><th>{Previous month} {Year}</th><th>{Current month} {Year}</th><th>Change</th><th>Trend</th></tr>
    </thead>
    <tbody>
        <tr>
            <td>{KPI}</td>
            <td>{Previous-month value}</td>
            <td>{Current-month value}</td>
            <td class="improved|declined">{Change value}</td>
            <td>{Indicator} {Direction arrow}</td>
        </tr>
    </tbody>
</table>
```

- **Trend direction**: `↑` = value increased, `↓` = value decreased, `→` = unchanged
- **class**: `.improved` = improvement (green), `.declined` = deterioration (red)
- Include a `⚠️` partial-month data notice.

#### 6. Footer

```html
<div class="footer">
    <p><strong>Data Sources &amp; Filters:</strong></p>
    <p>• Dashboard 1: CES BI Hub — CSS A&amp;I and DTP | Filter: Channel Function Detail = ASW_SAPEpicEsc | Time Fiscal Year = FY {YYYY} | LastSixMonths = (All)</p>
    <p>• Dashboard 2: Power BI (msit) — OpEx Overall PCY Level A&amp;I+DTP | Filter: Staff Group = A&amp;I-Azure-ASW Epic and SAP</p>
    <p>• CPE Survey: Kusto — supportrptwus3prod / KPISupportData | FY{YYYY} (Jul {YYYY-1} – {Month} {Year}) | ASW Engineers only</p>
    <p>• SE Members: Kusto — supportrptwus3prod / KPISupportData + bedrock.eastus / CSI.ASWStakeholder | IR SLA Missed: Cowork asw_ir_missed_FY26.xlsx (or Dashboard fallback) | FY26 (Jul 2025 – Jun 2026)</p>
    <p>• Data as of: {YYYY-MM-DD} (Dashboard 1 &amp; 2)</p>
    <p>• Report generated: {YYYY-MM-DD HH:MM} (UTC+8)</p>
</div>
```

### Tab 2: CPE Insight Structure

```html
<div id="tab-cpe" class="tab-panel">
    <div class="section">
        <h2 class="section-title">CPE Insight — ASW Team SAP CPE Surveys</h2>
        <p style="font-size:13px; color:#666; margin-bottom:16px;">
            FY{YYYY} YTD Survey responses (Jul {YYYY-1} – {Month} {Year}) sorted by Closed Date.
            Source: Kusto <code>KPISupportData.AllCloudsSupportIncidentWithReferenceModelVNext</code>
        </p>
        <!-- Summary Cards -->
        <div class="cpe-summary-cards">
            <div class="cpe-card"><div class="cpe-label">Total Surveys</div><div class="cpe-value">{N}</div></div>
            <div class="cpe-card"><div class="cpe-label">Avg CSAT Score</div><div class="cpe-value">{X.XX}</div></div>
            <div class="cpe-card"><div class="cpe-label">5★ Responses</div><div class="cpe-value">{N} ({%})</div></div>
            <div class="cpe-card"><div class="cpe-label">4★ Responses</div><div class="cpe-value">{N}</div></div>
            <div class="cpe-card"><div class="cpe-label">≤3★ Responses</div><div class="cpe-value">{N}</div></div>
            <div class="cpe-card"><div class="cpe-label">Engineers</div><div class="cpe-value">{N}</div></div>
        </div>
        <!-- Data Table -->
        <div class="table-wrapper"><table>
            <colgroup>
                <col style="width:130px"><col style="width:auto"><col style="width:auto">
                <col style="width:95px"><col style="width:auto"><col style="width:50px">
                <col style="width:30%"><col style="width:85px"><col style="width:85px"><col style="width:auto">
            </colgroup>
            <thead><tr>
                <th>Case ID</th><th class="sortable" data-col="1">Customer</th><th class="sortable" data-col="2">Service</th><th>AgentAlias</th>
                <th class="sortable" data-col="4">SE Name</th><th>CSAT</th><th>Verbatim</th><th class="sortable desc" data-col="7">Closed</th><th class="sortable" data-col="8">Created</th><th class="sortable" data-col="9">Region</th>
            </tr></thead>
            <tbody>
                <!-- One row per record -->
                <tr>
                    <td>{IncidentId}</td>
                    <td>{Customer_TPName}</td>
                    <td>{ServiceName}</td>
                    <td>{AgentAlias}</td>
                    <td>{AgentName}</td>
                    <td><span class="badge badge-{green|yellow|red}">{Score} ★</span></td>
                    <td class="verbatim-col" style="text-align:left;white-space:normal;font-size:12px;">
                        {Verbatim text; when empty, display <span style="color:#ccc;">-</span>}
                    </td>
                    <td>{YYYY-MM-DD}</td>
                    <td>{YYYY-MM-DD}</td>
                    <td>{RegionName}</td>
                </tr>
            </tbody>
        </table></div>
    </div>
</div>
```

**CPE table rules**:
- **Table layout**: use `table-layout: auto` and `<colgroup>` to set suggested column widths; other columns automatically fit their content.
- **Column widths**: Case ID 130px, Customer auto, Service auto, AgentAlias 95px, SE Name auto, CSAT 50px, Verbatim 30% (remaining space), Closed 85px, Created 85px, Region auto.
- **Interactive sorting**: clicking the headers of Customer, Service, SE Name, Closed, Created, and Region (`th.sortable`) sorts those six columns; default sort is Closed descending.
- **Sort indicators**: `th.sortable::after` displays ⇅ (unsorted), ↑ (ascending `.asc`), or ↓ (descending `.desc`).
- CSAT badges: `badge-green` (5★), `badge-yellow` (4★), `badge-red` (≤3★).
- Wrap Verbatim text automatically (`white-space: normal`, class `verbatim-col`); use `white-space: nowrap` + `text-overflow: ellipsis` for other columns.
- Display a gray `-` when Verbatim is empty.
- Sorting: default to `ClosedDateTime` descending (most recent date first).

### Tab 3: IR Missing Insight Structure

```html
<div id="tab-irmissing" class="tab-panel">
    <div class="section">
        <h2 class="section-title">IR Missing Insight — FY{YYYY} Initial Response Not Met Cases</h2>
        <p style="font-size:13px; color:#666; margin-bottom:16px;">
            FY{YYYY} YTD IR Missing cases for ASW_SAPEpicEsc (Jul {YYYY-1} – {Month} {Year}).
            Source: CES BI Hub IR Missed Reasons Dashboard + Kusto
        </p>
        <!-- Main Flex container: Cards+TTMS on the left, Chart on the right -->
        <div style="display:flex; gap:20px; align-items:stretch; margin-bottom:20px;">
            <!-- Left column (fixed at 320px): Summary Cards + TTMS statistics -->
            <div style="display:flex; flex-direction:column; gap:12px; width:320px; flex-shrink:0;">
                <!-- Summary Cards (2×2 grid) -->
                <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px;">
                    <div class="cpe-card" style="border-top-color:#e74c3c;">
                        <div class="cpe-label">Total IR Missing</div><div class="cpe-value">{N}</div>
                    </div>
                    <div class="cpe-card" style="border-top-color:#e74c3c;">
                        <div class="cpe-label">Engineers Involved</div><div class="cpe-value">{N}</div>
                    </div>
                    <div class="cpe-card" style="border-top-color:#e67e22;">
                        <div class="cpe-label">Severity A/1</div><div class="cpe-value">{N}</div>
                    </div>
                    <div class="cpe-card" style="border-top-color:#f39c12;">
                        <div class="cpe-label">Severity B</div><div class="cpe-value">{N}</div>
                    </div>
                </div>
                <!-- Average TTMS by Severity (fills the remaining space at the bottom of the left column) -->
                <div style="flex:1; background:#fff; border-radius:10px; padding:16px; box-shadow:0 2px 8px rgba(0,0,0,0.06); border-top:3px solid #6366f1;">
                    <div style="font-size:0.7rem; color:#64748b; text-transform:uppercase; margin-bottom:10px;">Avg TTMS by Severity</div>
                    <!-- One card per Severity (A / B / C), stacked vertically -->
                    <div style="margin-bottom:10px; padding:8px 10px; background:#f8fafc; border-radius:6px; border-left:3px solid #e74c3c;">
                        <div style="font-weight:600; font-size:0.8rem; color:#e74c3c;">Severity A</div>
                        <div style="font-size:1.3rem; font-weight:700; color:#1e293b;">{avg} <span style="font-size:0.7rem; color:#94a3b8;">mins</span></div>
                        <div style="font-size:0.65rem; color:#94a3b8;">{N} cases | Range: {min} – {max}</div>
                    </div>
                    <div style="margin-bottom:10px; padding:8px 10px; background:#f8fafc; border-radius:6px; border-left:3px solid #e67e22;">
                        <div style="font-weight:600; font-size:0.8rem; color:#e67e22;">Severity B</div>
                        <div style="font-size:1.1rem; color:#94a3b8;">N/A</div>
                        <div style="font-size:0.65rem; color:#94a3b8;">No SLA requirement</div>
                    </div>
                    <div style="margin-bottom:10px; padding:8px 10px; background:#f8fafc; border-radius:6px; border-left:3px solid #3498db;">
                        <div style="font-weight:600; font-size:0.8rem; color:#3498db;">Severity C</div>
                        <div style="font-size:1.1rem; color:#94a3b8;">N/A</div>
                        <div style="font-size:0.65rem; color:#94a3b8;">No SLA requirement</div>
                    </div>
                </div>
            </div>
            <!-- Right column (flex:1): IR Missing Trend Chart -->
            <div style="flex:1; min-width:350px; background:#fff; border-radius:10px; padding:12px 16px; box-shadow:0 2px 8px rgba(0,0,0,0.06); border-top:3px solid #0078d4;">
                <div style="font-size:0.7rem; color:#64748b; text-transform:uppercase; margin-bottom:4px;">IR Missing Trend (FY{YYYY})</div>
                <svg viewBox="0 0 550 180" style="width:100%; height:auto; font-family:sans-serif;">
                    <!-- Grid: Y-axis 0~{maxCumulative}, X-axis Jul~{last month} -->
                    <!-- Cumulative line: stroke #0078d4, stroke-width 2.5 -->
                    <!-- Data points: circle r=3.5, fill #0078d4, value labels above -->
                    <!-- Monthly bars: fill #f97316, opacity 0.5, with count labels -->
                    <!-- Legend: top-left, Cumulative (blue circle) + Monthly (orange rect) -->
                </svg>
            </div>
        </div>
        <!-- Data Table -->
        <div class="table-wrapper"><table>
            <thead><tr>
                <th>Case ID</th><th>Customer</th><th>Service</th><th>SE Manager</th>
                <th>Created</th><th>Closed</th><th>Initial Severity</th><th>TTMS (mins)</th><th>Region</th>
            </tr></thead>
            <tbody>
                <tr>
                    <td>{IncidentId}</td>
                    <td>{Customer_TPName}</td>
                    <td>{ServiceName}</td>
                    <td>{SE Manager (looked up via AGENT_MANAGER_MAP)}</td>
                    <td>{YYYY-MM-DD}</td>
                    <td>{YYYY-MM-DD}</td>
                    <td>{Sev A in bold red; others in normal style}</td>
                    <td>{TTMS value; display null as a gray -, unusually high values in bold red}</td>
                    <td>{RegionName}</td>
                </tr>
            </tbody>
        </table></div>
    </div>
</div>
```

**IR Missing page layout principles**:
- **Overall layout**: the top uses a horizontal flex layout (left column fixed at 320px + right column flex:1), with a full-width data table below.
- **Left column**: Summary Cards (2×2 grid) + Avg TTMS by Severity (vertically stacked to fill the remaining height).
- **Right column**: SVG line chart (blue Cumulative line + orange Monthly Count bars), automatically filling the available right-side space.
- **Visual balance**: both columns have equal height (`align-items:stretch`) to avoid blank space on either side.

**IR Missing table rules**:
- Severity A：`<span style="color:#e74c3c; font-weight:600;">A</span>`
- Severity B/C: normal text
- TTMS null (common for Sev B/C): `<span style="color:#ccc;">-</span>`
- TTMS values: **round to one decimal place** (for example, `2.48` → `2.5`, `29.98` → `30.0`)
- Unusually high TTMS values (> 480 mins / 8 hours): `style="color:#e74c3c; font-weight:600;"`
- If SE Name is empty: gray `-`
- Sorting: `CreatedDateTime` descending

### Tab 4: SE Members Performance Structure

```html
<div id="tab-sembers" class="tab-panel">
    <div class="section">
        <h2 class="section-title">SE Members Performance — FY26 (Jul 2025 – Jun 2026)</h2>
        <p style="font-size:13px; color:#666; margin-bottom:16px;">
            FY26 case performance summary per ASW engineer.
            Source: Kusto <code>KPISupportData.AllCloudsSupportIncidentWithReferenceModelVNext</code> + <code>bedrock.CSI.ASWStakeholder</code> + IR Missing data.
        </p>
        <!-- Summary Cards (6 cards) -->
        <div class="cpe-summary-cards">
            <div class="cpe-card"><div class="cpe-label">Total SE Members</div><div class="cpe-value">{N}</div></div>
            <div class="cpe-card"><div class="cpe-label">Total Case Assignments</div><div class="cpe-value">{N}</div></div>
            <div class="cpe-card"><div class="cpe-label">Team Avg CSAT</div><div class="cpe-value">{X.XX}</div></div>
            <div class="cpe-card"><div class="cpe-label">Team Avg DTC</div><div class="cpe-value">{X.X} days</div></div>
            <div class="cpe-card"><div class="cpe-label">Total IR SLA Missed</div><div class="cpe-value">{N}</div></div>
            <div class="cpe-card"><div class="cpe-label">Team % Closed ≤7d</div><div class="cpe-value">{X.X}%</div></div>
        </div>
        <!-- Data Table -->
        <div class="table-wrapper"><table>
            <colgroup>
                <col style="width:auto"><!-- SE Name -->
                <col style="width:auto"><!-- SE Manager Name -->
                <col style="width:90px"><!-- Case Assignments -->
                <col style="width:70px"><!-- Avg DTS -->
                <col style="width:70px"><!-- Avg DTC -->
                <col style="width:100px"><!-- % Closed ≤7d -->
                <col style="width:80px"><!-- SE Country -->
                <col style="width:80px"><!-- CSAT Avg -->
                <col style="width:90px"><!-- Surveys Count -->
                <col style="width:100px"><!-- IR SLA Missed -->
            </colgroup>
            <thead><tr>
                <th class="sortable asc" data-col="0">SE Name</th>
                <th class="sortable" data-col="1">SE Manager Name</th>
                <th class="sortable" data-col="2">Case Assignments</th>
                <th class="sortable" data-col="3">Avg DTS</th>
                <th class="sortable" data-col="4">Avg DTC</th>
                <th class="sortable" data-col="5">% Closed ≤7d</th>
                <th class="sortable" data-col="6">SE Country</th>
                <th class="sortable" data-col="7">CSAT Avg</th>
                <th class="sortable" data-col="8">Surveys Count</th>
                <th class="sortable" data-col="9">IR SLA Missed</th>
            </tr></thead>
            <tbody>
                <!-- One row per SE, sorted by SE Name ascending -->
                <tr>
                    <td>{AgentName}</td>
                    <td>{Manager}</td>
                    <td style="text-align:right;">{CaseAssignments}</td>
                    <td style="text-align:right;">{AvgDTS or <span style="color:#ccc;">-</span>}</td>
                    <td style="text-align:right;">{AvgDTC or <span style="color:#ccc;">-</span>}</td>
                    <td style="text-align:right;">{PctClosedIn7d}% {🟢|🟡|🔴}</td>
                    <td>{Country}</td>
                    <td style="text-align:right;">{CSATAvg} {🟢|🟡|🔴} or <span style="color:#ccc;">-</span></td>
                    <td style="text-align:right;">{SurveysCount}</td>
                    <td style="text-align:right;">{IRSLAMissed} {🟢|🟡|🔴}</td>
                </tr>
            </tbody>
        </table></div>
    </div>
</div>
```

**SE Members Performance table rules**:
- **Default sort**: SE Name ascending (`th.sortable.asc` is shown on the SE Name column header).
- **Sortable columns**: all 10 columns support sorting by clicking their headers.
- **Number formats**: Avg DTS / Avg DTC to one decimal place; % Closed ≤7d to one decimal place (with %); CSAT Avg to two decimal places; IR SLA Missed as an integer.
- **Color indicator rules**:
  - CSAT Avg: round the average to the nearest integer → 5=🟢 / 4=🟡 / ≤3=🔴; display a gray `-` when there are no surveys.
  - % Closed ≤7d：≥50%=🟢 / 40–49%=🟡 / <40%=🔴
  - IR SLA Missed：0=🟢 / 1=🟡 / ≥2=🔴
- **Missing data display**: display `<span style="color:#ccc;">-</span>` when Avg DTS / Avg DTC / CSAT Avg has no value.
- **Number alignment**: right-align all numeric columns (Case Assignments, Avg DTS, Avg DTC, % Closed ≤7d, CSAT Avg, Surveys Count, IR SLA Missed) with `text-align:right`.
- **Data source attribution**: add `• SE Members: Kusto KPISupportData + bedrock.CSI.ASWStakeholder | IR SLA Missed: Cowork asw_ir_missed_FY26.xlsx (or Dashboard fallback) | FY26 (Jul 2025 – Jun 2026)` to the footer.

**Average TTMS by Severity calculation rules**:
- Position: below the Summary Cards in the left column (same flex column), filling the remaining vertical space.
- Present as vertically stacked cards, one per Severity (A / B / C).
- Calculation: average all non-null TTMS values for that Severity (round to one decimal place).
- If all TTMS values for that Severity are null, display `N/A` and the note "No SLA requirement".
- Card contents: Severity name, average, case count, and value range (min – max).
- Colors: Sev A `#e74c3c` / Sev B `#e67e22` / Sev C `#3498db`.
- Container style: `border-top: 3px solid #6366f1`, rounded white background.

**SVG monthly trend chart rules**:
- **Position**: right column (flex:1), same height as the left column.
- **viewBox**: `0 0 550 180` (compact to fit the available right-side space).
- **Chart type**: combination chart (Cumulative line + Monthly Count bars).
- **Cumulative line**: `stroke #0078d4` (Microsoft Blue), `stroke-width 2.5`, circular data points r=3.5.
- **Monthly bars**: `fill #f97316` (orange), `opacity 0.5`, bottom-aligned.
- **Y-axis**: maximum cumulative value; use the same scale for both chart series.
- **X-axis**: Jul through the current month, evenly spaced.
- **Legend**: upper left, blue dot = Cumulative, orange square = Monthly.
- **Container style**: `border-top: 3px solid #0078d4`, rounded white background.

### Tab-Switching Script

```html
<script>
function switchTab(tabId) {
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.getElementById('tab-' + tabId).classList.add('active');
    event.target.classList.add('active');
}
</script>
```

### Template Replacement Variables

| Variable | Description | Example |
|------|------|------|
| `{Month}` | Report month (full English name) | `May` |
| `{Year}` | Report year | `2026` |
| `{YYYY}` | Fiscal year | `2026` |
| `{YYYY-1}` | Fiscal-year start year | `2025` |
| `{YY}` | Abbreviated fiscal year | `26` |
| `{N}` | Count value for each summary card | `43` |
| `{Current month}` | Current month (English abbreviation) | `May` |
| `{Previous month}` | Previous month (full English name) | `Apr` |

---

## Workflow

### Step 0 — Select the report option

Use [Report options and request routing](#report-options-and-request-routing) before collecting data. If RCA Standardization is selected, follow [RCA Standardization Report](#rca-standardization-report) and its refresh/verification instructions instead of the MOR-only steps below. For other standalone reports, follow their corresponding sections; apply the full monthly-review workflow only when producing MOR.

### Step 1 — Data Collection

> 🚀 **Default path**: Cowork always provides Dashboard 1 KPI + IR Missing data (files are placed in `Output/Cowork/`); continue to retrieve Dashboard 2 OpEx with Playwright + external Edge; use Kusto MCP for CPE Survey. Use the Dashboard 1 / IR Missed Playwright fallback only if Cowork files are missing or expired.

> 🚨 **Browser requirements (Playwright fallback / Dashboard 2 only; BLOCKING RULE, required on every run)**:
>
> **Always open** all Dashboard pages (Dashboard 1, Dashboard 2, IR Missed Reasons) in an external Microsoft Edge browser. **The following browsers are prohibited**:
>
> - ❌ **VS Code Simple Browser** (embedded browser)
> - ❌ **`open_browser_page` / VS Code Chat integrated Playwright browser** (also embedded and blocked by Conditional Access)
> - ❌ Any third-party browser other than Edge
>
> **Correct procedure**:
>
> 1. Open external Edge by running `Start-Process msedge '<URL>'` in a terminal.
> 2. Use **Playwright MCP tools (`mcp_playwright_browser_*`)** to connect to that external Edge via CDP for page interaction and data extraction.
> 3. **Do not call `open_browser_page`** (it opens the integrated browser and violates this rule).
>
> **Reason**: VS Code embedded / Chat integrated browsers cannot access internal systems such as CES BI Hub under Conditional Access compliance policies; they may be stuck on the sign-in page or denied access.
>
> **If Playwright MCP cannot connect to external Edge**: notify the user and pause execution; do not fall back to the integrated browser. Ask the user to operate Edge manually and provide a screenshot / exported file, or start an Edge instance with a CDP debug port using `Start-Process msedge --remote-debugging-port=9222` for Playwright to attach to.

> ⚠️ **Mandatory verification (required on every run)**: every time a Monthly Summary Report is produced, **retrieve these four categories of data sources again**; do not skip them or use cached / historical data only:
>
> | # | Data source | Purpose | Preferred method | Fallback |
> |---|----------|------|---------|----------|
> | 1 | **Commercial Insights+ V2** — KPI by Month | 19 KPI（Dashboard 1 Quality + Operational） | Cowork xlsx | Playwright + CES BI Hub |
> | 2 | **Commercial Insights+ V2** — IR Missed | IR Missing details | Cowork xlsx | Playwright + CES BI Hub IR Missed Reasons |
> | 3 | **OpEx Overall PCY Level A&I+DTP** | 5 OpEx KPIs | Playwright + Edge (no Cowork version) | — |
> | 4 | **Kusto — CPE Survey** | CPE Insight (CSAT, Verbatim, AgentName) | Kusto MCP | — |
>
> Even if data was collected for the previous report, **retrieve it again** on every run to ensure the report reflects the latest data. Do not use cached data, historical records, or data from previous conversations.

> **Additional mandatory sources for US / Costa Rica + CaaS reports (only when that standalone report is requested)**:
>
> | # | Data source | Purpose |
> |---|----------|------|
> | 5 | `CSI.SupportRequestHistory_Snapshot_Table2` | FY26 Engineer ownership |
> | 6 | `CSI.SupportRequestHistory_Snapshot_Table3` | FY27 Engineer ownership + Lead-owned cases |
> | 7 | `KPISupportData.AllCloudsSupportIncidentWithReferenceModelVNext` | DTS / DTC / ≤7d + Customer portfolio KPI |
> | 8 | `asw_caas_lead/scripts/generate_dashboard_v1.py` → `FOCUS` | Current CaaS assignments / Stage / indicators |
> | 9 | Customer Outreach charter + stakeholder deck digests | CaaS role / legacy assignment context |
>
> Re-verify sources 5–9 on every run. The assignment master may be reused, but FY27 Customer stats must be queried again, and the roster / TPID mapping in the skill must be confirmed against the current master.

**Default execution order**:

0. **Prerequisite (completed by the user)**: run `asw-team-kpi-monthly` in Cowork (KPI + IR Missed), then copy the generated xlsx / optional json to `C:\GitHubCopilot\IronMan\Output\Cowork\`.
1. This Agent reads the latest `asw_kpi_by_month_FY*.xlsx` from `Output/Cowork/` → all Dashboard 1 KPIs.
2. This Agent reads the latest `asw_ir_missed_FY*.xlsx` from `Output/Cowork/` → IR Missing details (including Verbatim and SE Manager).
3. Open Dashboard 2 (using external Edge + Playwright MCP), verify the Staff Group Filter, wait **2 minutes**, then extract OpEx Metric Trend View data.
4. Submit the CPE Survey Kusto Query (`mcp_kusto_kusto_query`) to query the **entire current FY** (for example, FY2027 = `datetime(2026-07-01) ~ datetime(2027-06-01)`).

**Additional steps for the standalone US / Costa Rica + CaaS report**:

5. Use the fixed 13-person roster to generate the FY26 / FY27 latest-owner case sets from Snapshot Tables 2 / 3, respectively.
6. Join the KPI table by `IncidentId` to produce Engineer metrics; retain members without an ownership match as `No data`.
7. Read the CaaS `FOCUS` + legacy assignments and resolve all Customer TPIDs. If RISE Selected TPID is empty, resolve it in Kusto using the Customer name, but label the mapping as a live resolution.
8. Query each Customer's FY27 portfolio stats + Lead-owned cases + Top L2/L3, and de-duplicate shared Customers at the unique-customer level.
9. Produce 4-tab HTML and verify each tab in a browser, including at least one Engineer drill-down and the CaaS Customer drill-down.

**Fallback steps (run only if Cowork files are missing, and only after receiving user direction)**:
1. Open Dashboard 1 (Edge), **perform the four Filter validations strictly in order** (① Channel=ASW_SAPEpicEsc → ② LastTwelveMonths=(All) → ③ LastSixMonths=(All) → ④ FY=current fiscal year only); after confirming all restatements are correct, wait **2 minutes** before extracting data.
2. Open the IR Missed Reasons Dashboard (Edge), **perform the four Filter validations strictly in order** (⚠️ **order is critical**: ① Channel=ASW_SAPEpicEsc → ② LastTwelveMonths=(All) → ③ **clear LastSixMonths first** (default is `is Yes`; clear it to `is (All)`) → ④ **set FY last**, to current fiscal year only), set the Slicer, wait **2 minutes**, then extract the IR Missing Case ID list. **Verify that case months cover the entire FY (starting in Jul) and that `scrollHeight ≥ 25000px`.**
3. Run a Kusto Query using the IR Missing Case ID list (to supplement fields unavailable in the Dashboard, such as AgentName and Region).

### Step 2 — Organize Content
Organize the raw data into structured report content and perform an initial Business Analysis.

### Step 3 — Generate HTML
Output the data and analysis as an HTML report and save it to the specified path.

### Step 4 — Create Slides (Optional)
Use the `ppt_creator` skill to convert the report content into a Monthly Review presentation.

---

## Known Issues & Lessons Learned

### PBI Filter Pane Interaction Limitations

| Severity | Issue | Description | Resolution |
|--------|------|------|------|
| 🚨 **P0** | **Time Fiscal Year bookmark defaults to including the previous fiscal year** | After the Dashboard 1 and IR Missed Reasons bookmarks load, the `Time Fiscal Year` restatement usually includes both the current and previous fiscal years (for example, in an FY2027 environment it shows `is FY 2027 or FY 2026`). **If not corrected to the current fiscal year only, Total/YTD data will include the previous fiscal year and all cumulative values will be wrong.** | **Must** expand the Filter Card → deselect the previous fiscal year → confirm the restatement shows only the current fiscal year (for example, `is FY2027`). If expansion fails, use Clear filter and reselect the current fiscal year. This is a P0-priority operation. |
| 🚨 **P0** | **LastSixMonths defaults to `is Yes`** | The `Time LastSixMonths` filter card on Dashboard 1 and IR Missed Reasons defaults to `is Yes`, so data covers only the past 6 months rather than the full fiscal year. **If not cleared, 40-50% of cases will be missed.** | Following the Filter validation order, click the Clear filter button in Step 3c to clear this filter (`[aria-label="Clear filter"]`), then confirm the restatement becomes `is (All)`. Verify `scrollHeight ≥ 25000px` afterwards. |
| ⚠️ P1 | **Filter Card cannot be expanded** | On the IR Drill page's "Filters on all pages", clicking the expand button (`aria-expanded="false"`) for some Filter Cards does not expand their contents, so their internal checkboxes cannot be operated directly. | Use **Clear filter (eraser button)** to reset to `is (All)`, or filter using the **Slicer on the page**. |
| ℹ️ P2 | **Clear filter button state** | The Clear filter button has two states: `aria-disabled="false"` (clickable) and `disabled="" aria-disabled="true"` (already All; no action needed). | Check the `aria-disabled` property before deciding whether to click. |

### PBI Slicer Interaction Tips

| Issue | Description | Resolution |
|------|------|------|
| **🚨 P0: All standard clicks on the Show/hide filter pane button fail** | Playwright `click()` on the PBI top-right `button[aria-label="Show/hide filter pane"]` is intercepted by the outer CES BI Hub Angular `<div class="toggleBtn" data-testid="filter-btn">` overlay (`subtree intercepts pointer events`); `click({force:true})` and `focus() + keyboard.press('Enter')` produce no errors, but `aria-expanded` does not become `true`. | **Use coordinate clicks with `page.mouse`** (the only reliable method tested in 2026-07):<br><code>const box = await btn.boundingBox();</code><br><code>await page.mouse.move(box.x + box.width/2, box.y + box.height/2);</code><br><code>await page.waitForTimeout(150);</code><br><code>await page.mouse.down();</code><br><code>await page.waitForTimeout(50);</code><br><code>await page.mouse.up();</code><br>The same pattern applies to the Filter Card **Clear filter button**, **Expand/collapse button**, and expanded **checkboxes**. Always run `await loc.scrollIntoViewIfNeeded()` before clicking; otherwise, `boundingBox` reports the original coordinates inside the filter pane's scroll container (which may be outside the viewport), and mouse clicks will miss. |
| **Virtualized checkboxes inside a Filter Card prevent direct targeting of the desired value** | Checkboxes in an expanded Filter Card use virtual scrolling; for example, Time Fiscal Year renders only a few values near FY 2007–2013. A direct lookup of `[role="checkbox"][title="FY 2027"]` returns count=0, and `scrollIntoViewIfNeeded` cannot make it appear (the element is not in the DOM). | **First filter the list using the Filter Card's built-in Search box**:<br>1. Find `input[placeholder="Search"]` inside the filter card.<br>2. Focus it with a coordinate mouse click → `await search.pressSequentially('FY 2027', { delay: 80 })` (`fill()` does not work).<br>3. The target checkbox appears after Search filters the list; select it using `boundingBox` + mouse.down/up.<br>Use exactly the same process to select `ASW_SAPEpicEsc` in Channel Function Detail. |
| **`fill()` does not work in the Slicer search box** | Entering text into the PBI Slicer search box with `fill()` or `type()` does not trigger a filter update. | Type character by character using `pressSequentially('ASW_SAP', { delay: 80-100 })` to simulate manual typing and trigger PBI's key handler. |
| **Checkbox aria-label is null** | A checkbox in an expanded Filter Card may have a null `aria-label`; its text is actually in the `title` property or child `.slicerText` element. | Identify the target item using `[role="checkbox"][title="FY 2027"]` or read its `title` property. |

### PBI Grid Virtual Scrolling

| Issue | Description | Resolution |
|------|------|------|
| **Grid renders only visible rows** | PBI tables use virtual scrolling, rendering only about 20 rows at a time; the remaining rows are not in the DOM. | Scroll the `.mid-viewport` div incrementally (400px each time, 300ms intervals), collect visible rows at each position, and de-duplicate with a `Set`. |
| **Grid renders only visible columns (horizontal virtual scrolling)** | When a PBI table has more columns than fit in the visible width (for example, only 10 of 13 columns are visible), hidden columns are not rendered in the DOM. Setting `scrollLeft` in code or using CSS scroll does not trigger PBI's virtual column rendering. | **Trigger horizontal scrolling over the Grid with `page.mouse.wheel(deltaX, 0)`**. Steps: ① get the grid's `boundingBox()` ② `page.mouse.move(box.x + box.width/2, box.y + box.height - 20)` to move to the bottom scrollbar area ③ `page.mouse.wheel(300, 0)` to scroll right (negative values scroll left) ④ wait 2 seconds, then read the newly rendered columns. **Read in two passes**: first the left side (Jul-Apr), then wheel right to read May + Total. |
| **scrollHeight changes with data volume** | The scrollHeight for full-year data (`LastSixMonths = All`) is about twice that of six months of data (for example, 33966 vs 17000). | Use `scrollHeight` to calculate the required number of scrolls to ensure all rows are covered. |

### Kusto Data Notes

| Issue | Description | Resolution |
|------|------|------|
| **🚨 Use the Kusto MCP tool** | Execute Kusto queries **directly with the `mcp_kusto_kusto_query` MCP tool**; Azure CLI authentication (`az login`) or the `kusto_runner.py` script is not required. The MCP tool is fully authenticated and can execute queries by passing the three parameters cluster_uri, database, and query. | Call `mcp_kusto_kusto_query` directly, specifying `cluster_uri="https://supportrptwus3prod.westus3.kusto.windows.net"`, `database="KPISupportData"`, and `query="..."`. |
| **`IsIrMet` field is empty** | In the Kusto `AllCloudsSupportIncidentWithReferenceModelVNext` table, the `IsIrMet` field is an empty string (`""`) for all records after FY2026, so it cannot be used to determine IR Missing status. | IR Missing status is **calculated by the PBI Model** (based on whether `InitialResponseDateTime` is null); Case IDs must be extracted from the Dashboard, not filtered directly in Kusto. |
| **InitialSeverity values** | Most cases have `A` / `B` / `C`, but nonstandard values such as `1` occasionally appear. | Display the raw value in the HTML report without converting it. |
| **TTMS and Severity relationship** | TTMS is usually `null` for Sev B/C cases (no SLA requirement). | Display `-` (gray) in HTML when TTMS is null. |

### PBI iframe Structure

```
Page (cesbihub.microsoft.com)                                       ← top document
  ├─ (Angular) outer wrapper (contains `<div data-testid="filter-btn">` overlay)
  ├─ iframe name="exportiFrame" src="about:blank"                    ← same-origin
  ├─ iframe name="refreshAccessTokenIframe" (cesbihub.microsoft.com) ← same-origin
  └─ iframe name="reportPageiFrame" src="about:blank"                ← same-origin, but contains PBI
       └─ iframe src="https://msit.powerbi.com/reportEmbed?..."      ← CROSS-ORIGIN; the actual PBI content is here
```

#### 🚨 P0: PBI content is in a Cross-Origin iframe — top-level `document.querySelector` cannot reach inside it

- CES BI Hub embeds the PBI report in an `msit.powerbi.com/reportEmbed` iframe, which is **cross-origin** relative to the top-level page. Therefore:
  - `document.querySelector('[data-testid="filter-btn"]')` or `button[aria-label="Show/hide filter pane"]` always returns `null` from the top-level document.
  - Accessing the PBI iframe's `contentDocument` from the top-level document is blocked by SOP (returns `null`).
  - `mcp_playwright_browser_evaluate` (running at the top level) **cannot** cross into the PBI frame to manipulate the DOM.
- **Correct approach**: use `mcp_playwright_browser_run_code_unsafe` to run Playwright's own frame API (Playwright can internally access all frames across origins):
  ```js
  async () => {
    const pbi = page.frames().find(f => f.url().includes('powerbi.com/reportEmbed'));
    if (!pbi) return { err: 'no pbi frame' };
    // Attach all subsequent locators to pbi, for example:
    const cards = await pbi.locator('[data-automation-type="filterCard"]').all();
    // Or search for the filter title:
    const fy = pbi.locator('[data-automation-type="filterCard"]').filter({
      has: pbi.locator('[data-testid="filter-card-title"][aria-label^="Time Fiscal Year"]')
    }).first();
    return { count: cards.length };
  }
  ```
  **Note**: `mcp_playwright_browser_run_code_unsafe` accepts only async arrow functions or expressions, not top-level `const` declarations; it must be wrapped in `async () => { ... }`.
- **Prohibited**: do not locate the PBI frame by index using a pattern such as `page.frames()[4]` — the index can change with CES BI Hub versions or load timing. Always use `find(f => f.url().includes('powerbi.com/reportEmbed'))`.

#### Common Locator Patterns

- **Filter Card locator**: `pbiFrame.locator('[data-automation-type="filterCard"]')` gets all filter cards; identify the desired filter using the `aria-label` property of `[data-testid="filter-card-title"]`.
- **Restatement text**: `[data-testid="filter-card-restatement"]` gets the description of the filter's current setting.
- **Expand/collapse button**: `pbi.locator('[aria-label="Time Fiscal Year Expand or collapse filter card"]')` (replace with the filter name).
- **Clear filter button**: `[aria-label="Clear filter"]` inside the card.
- **Search input**: `input[placeholder="Search"]` inside the card.
- **Checkbox**: `pbi.locator('[role="checkbox"][title="FY 2027"]')` (appears only after Search filters the virtualized list).
