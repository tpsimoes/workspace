---
name: review-reporter
description: "準備 Monthly Review Meeting 所需的報告內容：KPI 數據收集（CSAT、IR、Case Volume、Day to Close）、Highlight / Lowlight 整理、Customer Support Story、Executive Escalation 摘要。當用戶提到「monthly review」「月報」「KPI」「CSAT」「highlight lowlight」「executive escalation」「向主管報告」時觸發。"
---

# Skill: Review Reporter

## 報告結構

Monthly Review 報告包含以下區塊：

### 1. KPI Dashboard Summary

> **執行順序**：(1) Filter 驗證 → (2) 等待 Data Refresh → (3) 資料擷取。三步驟必須依序完成，不可跳步。若 Dashboard 無法存取，通知用戶並詢問是否使用上次匯出的資料。

需收集的指標：

| KPI | 說明 | 來源 |
|-----|------|------|
| CSAT | 客戶滿意度評分 | Survey Dashboard |
| IR (Initial Response) | 首次回應時間 | Case Management System |
| Case Volume | 案件數量（開 / 關 / 進行中） | Case Management System |
| Day to Close | 平均結案天數 | Case Management System |
| Backlog | 待處理案件數 | Case Management System |

產出格式：表格 + 月趨勢（與上月對比 ↑↓）

### 2. Highlight / Lowlight

**Highlight**（本月亮點）：
- 重大客戶問題成功解決
- 團隊成員突出表現
- 流程改善成果
- 跨團隊協作成功案例

**Lowlight**（需關注事項）：
- KPI 未達標項目及原因分析
- 人力 / 資源瓶頸
- 需主管協助排除的障礙

### 3. Customer Support Story

- 挑選本月最具代表性的 1-2 個支援案例
- 結構：問題背景 → 挑戰 → 行動 → 結果 → 客戶回饋

### 4. Executive Escalation

若本月有 Executive Escalation，需特別報告：
- 案例摘要（客戶、問題、影響範圍）
- 當前狀態 / 解決方案
- Lessons Learned

---

## Dashboard 資料收集規範

### 資料取得方式（Method Selection）

MOR 各資料源採用不同的取得方式，職責明確劃分：

| # | 資料源 | 用途 | 取得方式 | 執行者 |
|---|--------|------|---------|--------|
| 1 | **Commercial Insights+ V2 Semantic Model** | 19 KPI（Dashboard 1：Quality + Operational Metrics） | Cowork `asw-team-kpi-monthly` skill 透過 Fabric AI Hub MCP 執行 DAX | **Cowork** |
| 2 | **Commercial Insights+ V2**（IR Missed subset） | IR Missing 案件明細（含 Time to IR、Verbatim、SE Manager） | Cowork `asw-team-kpi-monthly` skill 的 IR Missed pattern | **Cowork** |
| 3 | **OpEx Overall PCY Level A&I+DTP**（Power BI msit） | 5 個 OpEx Metrics（Case Assignment / Backlog） | Playwright + 外部 Edge（本 SKILL Step 1B） | **本 Agent** |
| 4 | **Kusto — CPE Survey** | CPE Insight 資料（CSAT、Verbatim、AgentName） | Kusto MCP（`mcp_kusto_kusto_query`） | **本 Agent** |

> **為何 Dashboard 1 / IR Missing 交給 Cowork**：`Commercial Insights+ V2 Dataset` 位於 `CESBIDataset_Commercial_PROD` workspace，個人 `az login` identity（`jacobw@microsoft.com`）目前無 Build permission，直接呼叫 Power BI REST API `executeQueries` 會回 `PowerBIEntityNotFound`。Cowork 的 `pbi_fabricaihub` MCP 使用特權服務主體，可跨租戶讀取，執行速度 30–60 秒（相對 Playwright 10–15 分鐘）。若未來個人取得 Build permission、或 VS Code Copilot 接入 Fabric AI Hub MCP，可再考慮把 Cowork 的角色收回本 Agent。

---

### 方式 A：Cowork 資料匯入（Dashboard 1 + IR Missing）

**執行流程**（每次 MOR 前置作業）：

1. 在 Cowork 執行以下兩個指令（由用戶操作）：
   ```
   Cowork > 執行 asw-team-kpi-monthly，FY<current>，輸出 KPI by Month
   Cowork > 執行 asw-team-kpi-monthly，FY<current>，輸出 IR Missed cases
   ```
2. Cowork 產出的 `.xlsx` + 對應 `.json`（若有）**由用戶複製到** `C:\GitHubCopilot\IronMan\Output\Cowork\`
3. 本 Agent 讀取該資料夾內最新檔案，直接組成報告；**不需再開啟 Dashboard 1 / IR Missed Reasons Dashboard**

**檔案落地契約（Cowork Intake Contract）**：

| 檔名（Glob） | 內容 | 讀取方式 |
|--------------|------|---------|
| `Output/Cowork/asw_kpi_by_month_FY*.xlsx` | 單一 sheet `KPI by Month`，19 個 KPI 欄位 + 每 FM 一列 | `openpyxl` / `pandas.read_excel` |
| `Output/Cowork/asw_kpi_by_month_FY*.json`（optional） | Cowork DAX runner 原始輸出（`meta` + `rows`） | `json.load` |
| `Output/Cowork/asw_ir_missed_FY*.xlsx` | 4 sheets：`FY<NN> IR Missed`、`By Customer`、`By Owner`、`By Severity` | `openpyxl` / `pandas.read_excel` |
| `Output/Cowork/asw_ir_missed_FY*.json`（optional） | 3-query merged JSON（dims + verbatim + owner_manager map） | `json.load` |

**選檔規則**：同一 FY 若有多個時間戳版本，**取檔名字典序最大者**（Cowork 檔名慣例通常帶 `_YYYYMMDD`）；若 xlsx 與 json 並存，優先讀 xlsx（欄位語意經 Cowork 標準化）。

**Sheet / 欄位對應**：

*`KPI by Month` 表* → 直接對到 SKILL 中「Dashboard 1 — Quality Metrics 表格」+「Operational Metrics 表格」，欄位順序與命名已在 Cowork skill 定義完成（見 Cowork `asw-team-kpi-monthly` SKILL 的 19 KPI 表）；本 Agent 不需重新映射，只需依照當前 FY 由 Jul 起讀取直到最新有值的月份。

*`FY<NN> IR Missed` 表*（12 欄）：`SR ID | Customer | Service | SR Owner | SE Manager | Initial Severity | Region | Created Date | Closed Date | Time to IR (mins) | CSAT | Verbatim`

| SKILL 中 HTML 欄位 | Cowork 欄位 | 備註 |
|-------------------|-------------|------|
| Case ID | `SR ID` | 以 TEXT 保存 16 位數字 |
| Customer | `Customer` | 已為 Top Parent Organization Name |
| Service | `Service` | Service Offering Master name |
| SE Manager | `SE Manager` | Cowork 已完成 owner alias → manager email 查詢 |
| Created | `Created Date` | 顯示 `yyyy-mm-dd` |
| Closed | `Closed Date` | 同上 |
| Initial Severity | `Initial Severity` | `A`/`B`/`C`（Sev A 紅色加粗） |
| TTMS (mins) | `Time to IR (mins)` | **注意語意**：此為總分鐘數，非 over-SLA；顯示時附註 `data as reported by Power BI` |
| Region | `Region` | Customer Region |

> **重要語意提醒**：Cowork 產出的 `Time to IR (mins)` 就是原 SKILL 沿用的 `TTMS` 欄位語意（Time To Meet SLA 分鐘數），但 Semantic Model 沒有 SLA target 資料，因此此值**是原始 IR 分鐘數，非「超過 SLA 的分鐘數」**。IR Missing Insight 頁面 Footer 需附註：`Time to IR reflects total minutes to initial response; SLA overage cannot be computed from the source model.`

**Fallback 觸發條件**：

當任一情況發生時，改走方式 B（Playwright）：

1. `Output/Cowork/asw_kpi_by_month_FY*.xlsx` 不存在或超過 30 天
2. Cowork 檔案存在但 KPI 欄位缺失（例：新增 KPI 未同步、欄名不符）
3. 用戶指示「重新從 Dashboard 拉」

---

### 方式 B（Fallback）：Playwright + CES BI Hub

> **何時使用**：Cowork 資料不可用時。以下所有 Filter 驗證、Iframe 操作、2 分鐘等待步驟**只有在採用方式 B 時**才需執行；使用方式 A 時可**完全略過**。

### Dashboard 1: CSS - A&I and DTP（Playwright）

| 項目 | 內容 |
|------|------|
| **名稱** | CSS - A&I and DTP |
| **平台** | CES BI Hub |
| **URL** | https://cesbihub.microsoft.com/User/groups/10/report/81538463-21f0-45bc-8f08-71d5dc9ccc48/0/0?reportTab=ReportSectiond24dca6cf2e742181ba9 |
| **必要 Filter** | Channel Function Detail = **ASW_SAPEpicEsc**（見下方 Filter 驗證 Checklist） |
| **Refresh 等待** | 點選 Filter 後等待 **2 分鐘** 再擷取資料 |

#### Filter 驗證 Checklist（每次必做，嚴格依照以下順序執行）

> **📅 當前財年（Current Fiscal Year）**：依報告執行日期動態判定；若日期落在 **7/1（含）之後**，即進入下一個 Microsoft Fiscal Year。以目前 MOR 執行日 2026/7/1 之後為例，當前財年為 **FY2027**（Jul 2026 – Jun 2027）。
>
> 微軟財年規則：FY 起始月為每年 **7 月 1 日**，結束於次年 6 月 30 日。財年編號以結束年為準（例：FY2027 = 2026/7/1 – 2027/6/30）。**每年 7/1 起，MOR 的 `Time Fiscal Year` filter 必須切換至新的財年**。因此 2026/7/1 起需選 **FY2027**，不可沿用 FY2026 或同時包含 FY2026。

進入 Dashboard 1 後，**依序**完成以下 4 項驗證：

1. ✅ **Channel Function Detail** → 顯示 `is ASW_SAPEpicEsc`
2. ✅ **Time LastTwelveMonths** → 顯示 `is (All)`（全部 checkbox 不勾選）
3. ✅ **Time LastSixMonths** → 顯示 `is (All)`（全部 checkbox 不勾選）
4. ✅ **Time Fiscal Year** → 顯示 `is FY2027`（僅當前財年，不可包含 FY2026）

若任一項不符，修正後等待 2 分鐘再擷取資料。

#### 收集 KPI 清單（19 項）

| # | KPI | 表格位置 | Target | Direction |
|---|-----|---------|--------|----------|
| 1 | CSAT 5 * Avg | Key Metrics by Date (上方表格) | ≥ 4.8 | High Good |
| 2 | DSAT | Key Metrics by Date (上方表格) | < 2% | Low Good |
| 3 | CSAT Surveys | Key Metrics by Date (上方表格) | - | - |
| 4 | CSAT Response Rate | Key Metrics by Date (上方表格) | - | - |
| 5 | % CritSit | Key Metrics by Date (上方表格) | - | - |
| 6 | % IR Met | Key Metrics by Date (上方表格) | ≥ 99% | High Good |
| 7 | IPD Created | Key Metrics by Date (下方表格) | vs Total | High Good |
| 8 | IPD Closed | Key Metrics by Date (下方表格) | - | - |
| 9 | Open Cases | Key Metrics by Date (下方表格) | - | - |
| 10 | Created Cases | Key Metrics by Date (下方表格) | - | - |
| 11 | Closed Cases | Key Metrics by Date (下方表格) | - | - |
| 12 | CSS TMPI | Key Metrics by Date (下方表格) | - | - |
| 13 | Avg DTC | Key Metrics by Date (下方表格) | ≤ 12 days | Low Good |
| 14 | Backlog Count | Key Metrics by Date (下方表格) | - | - |
| 15 | Backlog DtC | Key Metrics by Date (下方表格) | - | - |
| 16 | Collaboration Tasks | Key Metrics by Date (下方表格) | - | - |
| 17 | Post IR Transfer % | Key Metrics by Date (下方表格) | - | - |
| 18 | % Transfer | Key Metrics by Date (下方表格) | - | - |
| 19 | % SR Closed in less than 7 Days | Key Metrics by Date (下方表格) | ≥ 50% | High Good |

#### 操作步驟

> **🚨 CRITICAL — Filter 設定為 BLOCKING 步驟，必須在擷取任何資料前完成所有 4 項驗證。**

1. 開啟 URL（bookmark 已含部分 Filter 設定）
2. 等待 PBI iframe 載入完成（`[role="grid"]` 出現）
3. **【BLOCKING】依序執行 Filter 驗證 Checklist（4 項全部通過才可繼續）：**

   **Step 3a — Channel Function Detail**
   - 確認 restatement 顯示 `is ASW_SAPEpicEsc`
   - 若不符：點擊 Filter Card restatement 展開 → 選取 `ASW_SAPEpicEsc`

   **Step 3b — Time LastTwelveMonths**
   - 確認 restatement 顯示 `is (All)`
   - 若不符：點擊 Clear filter 按鈕（`[aria-label="Clear filter"]`）清除

   **Step 3c — Time LastSixMonths**
   - 確認 restatement 顯示 `is (All)`
   - 若不符：點擊 Clear filter 按鈕（`[aria-label="Clear filter"]`）清除

   **Step 3d — Time Fiscal Year（⚠️ Bookmark 預設可能為 `FY 2027 or FY 2026`，必須手動修正）**
   - 確認 restatement **僅顯示** `is FY2027`（不可包含 FY2026）
   - Bookmark 載入後 restatement 通常為 `is FY 2027 or FY 2026`，**此為未通過狀態**
   - **修正操作**：
     1. 先點擊 Clear filter（橡皮擦按鈕 `[aria-label="Clear filter"]`）清除現有選擇
     2. 點擊 `Time Fiscal Year` filter card 的展開按鈕（`aria-label="Time Fiscal Year Expand or collapse filter card"`）展開該 Filter Card
     3. 展開後找到 checkbox 清單，勾選 `FY 2027`（確認 `aria-checked="true"`）
     4. 確認不勾選 `FY 2026`（若可見，確認 `aria-checked="false"`）
   - **驗證**：restatement 變為 `is FY2027`（不含 `or FY 2026`）

4. **【BLOCKING】Filter 變更後，等待 2 分鐘（120 秒）** 讓資料完成 Data Refresh
   - 使用 `page.waitForTimeout(120000)` 或等效方式
   - **禁止在等待時間內擷取任何資料**
5. 從 Power BI iframe 中擷取「Key Metrics by Date」兩張表格的**整個 FY 年度數據**
6. 收集每個 KPI 的 FM Jul 起至當前月份的所有數值及 Total
   - 微軟 Fiscal Year 為 Jul ~ Jun（FY 2027 = FM Jul 2026 ~ FM Jun 2027）
   - 年度尚未結束時，資料僅會到當前月份（例：2026 年 7 月時僅有 Jul 共 1 個月；2027 年 5 月時僅有 Jul ~ May 共 11 個月）
   - Total 為已有月份的累計值，非完整 12 個月
   - **Total 欄位即為 FY2027 YTD 值**（因 Filter 僅選 FY2027，Total = 當前財年累計）

---

### Dashboard 2: OpEx Overall PCY Level

| 項目 | 內容 |
|------|------|
| **名稱** | OpEx Overall PCY Level A&I+DTP |
| **平台** | Power BI (msit.powerbi.com) |
| **URL** | https://msit.powerbi.com/groups/me/reports/97cef847-3bf0-445c-b4b6-5e4f7e29fc8d/238752830e2a8090a3ca?experience=power-bi |
| **必要 Filter** | Staff Group 僅選擇 **A&I-Azure-ASW Epic and SAP**（不可多選） |
| **Refresh 等待** | 確認 Filter 後等待 **2 分鐘** 再擷取資料 |
| **備註** | 此 Dashboard 預設僅顯示過去六個月數據，無需額外設定時間 Filter |

#### 收集 KPI 清單（5 項，來自 Metric Trend View 表格）

| # | KPI | Category | Target |
|---|-----|----------|--------|
| 1 | % Hours out of Queue (WFM + VDM) | Case Assignment | ≤ 4.0% (Low Good) |
| 2 | Accept Rate (WFM + VDM) | Case Assignment | ≥ 1.8 (High Good) |
| 3 | % Case Assignment >= 1 | Case Assignment | ≥ 85.0% (High Good) |
| 4 | Quick Ownership Change % (0-15 Mins) | Case Assignment | ≤ 2.0% (Low Good) |
| 5 | % Cases Closed within 7 days | Backlog Management | ≥ 50.0% |

#### 操作步驟

1. 開啟 URL
2. 若出現帳號選擇頁面，選擇 `jacobw@microsoft.com`
3. **【必要】** 確認左側 Staff Group 下拉選單**僅選擇** `A&I-Azure-ASW Epic and SAP`
   - **點選方式**：找到 Slicer 中 class 為 `slicerText` 的 `<span>` 元素，文字內容為 `A&I-Azure-ASW Epic and SAP`，確認該項目為唯一勾選項目；若有其他項目被勾選，需先取消再僅保留此項
4. 確認 Filter 後，等待 **2 分鐘** 讓資料完成 Data Refresh，再執行 KPI 資料擷取
5. 找到頁面下方「Metric Trend View」表格
6. 擷取 5 項 KPI 的過去六個月數據（Dashboard 預設顯示範圍）

---

## 輸出規範

### HTML 報告格式

- **儲存位置**：`C:\GitHubCopilot\IronMan\Output\monthly_review_{month}{year}.html`
- **時區標示**：表頭日期與時間使用 **UTC+8**，格式為 `YYYY-MM-DD HH:MM (UTC+8)`
- **分頁結構**：HTML 報告採用 Tab 分頁設計，包含以下頁籤：

| Tab | 名稱 | 內容 |
|-----|------|------|
| 主頁 | MOR Summary Report | KPI Dashboard 摘要、趨勢表格、MoM Summary、Business Analysis |
| 分頁 1 | CPE Insight | 所有 Survey Case 明細，依 AgentAlias 分組（來源：Kusto Query） |
| 分頁 2 | IR Missing Insight | 當前財年 IR Missing 案件明細（來源：Dashboard IR Missed Reasons + Kusto Query） |

#### MOR Summary Report 頁面結構
  1. Executive Summary Cards（關鍵 KPI 快照，數值顯示該 KPI 的**年度累計 Total**，並顯示 MoM 變化箭頭）
  2. Business Analysis（Highlights / Lowlights / Recommendations）
  3. Dashboard 1 表格（Quality Metrics + Operational Metrics，含完整 FY 年度趨勢，有 Target 的 KPI 顯示 🟢🟡🔴 燈號）
  4. Dashboard 2 表格（Actuals vs Targets + Metric Trend View 過去 6 個月趨勢）
  5. Month-over-Month Summary（上月 vs 當月，含 Change 與 Trend 方向）

#### Executive Summary Cards 清單（9 項）

| # | Card 名稱 | 來源 | Status 判定 |
|---|-----------|------|-------------|
| 1 | CSAT 5★ Avg | Dashboard 1 — Key Metrics by Date (上方) | ≥ 4.5 Green / ≥ 4.0 Yellow / < 4.0 Red |
| 2 | % IR Met | Dashboard 1 — Key Metrics by Date (上方) | ≥ 95% Green / ≥ 90% Yellow / < 90% Red |
| 3 | Created Cases | Dashboard 1 — Key Metrics by Date (下方) | 純資訊，無 Status |
| 4 | Closed Cases | Dashboard 1 — Key Metrics by Date (下方) | 純資訊，無 Status |
| 5 | Avg DTC | Dashboard 1 — Key Metrics by Date (下方) | ≤ 10 Green / ≤ 15 Yellow / > 15 Red |
| 6 | % CritSit | Dashboard 1 — Key Metrics by Date (上方) | ≤ 15% Green / ≤ 20% Yellow / > 20% Red |
| 7 | DSAT | Dashboard 1 — Key Metrics by Date (上方) | ≤ 1% Green / ≤ 2% Yellow / > 2% Red |
| 8 | % Cases Closed within 7 days | **Dashboard 2** — Actuals \|\| Benchmarks \|\| Variance 表格 | ≥ 50% Green / ≥ 40% Yellow / < 40% Red |
| 9 | Post IR Transfer % | Dashboard 1 — Key Metrics by Date (下方) | ≤ 20% Green / ≤ 25% Yellow / > 25% Red |

> **注意**：`% Cases Closed within 7 days` 是唯一來自 Dashboard 2 的 Executive Summary Card。  
> 數值取自 Dashboard 2「Actuals || Benchmarks || Variance」矩陣表格中  
> `% Cases Closed within 7 days` 列的 **Actual Value** 欄位，Target 為 **50.0%**。

#### Executive Summary Cards — MoM Change 顯示規則

每張 Card 底部的 `.trend` 區域顯示**當月 vs 上月的變化**，格式為：`{箭頭} {±數值} vs {上月名}`

- **箭頭方向**：`↑` = 數值上升、`↓` = 數值下降、`→` = 持平
- **箭頭顏色**（依 KPI Direction 判定改善/惡化）：
  - **High Good**（CSAT、% IR Met、Created/Closed Cases、% Closed ≤7d）：↑ 綠色 = 改善、↓ 紅色 = 惡化
  - **Low Good**（Avg DTC、% CritSit、DSAT、Post IR Transfer %）：↓ 綠色 = 改善、↑ 紅色 = 惡化
  - **純資訊**（Created Cases、Closed Cases）：箭頭使用灰色（`#6b7280`），不判定好壞
- **變化值格式**：`+X.X` 或 `-X.X`（浮點）、`+N` 或 `-N`（整數）
- **範例**：`<span style="color:#dc3545;font-weight:600;">↑ +4.1</span> <span style="color:#94a3b8;">vs Apr</span>`

#### MoM Change 對應數據（需每月更新）

| # | Card 名稱 | Direction | 計算方式 |
|---|-----------|-----------|----------|
| 1 | CSAT 5★ Avg | high | 當月 CSAT - 上月 CSAT |
| 2 | % IR Met | high | 當月 % - 上月 % |
| 3 | Created Cases | neutral | 當月 - 上月 |
| 4 | Closed Cases | neutral | 當月 - 上月 |
| 5 | Avg DTC | low | 當月 - 上月 |
| 6 | % CritSit | low | 當月 % - 上月 % |
| 7 | DSAT | low | 當月 % - 上月 %（若無數據則 0） |
| 8 | % Closed ≤7d | high | 當月 % - 上月 % |
| 9 | Post IR Transfer % | low | 當月 % - 上月 % |



#### Business Analysis 規則

Business Analysis 區塊位於 **Executive Summary Cards 與 Dashboard 1 表格之間**，以 Business Owner 視角提供 KPI 洞察。

##### 結構

```html
<div class="analysis-grid">
    <div class="analysis-box highlight-box"><h4>🟢 Highlights</h4><ul>...</ul></div>
    <div class="analysis-box lowlight-box"><h4>🔴 Lowlights / Areas of Concern</h4><ul>...</ul></div>
    <div class="analysis-box recommend-box" style="grid-column: span 2;"><h4>💡 Recommendations</h4><ul>...</ul></div>
</div>
```

##### Highlight 判定規則（當月表現突出）

針對有 Target 的 KPI，當月值達標或超標時列為 Highlight：

| KPI | Highlight 條件 | 附加條件 |
|-----|----------------|----------|
| CSAT 5★ Avg | 當月 ≥ 4.8 | — |
| % IR Met | 當月 ≥ 99% | — |
| Avg DTC | 當月 ≤ 12 | — |
| % Cases Closed ≤7d | 當月 ≥ 50% | — |
| IPD Created | 當月 ≥ YTD Total (平均) | 或過去 3 個月呈上升趨勢 |

##### Lowlight 判定規則（當月需關注）

針對有 Target 的 KPI，當月值未達標或趨勢下滑時列為 Lowlight：

| KPI | Lowlight 條件 | 附加條件 |
|-----|---------------|----------|
| CSAT 5★ Avg | 當月 < 4.8 | 或過去 3 個月呈下滑趨勢 |
| % IR Met | 當月 < 99% | — |
| Avg DTC | 當月 > 12 | 或過去 3 個月呈上升趨勢 |
| % Cases Closed ≤7d | 當月 < 50% | 或過去 3 個月呈下滑趨勢 |
| IPD Created | 當月 < YTD Total (平均) | 或過去 3 個月呈下滑趨勢 |

- **趨勢判定**：取最近 3 個月（M-2, M-1, M），若連續 3 個月同方向移動或有明顯波動，標註趨勢
- **部分月數據**：若當月數據為部分月（月中報告），需加註 `⚠️ partial month data`

##### Recommendation 撰寫原則

- 以 **Business Owner** 視角撰寫，聚焦可執行的行動建議
- 針對每個 Lowlight KPI 提供對應建議
- 包含：根因調查方向、短期緩解措施、長期改善目標
- 對於持續達標的 KPI，建議維持現有做法並強化
- 格式：`<strong>{建議標題}</strong> — {具體說明}`

#### CPE Insight 頁面結構

- **資料來源**：Kusto Query（詳見 `kusto_query` Skill → `references/catalog-custom.md` §ASW CPE Survey）
- **Cluster**：`supportrptwus3prod.westus3.kusto.windows.net` / `KPISupportData`
- **團隊成員篩選**：透過 `ASWStakeholder` 表格 lookup `AgentAlias` 欄位，僅取 ASW 團隊成員的 Survey
- **排除名單**：已離開 ASW 的成員需排除，目前排除：`zhaobo`
- **時間範圍**：**整個當前 Fiscal Year（FY）**，以 `CreatedDateTime` 篩選 FY 起訖日期（例：FY2027 = `2026-07-01` ~ `2027-06-01`）。**不可僅取單月資料**，CPE Insight 頁面需完整呈現整年所有 Survey 記錄
- **資料條件**：`isnotempty(TotalCustomerSATScore)`（僅含有 CSAT 分數的案件）

##### Kusto Query

```kql
let ASWNames = cluster('bedrock.eastus.kusto.windows.net').database("CSI").ASWStakeholder
| where Role == "Engineer" | where BusinessUnit == "CSS-ASW"
| project AgentAlias, AgentName;
AllCloudsSupportIncidentWithReferenceModelVNext
| where CreatedDateTime >= datetime(_fy_start) and CreatedDateTime < datetime(_fy_end)
| where AgentAlias in (ASWNames | project AgentAlias)
| where AgentAlias !in ('zhaobo') // 已離開 ASW 的成員排除
| where isnotempty(TotalCustomerSATScore)
| lookup ASWNames on AgentAlias
| project IncidentId, Customer_TPName, ServiceName, ClosedDateTime, TotalCustomerSATScore, SurveyVerbatims, CreatedDateTime, AgentAlias, AgentName, Customer_TPID, RegionName
| order by ClosedDateTime desc
```

> **`_fy_start` / `_fy_end` 參數**：當前 Fiscal Year 的起訖日期。FY2027 = `2026-07-01` / `2027-06-01`。查詢涵蓋完整財年所有月份的 CPE Survey。

##### 輸出欄位（11 欄）

| # | 欄位名稱 | 說明 |
|---|----------|------|
| 1 | IncidentId | Case ID |
| 2 | Customer_TPName | 客戶名稱 |
| 3 | ServiceName | 服務 / 產品名稱 |
| 4 | ClosedDateTime | 結案日期時間 |
| 5 | TotalCustomerSATScore | CSAT 分數（1-5） |
| 6 | SurveyVerbatims | 客戶文字回饋 |
| 7 | CreatedDateTime | 案件建立日期時間 |
| 8 | AgentAlias | 工程師 Alias |
| 9 | AgentName | 工程師姓名（SE Name），來源：`ASWStakeholder` 表 |
| 10 | Customer_TPID | 客戶 TPID |
| 11 | RegionName | 客戶所在區域 |

##### 頁面呈現規則

- **表格方式**：所有 Survey 整合為單一表格（不分組）
- **欄位順序**：Case ID, Customer, Service, AgentAlias, SE Name, CSAT, Verbatim, Closed, Created, Region
- **預設排序**：依 `ClosedDateTime` 降序排列（最新日期在最上方）
- **可排序欄位**：**SE Name**（string）、**CSAT**（number）、**Closed**（date）三欄需加入前端排序功能，點擊欄位標頭可切換升冪/降冪
- **排序 UI**：欄位標頭顯示排序方向箭頭（↑升冪 / ↓降冪），hover 高亮，預設 Closed 欄標示為 `desc`
- **CSAT 分數標示**：5 = 🟢, 4 = 🟡, 1-3 = 🔴

#### IR Missing Insight 頁面結構

- **目的**：列出當前財年所有 IR Missing（Initial Response 未達標）的案件明細
- **資料來源**：
  1. **Dashboard（IR Missed Reasons）**：從 CES BI Hub 的「Service Request IR Missed Reasons」表格中，擷取 `Is IR Met = No` 的 Service Request Number
  2. **Kusto Query**：以擷取到的 Case ID 查詢案件詳細資訊

##### Dashboard: IR Missed Reasons（Playwright — fallback 專用）

> **預設來源為 Cowork 匯入檔**：`Output/Cowork/asw_ir_missed_FY*.xlsx`（方式 A）已含完整 IR Missing 明細（Time to IR、Verbatim、SE Manager），無需 Dashboard scroll。IR Missing 定義為 `'Service Request'[Is IR Met] = "No"`（來自 Semantic Model，非 Kusto 判定）。以下 Playwright 流程只在 Cowork 檔案不可用時採用。

| 項目 | 內容 |
|------|------|
| **名稱** | CSS - A&I and DTP（IR Missed Reasons 分頁） |
| **平台** | CES BI Hub |
| **URL** | `https://cesbihub.microsoft.com/User/groups/10/report/81538463-21f0-45bc-8f08-71d5dc9ccc48/0/0?reportTab=ReportSection157aebf13d4b20b43fc5` |
| **必要 Filter** | 與 Dashboard 1 相同：Channel Function Detail = `ASW_SAPEpicEsc`、Time Fiscal Year = 當前財年 |
| **Filter 驗證** | 參照下方「操作步驟」Step 3a-3d |

##### 操作步驟

> **🚨 CRITICAL — 以下 Filter 設定為 BLOCKING 步驟，必須全部完成且等待 2 分鐘後才可擷取資料。**

1. 開啟 URL（使用 Edge）
2. 等待 PBI iframe 載入完成
3. **【BLOCKING】依序執行 Filter 驗證 Checklist（4 項全部通過）：**

   **Step 3a — Channel Function Detail**
   - 確認 restatement 顯示 `is ASW_SAPEpicEsc`
   - 若不符：點擊 Filter Card restatement 展開 → 選取 `ASW_SAPEpicEsc`

   **Step 3b — Time LastTwelveMonths**
   - 確認 restatement 顯示 `is (All)`
   - 若不符：點擊 Clear filter 按鈕（`[aria-label="Clear filter"]`）清除

   **Step 3c — Time LastSixMonths（⚠️ 預設為 `is Yes`，必須清除）**
   - 點擊 Clear filter 按鈕（`[aria-label="Clear filter"]`）→ restatement 變為 `is (All)`
   - **若未清除將遺失 40-50% 案件**

   **Step 3d — Time Fiscal Year（⚠️ Bookmark 預設可能含前一財年，必須修正）**
   - 確認 restatement **僅顯示** `is FY2027`（不可包含 FY2026）
   - **修正操作**：
     1. 先點擊 Clear filter（橡皮擦按鈕 `[aria-label="Clear filter"]`）清除現有選擇
     2. 點擊展開按鈕（`aria-label="Time Fiscal Year Expand or collapse filter card"`）展開
     3. 勾選 `FY 2027`（確認 `aria-checked="true"`）
     4. 確認不勾選 `FY 2026`（若可見，確認 `aria-checked="false"`）
   - **驗證**：restatement 為 `is FY2027`（不含 `or FY 2026`）

4. **設定頁面 Slicer**（與 Filter Pane 不同，這是頁面上的篩選器）：
   1. Channel Function Detail Slicer → 搜尋 `ASW_SAP` → 勾選 `ASW_SAPEpicEsc`
   2. Fiscal Year Slicer → 僅勾選 `FY 2027`
5. **【BLOCKING】等待 2 分鐘（120 秒）** Data Refresh — `page.waitForTimeout(120000)`
6. **驗證 scrollHeight**：≥ 25000px 則繼續；< 18000px 則回步驟 3 重做
7. 找到「Service Request IR Missed Reasons」表格（`[role="grid"]`）
8. **點擊 `Is IR Met` 欄位標題排序**：讓 `No` 值浮到最上方（點擊一次升冪排序，`No` < `Yes` 所以 `No` 在前）
9. 透過 `.mid-viewport` div 逐步捲動（每次 400px）收集列，擷取 **Service Request Number**。當讀到的 `Is IR Met` 值從 `No` 變為 `Yes` 時即可停止，表示所有 IR Missing 案件已收集完畢
10. **結果驗證**：確認案件涵蓋 Jul 起各月份（非僅最近 6 個月）

##### Kusto Query

以 Dashboard 擷取到的 IR Missing Case ID 清單，查詢案件詳細資訊：

```kql
let ASWNames = cluster('bedrock.eastus.kusto.windows.net').database("CSI").ASWStakeholder
| where Role == "Engineer" | where BusinessUnit == "CSS-ASW"
| project AgentAlias, AgentName;
let IRMissingCases = dynamic([_caseIds]); // 從 Dashboard 擷取的 Case ID 清單
database('KPISupportData').AllCloudsSupportIncidentWithReferenceModelVNext
| where IncidentId in (IRMissingCases)
| lookup ASWNames on AgentAlias
| project IncidentId, Customer_TPName, ServiceName, AgentAlias, AgentName, CreatedDateTime, ClosedDateTime, InitialSeverity, TTMS, RegionName
| order by CreatedDateTime desc
```

> **`_caseIds` 參數**：從 Dashboard「Service Request IR Missed Reasons」表格中擷取的 IR Missing Case ID 清單，格式為 KQL dynamic array（例：`'2604010030001234', '2603150040005678'`）
> **注意**：Kusto 表中 `IsIrMet` 欄位為空字串，IR Missing 狀態由 Dashboard（PBI Model）計算判定。因此 Kusto Query 不需要 `| where IsIrMet == 'No'` 篩選條件，僅以 Dashboard 擷取到的 Case ID 為準。

##### 輸出欄位（10 欄）

| # | 欄位名稱 | 說明 |
|---|----------|------|
| 1 | IncidentId | Case ID |
| 2 | Customer_TPName | 客戶名稱 |
| 3 | ServiceName | 服務 / 產品名稱 |
| 4 | AgentAlias | 工程師 Alias |
| 5 | AgentName | 工程師姓名（SE Name） |
| 6 | CreatedDateTime | 案件建立日期 |
| 7 | ClosedDateTime | 結案日期 |
| 8 | InitialSeverity | 初始嚴重等級 |
| 9 | TTMS | Time To Meet SLA（分鐘） |
| 10 | RegionName | 客戶所在區域 |

##### 頁面呈現規則

- **表格方式**：所有 IR Missing 案件整合為單一表格
- **欄位順序**：Case ID, Customer, Service, SE Manager, Created, Closed, Initial Severity, TTMS, Region
- **隱藏欄位**：Agent（AgentAlias）、SE Name（AgentName）不顯示於表格中
- **SE Manager 欄位**：使用 `AGENT_MANAGER_MAP` 字典將 AgentAlias 對應到其 SE Manager 名稱（資料來源：`bedrock.CSI.ASWStakeholder` 表的 `Manager` 欄位）；未在 mapping 中的 agent 使用 `DEFAULT_SE_MANAGER` 預設值（`Unknown`）
- **排序**：依 `CreatedDateTime` 降序排列（最新日期在最上方）
- **版面佈局**：頁面上方為 flex 橫向排列（左欄 320px + 右欄 flex:1），左欄含 Summary Cards（2×2 grid）+ Avg TTMS by Severity 統計面板，右欄為 SVG 趨勢圖；下方為全寬資料表格

- **KPI Target 色彩標示規則**（適用於 Dashboard 1 有 Target 的 KPI）：
  - 🟢 = 達標（At or above Target）
  - 🟡 = 接近目標（Below Target but within 5% gap）
  - 🔴 = 未達標（More than 5% gap below Target）
  - 5% gap 計算方式：以 Target 值的 5% 為閾值（例：Target ≥ 4.8，5% = 0.24，Yellow 範圍為 4.56~4.79）
  - 指標一律使用燈號（🟢🟡🔴）表示，不使用文字符號（✓/⚠/✗）
  - KPI 數值一律以**黑色**顯示，燈號置於數值後方（例：`4.86 🟢`、`4.67 🟡`、`4.50 🔴`）
  - **標示位置**：僅在各月份欄位數值後顯示燈號；**Total 欄位不顯示燈號**（Total 為年度累計值，不作單一標示）
  - **適用 KPI 清單**：
    | KPI | Target | Direction |
    |-----|--------|-----------|
    | CSAT 5★ Avg | ≥ 4.8 | high (越高越好) |
    | % IR Met | ≥ 99% | high |
    | Avg Day to Close | ≤ 12 | low (越低越好) |
    | % Cases Closed ≤7d | ≥ 50% | high |
- **vs Total 標示規則**（適用於無明確 Target 但以 Total 為基準的 KPI，如 IPD Created）：
  - 🟢 = 當月值 ≥ Total（達到平均水準）
  - 🟡 = 當月值低於 Total，但落差在 5% 以內
  - 🔴 = 當月值低於 Total 超過 5%
  - Total 欄本身不做色彩標示
  - Target 欄位顯示為「vs Total」
- **無標示的 KPI**：Target 與 Direction 均為 `-` 的 KPI 不做任何色彩標示
- **Trend 標示規則**（MoM Summary 等）：
  - 🟢 綠色 = 改善中 / 達標
  - 🟡 橙色 = 接近目標 / 需觀察
  - 🔴 紅色 = 未達標 / 需立即行動
- **Footer** 需註明：
  - 各 Dashboard 使用的 Filter 條件
  - 資料日期（Data as of）
  - 報告產生時間（UTC+8）

---

## HTML 報告固定模板（Standard Template）

以下為 MOR Summary Report HTML 輸出的固定格式模板。未來每月報告均應遵循此結構產出，僅替換數據內容。

### 整體架構

```
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>MOR Summary Report - {Month} {Year} | ASW SAP & Epic Support</title>
  <style>/* 共用 CSS（見 Design System）*/</style>
</head>
<body>
  <div class="header">（報告標頭）</div>
  <div class="tab-nav">（分頁導航按鈕 × 3）</div>
  <div id="tab-mor" class="tab-panel active">（Tab 1: MOR Summary Report）</div>
  <div id="tab-cpe" class="tab-panel">（Tab 2: CPE Insight）</div>
  <div id="tab-irmissing" class="tab-panel">（Tab 3: IR Missing Insight）</div>
  <script>/* switchTab 函數 */</script>
</body>
</html>
```

### Design System（CSS 變數與共用樣式）

```css
:root {
    --green: #28a745;    /* 達標 */
    --yellow: #ffc107;   /* 接近目標 */
    --red: #dc3545;      /* 未達標 */
    --blue: #0078d4;     /* Microsoft Blue，主色 */
    --dark: #1a1a2e;     /* 標題 / 深色背景 */
    --card-bg: #ffffff;
    --bg: #f4f6f9;       /* 頁面底色 */
    --text: #333333;
    --border: #e0e0e0;
}
```

**主要元件類別**：

| CSS Class | 用途 |
|-----------|------|
| `.header` | 頁面最上方深色 Banner（gradient: `--dark` → `#16213e`） |
| `.tab-nav` / `.tab-btn` | 分頁切換按鈕列 |
| `.tab-panel` | 分頁內容區域（`.active` 顯示） |
| `.section` / `.section-title` | 區塊標題（藍色底線） |
| `.cards` / `.card` | Executive Summary KPI 卡片（grid layout, 左側色帶） |
| `.card.green` / `.card.yellow` / `.card.red` | 卡片色帶變體 |
| `.table-wrapper` / `table` | 資料表格（圓角白底、hover 高亮） |
| `.highlight-col` | 當前月份欄（黃底加粗） |
| `.total-col` | Total 欄位（綠底加粗） |
| `.badge` / `.badge-green` / `.badge-yellow` / `.badge-red` | CSAT 分數標籤（5★=green, 4★=yellow, ≤3★=red） |
| `.analysis-grid` / `.analysis-box` | Business Analysis 區塊（2 欄 grid） |
| `.highlight-box` / `.lowlight-box` / `.recommend-box` | Analysis 區塊色帶（green/red/blue） |
| `.cpe-summary-cards` / `.cpe-card` | CPE / IR Missing 摘要卡片（上方色帶，非左側） |
| `th.sortable` / `.asc` / `.desc` | 可排序欄位表頭（hover 高亮、方向箭頭指示） |
| `.verbatim-col` | Verbatim 欄位（white-space: normal，允許自動換行） |
| `.footer` | 頁尾（資料來源、Filter、日期） |

### Header 區塊

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

### Tab 導航

```html
<div class="tab-nav">
    <button class="tab-btn active" onclick="switchTab('mor')">MOR Summary Report</button>
    <button class="tab-btn" onclick="switchTab('cpe')">CPE Insight</button>
    <button class="tab-btn" onclick="switchTab('irmissing')">IR Missing Insight</button>
</div>
```

### Tab 1: MOR Summary Report 結構

依序包含以下 6 個 Section：

#### 1. Executive Summary Cards（9 張）

```html
<div class="section">
    <h2 class="section-title">Executive Summary (Year-to-Date Total)</h2>
    <div class="cards">
        <div class="card {color}">
            <div class="label">{KPI 名稱}</div>
            <div class="value">{YTD Total 數值}</div>
            <div class="trend">FY{YY} YTD</div>
        </div>
        <!-- 重複 9 張，參照 Executive Summary Cards 清單 -->
    </div>
</div>
```

- `{color}` = `green` | `yellow` | `red`（依 Status 判定規則）或不填（純資訊 Card）

#### 2. Business Analysis

```html
<div class="analysis-grid">
    <div class="analysis-box highlight-box">
        <h4>🟢 Highlights</h4>
        <ul><li><strong>{標題}</strong> — {說明}</li>...</ul>
    </div>
    <div class="analysis-box lowlight-box">
        <h4>🔴 Lowlights / Areas of Concern</h4>
        <ul><li><strong>{標題}</strong> — {說明}</li>...</ul>
    </div>
    <div class="analysis-box recommend-box" style="grid-column: span 2;">
        <h4>💡 Recommendations</h4>
        <ul><li><strong>{標題}</strong> — {說明}</li>...</ul>
    </div>
</div>
```

- Highlights / Lowlights 各佔一欄（2-column grid）
- Recommendations 橫跨兩欄（`grid-column: span 2`）

#### 3. Dashboard 1 — Quality Metrics 表格

```html
<div class="section">
    <h2 class="section-title">Dashboard 1 — Quality Metrics (FY{YYYY})</h2>
    <div class="table-wrapper">
        <table>
            <thead>
                <tr>
                    <th>KPI</th><th>Target</th>
                    <th>Jul</th><th>Aug</th>...<th class="highlight-col">{當月}</th>
                    <th class="total-col">Total</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>{KPI名稱}</td>
                    <td style="font-weight:600;color:#555;">{Target值}</td>
                    <td>{月值} {燈號}</td>
                    ...
                    <td class="highlight-col">{當月值} {燈號}</td>
                    <td class="total-col">{Total值} {燈號}</td>
                </tr>
            </tbody>
        </table>
    </div>
</div>
```

- **Quality Metrics KPI**（6 項，來自上方表格）：CSAT 5★ Avg, DSAT, CSAT Surveys, CSAT Response Rate, % CritSit, % IR Met
- **Operational Metrics KPI**（12 項，來自下方表格）：IPD Created, IPD Closed, Open Cases, Created Cases, Closed Cases, CSS TMPI, Avg DTC, Backlog Count, Backlog DtC, Collaboration Tasks, Post IR Transfer %, % Transfer
- 當月為年度最後一個有資料的月份，使用 `highlight-col` class 標示
- 「部分月數據」加 `⚠️` 提示（如月中資料）

#### 4. Dashboard 2 — OpEx Metric Trend View 表格

包含兩個子表格：
- **主要 OpEx Metrics（5 項有 Target）**：欄位 = Category | KPI | Target | 最近 6 個月
- **Additional OpEx Metrics（6 項無 Target）**：欄位 = Category | KPI | 最近 6 個月

接著是 **FYTD Actuals vs Benchmarks** 表格：

```html
<table>
    <thead>
        <tr><th>KPI</th><th>Actual</th><th>Target</th><th>Variance</th><th>Status</th></tr>
    </thead>
    <tbody>
        <tr>
            <td>{KPI名稱}</td>
            <td>{Actual值}</td>
            <td>{Target值}</td>
            <td class="improved|declined">{差異值}</td>
            <td>🟢 Met | 🔴 Not Met</td>
        </tr>
    </tbody>
</table>
```

#### 5. Month-over-Month Summary 表格

```html
<table class="mom-table">
    <thead>
        <tr><th>KPI</th><th>{上月} {Year}</th><th>{當月} {Year}</th><th>Change</th><th>Trend</th></tr>
    </thead>
    <tbody>
        <tr>
            <td>{KPI}</td>
            <td>{上月值}</td>
            <td>{當月值}</td>
            <td class="improved|declined">{變化值}</td>
            <td>{燈號} {方向箭頭}</td>
        </tr>
    </tbody>
</table>
```

- **Trend 方向**：`↑` = 數值上升、`↓` = 數值下降、`→` = 持平
- **class**：`.improved` = 改善（綠色）、`.declined` = 惡化（紅色）
- 需附 `⚠️` 部分月數據提示

#### 6. Footer

```html
<div class="footer">
    <p><strong>Data Sources &amp; Filters:</strong></p>
    <p>• Dashboard 1: CES BI Hub — CSS A&amp;I and DTP | Filter: Channel Function Detail = ASW_SAPEpicEsc | Time Fiscal Year = FY {YYYY} | LastSixMonths = (All)</p>
    <p>• Dashboard 2: Power BI (msit) — OpEx Overall PCY Level A&amp;I+DTP | Filter: Staff Group = A&amp;I-Azure-ASW Epic and SAP</p>
    <p>• CPE Survey: Kusto — supportrptwus3prod / KPISupportData | FY{YYYY} (Jul {YYYY-1} – {Month} {Year}) | ASW Engineers only</p>
    <p>• Data as of: {YYYY-MM-DD} (Dashboard 1 &amp; 2)</p>
    <p>• Report generated: {YYYY-MM-DD HH:MM} (UTC+8)</p>
</div>
```

### Tab 2: CPE Insight 結構

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
                <!-- 每一列 -->
                <tr>
                    <td>{IncidentId}</td>
                    <td>{Customer_TPName}</td>
                    <td>{ServiceName}</td>
                    <td>{AgentAlias}</td>
                    <td>{AgentName}</td>
                    <td><span class="badge badge-{green|yellow|red}">{Score} ★</span></td>
                    <td class="verbatim-col" style="text-align:left;white-space:normal;font-size:12px;">
                        {Verbatim 文字，無內容時顯示 <span style="color:#ccc;">-</span>}
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

**CPE 表格規則**：
- **表格佈局**：`table-layout: auto`，使用 `<colgroup>` 設定建議欄寬，其他欄位自動適配內容寬度
- **欄寬配置**：Case ID 130px, Customer auto, Service auto, AgentAlias 95px, SE Name auto, CSAT 50px, Verbatim 30%（剩餘空間）, Closed 85px, Created 85px, Region auto
- **互動排序**：Customer, Service, SE Name, Closed, Created, Region 六欄支援點擊表頭排序（`th.sortable`），預設以 Closed 降序排列
- **排序標示**：`th.sortable::after` 顯示 ⇅（未排序）、↑（升序 `.asc`）、↓（降序 `.desc`）
- CSAT Badge：`badge-green`（5★）、`badge-yellow`（4★）、`badge-red`（≤3★）
- Verbatim 文字自動換行（`white-space: normal`，class `verbatim-col`），其餘欄位 `white-space: nowrap` + `text-overflow: ellipsis`
- 無 Verbatim 時顯示灰色 `-`
- 排序：預設 `ClosedDateTime` 降序（最近日期在上方）

### Tab 3: IR Missing Insight 結構

```html
<div id="tab-irmissing" class="tab-panel">
    <div class="section">
        <h2 class="section-title">IR Missing Insight — FY{YYYY} Initial Response Not Met Cases</h2>
        <p style="font-size:13px; color:#666; margin-bottom:16px;">
            FY{YYYY} YTD IR Missing cases for ASW_SAPEpicEsc (Jul {YYYY-1} – {Month} {Year}).
            Source: CES BI Hub IR Missed Reasons Dashboard + Kusto
        </p>
        <!-- 主要 Flex 容器：左側 Cards+TTMS、右側 Chart -->
        <div style="display:flex; gap:20px; align-items:stretch; margin-bottom:20px;">
            <!-- 左側欄（固定 320px）：Summary Cards + TTMS 統計 -->
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
                <!-- Average TTMS by Severity（填滿左側下方空間） -->
                <div style="flex:1; background:#fff; border-radius:10px; padding:16px; box-shadow:0 2px 8px rgba(0,0,0,0.06); border-top:3px solid #6366f1;">
                    <div style="font-size:0.7rem; color:#64748b; text-transform:uppercase; margin-bottom:10px;">Avg TTMS by Severity</div>
                    <!-- 每個 Severity 一張卡片（A / B / C），垂直堆疊 -->
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
            <!-- 右側欄（flex:1）：IR Missing Trend Chart -->
            <div style="flex:1; min-width:350px; background:#fff; border-radius:10px; padding:12px 16px; box-shadow:0 2px 8px rgba(0,0,0,0.06); border-top:3px solid #0078d4;">
                <div style="font-size:0.7rem; color:#64748b; text-transform:uppercase; margin-bottom:4px;">IR Missing Trend (FY{YYYY})</div>
                <svg viewBox="0 0 550 180" style="width:100%; height:auto; font-family:sans-serif;">
                    <!-- Grid: Y-axis 0~{maxCumulative}, X-axis Jul~{最後月份} -->
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
                    <td>{SE Manager（透過 AGENT_MANAGER_MAP 查詢）}</td>
                    <td>{YYYY-MM-DD}</td>
                    <td>{YYYY-MM-DD}</td>
                    <td>{Sev A 紅色加粗，其餘一般}</td>
                    <td>{TTMS 值，null 顯示灰色 -，異常高值紅色加粗}</td>
                    <td>{RegionName}</td>
                </tr>
            </tbody>
        </table></div>
    </div>
</div>
```

**IR Missing 頁面版面設計原則**：
- **整體佈局**：上方為 flex 橫向排列（左欄固定 320px + 右欄 flex:1），下方為全寬資料表格
- **左欄**：Summary Cards（2×2 grid）+ Avg TTMS by Severity（垂直堆疊，填滿剩餘高度）
- **右欄**：SVG 折線圖（Cumulative 藍線 + Monthly Count 橘色 bar），自動填滿右側空間
- **視覺平衡**：左右兩欄等高（`align-items:stretch`），避免任一側出現空白

**IR Missing 表格規則**：
- Severity A：`<span style="color:#e74c3c; font-weight:600;">A</span>`
- Severity B/C：一般文字
- TTMS null（Sev B/C 常見）：`<span style="color:#ccc;">-</span>`
- TTMS 數值：**四捨五入至小數點第一位**（例：`2.48` → `2.5`、`29.98` → `30.0`）
- TTMS 異常值（> 480 mins / 8 hours）：`style="color:#e74c3c; font-weight:600;"`
- SE Name 為空：灰色 `-`
- 排序：`CreatedDateTime` 降序

**Average TTMS by Severity 統計規則**：
- 位置：左欄 Summary Cards 下方（同一 flex column），填滿左側剩餘垂直空間
- 以垂直堆疊卡片呈現，每個 Severity 一張卡片（A / B / C）
- 計算邏輯：取該 Severity 所有 TTMS 非 null 值，計算平均值（四捨五入小數一位）
- 若該 Severity 所有 TTMS 均為 null，顯示 `N/A` 並標注 "No SLA requirement"
- 卡片內容：Severity 名稱、平均值、case 數量、數值範圍（min – max）
- 色彩：Sev A `#e74c3c` / Sev B `#e67e22` / Sev C `#3498db`
- 容器樣式：`border-top: 3px solid #6366f1`，白底圓角

**SVG 月度趨勢圖規則**：
- **位置**：右欄（flex:1），與左欄等高
- **viewBox**：`0 0 550 180`（較緊湊，適配右側空間）
- **圖表類型**：複合圖（Cumulative 折線 + Monthly Count 長條）
- **Cumulative 折線**：`stroke #0078d4`（Microsoft Blue）、`stroke-width 2.5`、圓形數據點 r=3.5
- **Monthly 長條**：`fill #f97316`（橘色）、`opacity 0.5`、底部對齊
- **Y 軸**：以 cumulative 最大值為上限，兩種圖共用同一 scale
- **X 軸**：Jul ~ 當月，等距排列
- **Legend**：左上方，藍色圓點 = Cumulative、橘色方塊 = Monthly
- **容器樣式**：`border-top: 3px solid #0078d4`，白底圓角

### Tab 切換 Script

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

### 模板替換變數一覽

| 變數 | 說明 | 範例 |
|------|------|------|
| `{Month}` | 報告月份（英文全名） | `May` |
| `{Year}` | 報告年份 | `2026` |
| `{YYYY}` | 財年年份 | `2026` |
| `{YYYY-1}` | 財年起始年份 | `2025` |
| `{YY}` | 財年年份縮寫 | `26` |
| `{N}` | 各摘要卡片的計數值 | `43` |
| `{當月}` | 當前月份（英文縮寫） | `May` |
| `{上月}` | 上一個月份（英文全名） | `Apr` |

---

## 工作流程

### Step 1 — 數據收集

> 🚀 **預設路徑**：Dashboard 1 KPI + IR Missing 一律由 Cowork 提供（檔案落地在 `Output/Cowork/`）；Dashboard 2 OpEx 依然用 Playwright + 外部 Edge 抓；CPE Survey 用 Kusto MCP。Cowork 檔案遺失／過期時才回從 Dashboard 1 / IR Missed 的 Playwright fallback。

> 🚨 **瀏覽器規定（Playwright fallback / Dashboard 2 專用，BLOCKING RULE，每次執行必遵守）**：
>
> 所有 Dashboard 頁面（Dashboard 1、Dashboard 2、IR Missed Reasons）**一律使用外部 Microsoft Edge 瀏覽器開啟**。**以下瀏覽器全部禁止使用**：
>
> - ❌ **VS Code Simple Browser**（內嵌瀏覽器）
> - ❌ **`open_browser_page` / VS Code Chat 整合式 Playwright 瀏覽器**（也算內嵌，同樣被 Conditional Access 拒絕存取）
> - ❌ 任何非 Edge 的第三方瀏覽器
>
> **正確操作方式**：
>
> 1. 透過終端機執行 `Start-Process msedge '<URL>'` 開啟外部 Edge 瀏覽器
> 2. 使用 **Playwright MCP 工具（`mcp_playwright_browser_*`）** 透過 CDP 連接該外部 Edge 進行頁面操作與資料擷取
> 3. **禁止呼叫 `open_browser_page`**（會開啟整合式瀏覽器，違反規則）
>
> **原因**：VS Code 內嵌 / Chat 整合瀏覽器因 Conditional Access 合規政策無法存取 CES BI Hub 等內部系統，會被卡在登入頁或直接拒絕。
>
> **若 Playwright MCP 無法連接外部 Edge**：通知用戶並暫停執行，不可退回使用整合式瀏覽器。可請用戶手動操作 Edge 並提供 screenshot / 匯出檔，或以 `Start-Process msedge --remote-debugging-port=9222` 啟動具 CDP debug port 的 Edge instance 供 Playwright attach。

> ⚠️ **強制查驗規則（每次執行必做）**：每次產出 Monthly Summary Report 時，**必須重新拉取以下 4 類資料來源**，不可跳過或僅使用快取/歷史資料：
>
> | # | 資料來源 | 用途 | 優先方式 | Fallback |
> |---|----------|------|---------|----------|
> | 1 | **Commercial Insights+ V2** — KPI by Month | 19 KPI（Dashboard 1 Quality + Operational） | Cowork xlsx | Playwright + CES BI Hub |
> | 2 | **Commercial Insights+ V2** — IR Missed | IR Missing 明細 | Cowork xlsx | Playwright + CES BI Hub IR Missed Reasons |
> | 3 | **OpEx Overall PCY Level A&I+DTP** | OpEx 5 KPI | Playwright + Edge（無 Cowork 版本） | — |
> | 4 | **Kusto — CPE Survey** | CPE Insight（CSAT、Verbatim、AgentName） | Kusto MCP | — |
>
> 即使上次報告已收集過資料，每次執行仍須**重新拉取**，確保報告反映最新數據。禁止使用任何快取、歷史記錄或先前對話中的資料。

**預設執行順序**：

0. **前置（由用戶完成）**：在 Cowork 跑完 `asw-team-kpi-monthly`（KPI + IR Missed），將產出 xlsx／選用 json 複製到 `C:\GitHubCopilot\IronMan\Output\Cowork\`。
1. 本 Agent 自 `Output/Cowork/` 讀取最新 `asw_kpi_by_month_FY*.xlsx` → 得 Dashboard 1 全部 KPI。
2. 本 Agent 自 `Output/Cowork/` 讀取最新 `asw_ir_missed_FY*.xlsx` → 得 IR Missing 明細（含 Verbatim、SE Manager）。
3. 開啟 Dashboard 2（使用外部 Edge + Playwright MCP），確認 Staff Group Filter，等待 **2 分鐘** 後擷取 OpEx Metric Trend View 資料。
4. 呈交 CPE Survey Kusto Query（`mcp_kusto_kusto_query`），查詢**整個當前 FY**（例 FY2027 = `datetime(2026-07-01) ~ datetime(2027-06-01)`）。

**Fallback 步驟（僅在 Cowork 檔案遺失時執行，需取得用戶導向后才進行）**：
1. 開啟 Dashboard 1（Edge），**嚴格依序執行 4 項 Filter 驗證**（① Channel=ASW_SAPEpicEsc → ② LastTwelveMonths=(All) → ③ LastSixMonths=(All) → ④ FY=僅當前財年），確認 restatement 全部正確後等待 **2 分鐘**，再擷取資料。
2. 開啟 IR Missed Reasons Dashboard（Edge），**嚴格依序執行 4 項 Filter 驗證**（⚠️ **順序至關重要，必須依序**：① Channel=ASW_SAPEpicEsc → ② LastTwelveMonths=(All) → ③ **LastSixMonths 必須先清除**（預設為 `is Yes`，清除為 `is (All)`） → ④ **最後才設定** FY=僅當前財年），設定 Slicer，等待 **2 分鐘** 後擷取 IR Missing Case ID 清單。**驗證：案件月份應涵蓋完整 FY（Jul 起），scrollHeight ≥ 25000px**。
3. 以 IR Missing Case ID 清單執行 Kusto Query（補充 AgentName、Region 等 Dashboard 未提供欄位）。

### Step 2 — 內容組織
將原始數據整理為結構化報告內容，進行初步 Business Analysis

### Step 3 — HTML 產出
將數據與分析結果輸出為 HTML 報告，存放至指定路徑

### Step 4 — 簡報製作（可選）
搭配 `ppt_creator` 技能，將報告內容轉為 Monthly Review 簡報

---

## 已知問題與經驗教訓（Known Issues & Lessons Learned）

### PBI Filter Pane 互動限制

| 嚴重度 | 問題 | 說明 | 解法 |
|--------|------|------|------|
| 🚨 **P0** | **Time Fiscal Year Bookmark 預設含前一財年** | Dashboard 1 與 IR Missed Reasons 的 bookmark 載入後，`Time Fiscal Year` restatement 通常會同時包含當前財年與前一財年（例：FY2027 環境下顯示 `is FY 2027 or FY 2026`）。**若未修正為僅當前財年，Total/YTD 數據將混入上一財年，導致所有累計值錯誤。** | **必須**展開 Filter Card → 取消勾選前一財年 → 確認 restatement 僅為當前財年（例：`is FY2027`）。若展開失敗，用 Clear filter 清除後重新勾選當前財年。此操作優先級等同 P0。 |
| 🚨 **P0** | **LastSixMonths 預設為 `is Yes`** | Dashboard 1 與 IR Missed Reasons 的 `Time LastSixMonths` filter card 預設為 `is Yes`，導致資料僅涵蓋過去 6 個月而非完整財年。**若未清除將遺失 40-50% 案件。** | 依照 Filter 驗證順序 Step 3c 點擊 Clear filter 按鈕清除此篩選（`[aria-label="Clear filter"]`），確認 restatement 變為 `is (All)`。操作後驗證 scrollHeight ≥ 25000px。 |
| ⚠️ P1 | **Filter Card 無法展開** | IR Drill 頁面的「Filters on all pages」中，部分 Filter Card 的展開按鈕（`aria-expanded="false"`）點擊後不會展開內容，無法直接操作內部 checkbox | 改用 **Clear filter（橡皮擦按鈕）** 重置為 `is (All)`，或使用**頁面上的 Slicer** 進行篩選 |
| ℹ️ P2 | **Clear filter 按鈕判斷** | Clear filter 按鈕有兩種狀態：`aria-disabled="false"`（可點擊）與 `disabled="" aria-disabled="true"`（已為 All，無需操作） | 檢查 `aria-disabled` 屬性後再決定是否點擊 |

### PBI Slicer 操作技巧

| 問題 | 說明 | 解法 |
|------|------|------|
| **🚨 P0：Show/hide filter pane 按鈕的所有標準 click 全失效** | 位於 PBI 右上角的 `button[aria-label="Show/hide filter pane"]` 使用 Playwright `click()` 會被 CES BI Hub 外層 Angular 的 `<div class="toggleBtn" data-testid="filter-btn">` overlay 攔截（`subtree intercepts pointer events`）；`click({force:true})` 與 `focus() + keyboard.press('Enter')` 雖無錯誤但 `aria-expanded` 不會變 `true` | **改用 `page.mouse` 座標點擊**（實測 2026-07 唯一可靠方式）：<br>```js
const box = await btn.boundingBox();
await page.mouse.move(box.x + box.width/2, box.y + box.height/2);
await page.waitForTimeout(150);
await page.mouse.down();
await page.waitForTimeout(50);
await page.mouse.up();
```<br>同樣模式適用於 Filter Card 的 **Clear filter 按鈕**、**Expand/collapse 按鈕**、以及展開後的 **checkbox**。點擊前務必先 `await loc.scrollIntoViewIfNeeded()`，否則 boundingBox 會回報 filter pane scroll 容器內的原始座標（可能超出 viewport），mouse.click 打不到。 |
| **Filter Card 內 checkbox 為虛擬捲動，無法直接定位目標值** | Filter Card 展開後 checkbox 使用虛擬捲動；例如 Time Fiscal Year 只渲染 FY 2007–2013 附近幾項，`[role="checkbox"][title="FY 2027"]` 直接查會回傳 count=0，`scrollIntoViewIfNeeded` 也無法喚出（元素根本不在 DOM 中） | **必用 Filter Card 內建 Search 框先過濾**：<br>1. 找到該 filter card 內 `input[placeholder="Search"]`<br>2. 座標 mouse click 聚焦 → `await search.pressSequentially('FY 2027', { delay: 80 })`（`fill()` 無效）<br>3. Search 過濾後目標 checkbox 會出現，再 `boundingBox` + mouse.down/up 勾選<br>Channel Function Detail 選 `ASW_SAPEpicEsc` 走完全一致流程 |
| **Slicer 搜尋框 `fill()` 無效** | PBI Slicer 搜尋框使用 `fill()` 或 `type()` 方法填入文字後不會觸發篩選更新 | 使用 `pressSequentially('ASW_SAP', { delay: 80-100 })` 逐字輸入，模擬人工鍵入以觸發 PBI 的 key handler |
| **Checkbox aria-label 為 null** | Filter Card 展開後的 checkbox 元素其 `aria-label` 可能為 null，實際文字位於 `title` 屬性或子元素 `.slicerText` | 使用 `[role="checkbox"][title="FY 2027"]` 或讀取 `title` 屬性辨識目標項目 |

### PBI Grid 虛擬捲動

| 問題 | 說明 | 解法 |
|------|------|------|
| **Grid 僅渲染可見行** | PBI 表格使用虛擬捲動（virtual scroll），一次僅渲染約 20 行，其餘行不在 DOM 中 | 透過 `.mid-viewport` div 逐步捲動（每次 400px，間隔 300ms），在每個位置收集可見行，使用 `Set` 去重 |
| **Grid 僅渲染可見欄（水平虛擬捲動）** | PBI 表格欄位數超出可見寬度時（如 13 欄僅顯示 10 欄），DOM 中不會渲染隱藏的欄位。`scrollLeft` 程式設定或 CSS scroll 無法觸發 PBI 的虛擬欄位渲染 | **使用 `page.mouse.wheel(deltaX, 0)` 在 Grid 上觸發水平捲動**。步驟：①取得 grid 的 `boundingBox()` ② `page.mouse.move(box.x + box.width/2, box.y + box.height - 20)` 移到表格底部捲軸區域 ③ `page.mouse.wheel(300, 0)` 向右捲動（負值向左）④ 等待 2 秒後讀取新渲染的欄位。需**分兩次讀取**：先讀左半部（Jul-Apr），再 wheel 右移讀取 May + Total |
| **scrollHeight 隨資料量變化** | 全年資料（`LastSixMonths = All`）的 scrollHeight 約為六個月資料的 2 倍（例：33966 vs 17000） | 以 `scrollHeight` 計算需要的捲動次數，確保涵蓋所有行 |

### Kusto 資料注意事項

| 問題 | 說明 | 解法 |
|------|------|------|
| **🚨 使用 Kusto MCP 工具** | Kusto 查詢**直接使用 `mcp_kusto_kusto_query` MCP 工具**執行，無需 Azure CLI 驗證（`az login`）或 `kusto_runner.py` 腳本。MCP 工具已具備完整認證能力，可直接傳入 cluster_uri、database、query 三個參數執行查詢 | 直接呼叫 `mcp_kusto_kusto_query`，指定 `cluster_uri="https://supportrptwus3prod.westus3.kusto.windows.net"`、`database="KPISupportData"`、`query="..."` |
| **`IsIrMet` 欄位為空** | Kusto `AllCloudsSupportIncidentWithReferenceModelVNext` 表中 `IsIrMet` 欄位在 FY2026 之後的所有記錄均為空字串（`""`），無法用於判斷 IR Missing 狀態 | IR Missing 狀態由 **PBI Model 計算**（基於 `InitialResponseDateTime` 是否為 null），必須從 Dashboard 擷取 Case ID，而非直接在 Kusto 中篩選 |
| **InitialSeverity 值** | 大部分案件為 `A` / `B` / `C`，但偶爾出現 `1` 等非標準值 | HTML 報告中直接顯示原始值，不做轉換 |
| **TTMS 與 Severity 關聯** | Sev B/C 案件的 TTMS 通常為 `null`（無 SLA 要求） | HTML 中 TTMS 為 null 時顯示 `-`（灰色） |

### PBI iframe 結構

```
Page (cesbihub.microsoft.com)                                       ← top document
  ├─ (Angular) 外層 wrapper（含 `<div data-testid="filter-btn">` overlay）
  ├─ iframe name="exportiFrame" src="about:blank"                    ← same-origin
  ├─ iframe name="refreshAccessTokenIframe" (cesbihub.microsoft.com) ← same-origin
  └─ iframe name="reportPageiFrame" src="about:blank"                ← same-origin，但內含 PBI
       └─ iframe src="https://msit.powerbi.com/reportEmbed?..."      ← CROSS-ORIGIN，PBI 實際內容在這
```

#### 🚨 P0：PBI 內容為 Cross-Origin iframe — 頂層 `document.querySelector` 無法穿透

- CES BI Hub 把 PBI 報告嵌在 `msit.powerbi.com/reportEmbed` iframe 內，該 iframe 相對於頁面頂層是 **cross-origin**，因此：
  - `document.querySelector('[data-testid="filter-btn"]')` 或 `button[aria-label="Show/hide filter pane"]` 從頂層文件永遠回傳 `null`
  - 從頂層文件 `contentDocument` 存取 PBI iframe 會被 SOP 阻擋（return `null`）
  - `mcp_playwright_browser_evaluate`（在頂層執行）**無法**跨進 PBI frame 操作 DOM
- **正確做法**：透過 `mcp_playwright_browser_run_code_unsafe` 執行 Playwright 自身的 frame API（Playwright 內部可跨 origin 存取所有 frames）：
  ```js
  async () => {
    const pbi = page.frames().find(f => f.url().includes('powerbi.com/reportEmbed'));
    if (!pbi) return { err: 'no pbi frame' };
    // 後續所有 locator 都掛在 pbi 上，例如：
    const cards = await pbi.locator('[data-automation-type="filterCard"]').all();
    // 或者搜尋 filter 標題：
    const fy = pbi.locator('[data-automation-type="filterCard"]').filter({
      has: pbi.locator('[data-testid="filter-card-title"][aria-label^="Time Fiscal Year"]')
    }).first();
    return { count: cards.length };
  }
  ```
  **注意**：`mcp_playwright_browser_run_code_unsafe` 只接受 async 箭頭函式或表達式，不接受 top-level `const` 宣告；必須包在 `async () => { ... }` 內。
- **禁止**：不要用 `page.frames()[4]` 這種靠 index 尋找 PBI frame — index 會因 CES BI Hub 頁面版本或載入時序不同而改變。永遠用 `find(f => f.url().includes('powerbi.com/reportEmbed'))`。

#### 常用 Locator 樣板

- **Filter Card 定位**：`pbiFrame.locator('[data-automation-type="filterCard"]')` 取得所有 filter cards，再透過 `[data-testid="filter-card-title"]` 的 `aria-label` 屬性判斷是哪個 filter
- **Restatement 文字**：`[data-testid="filter-card-restatement"]` 取得 filter 的當前設定值描述
- **展開/收合按鈕**：`pbi.locator('[aria-label="Time Fiscal Year Expand or collapse filter card"]')`（把 filter 名稱換掉）
- **Clear filter 按鈕**：卡片內 `[aria-label="Clear filter"]`
- **Search 輸入框**：卡片內 `input[placeholder="Search"]`
- **Checkbox**：`pbi.locator('[role="checkbox"][title="FY 2027"]')`（虛擬捲動下 Search 過濾後才會出現）
