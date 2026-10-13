"use strict";

function average(row, sum, count) {
  return row && row[count] > 0 ? row[sum] / row[count] : null;
}

function compareDTC(a, b) {
  const left = average(a, "DTCSum", "DTCRecords");
  const right = average(b, "DTCSum", "DTCRecords");
  if (left === null && right !== null) return 1;
  if (right === null && left !== null) return -1;
  return (left === null ? 0 : left - right) || a.Engineer.localeCompare(b.Engineer);
}

function pathMatches(a, b) {
  return a.SapSupportPathL2 === b.SapSupportPathL2 && a.SapSupportPathL3 === b.SapSupportPathL3;
}

function scopeReport(data, scope, selectedPath = null) {
  const rows = data.rows.filter(row => row.Scope === scope);
  const cohort = data.cohort.filter(row => scope === "All" || row.Scope === scope);
  const totals = rows.filter(row => row.Kind === "Engineer");
  const summary = totals.reduce((result, row) => {
    for (const key of ["Tickets", "DTCSum", "DTCRecords", "CSATSum", "SurveysCount"]) result[key] += row[key];
    return result;
  }, { Tickets: 0, DTCSum: 0, DTCRecords: 0, CSATSum: 0, SurveysCount: 0 });
  const paths = rows.filter(row => row.Kind === "Path").sort((a, b) =>
    b.Tickets - a.Tickets || a.SapSupportPathL2.localeCompare(b.SapSupportPathL2) || a.SapSupportPathL3.localeCompare(b.SapSupportPathL3)
  ).slice(0, 10);
  const customers = rows.filter(row => row.Kind === "Customer").sort((a, b) =>
    b.Tickets - a.Tickets || a.Customer.localeCompare(b.Customer) || a.Customer_TPID.localeCompare(b.Customer_TPID)
  ).slice(0, 10);
  const source = selectedPath === null ? totals : rows.filter(row => row.Kind === "PathEngineer" && pathMatches(row, selectedPath));
  const engineers = cohort.map(member => source.find(row => row.Engineer === member.Engineer) || {
    Engineer: member.Engineer, Tickets: 0, DTCSum: 0, DTCRecords: 0, CSATSum: 0, SurveysCount: 0,
    ReopenRecords: 0, ReopenKnownRecords: 0
  }).sort(compareDTC);
  return { summary, paths, customers, engineers, members: cohort.length, rows };
}

function sortPaths(rows, key = "AvgDTC", direction = "descending") {
  const factor = direction === "ascending" ? 1 : -1;
  return [...rows].sort((a, b) => {
    const left = a[key];
    const right = b[key];
    if (left === null && right !== null) return 1;
    if (right === null && left !== null) return -1;
    const difference = left === null ? 0 : typeof left === "number" ? left - right : left.localeCompare(right);
    return difference * factor || a.SapSupportPathL2.localeCompare(b.SapSupportPathL2) || a.SapSupportPathL3.localeCompare(b.SapSupportPathL3);
  });
}

function pathRows(report) {
  const rows = report.paths.map(row => {
    const candidates = report.rows.filter(candidate => candidate.Kind === "PathEngineer" && pathMatches(candidate, row) && candidate.DTCRecords > 0).sort(compareDTC);
    const best = candidates.length ? average(candidates[0], "DTCSum", "DTCRecords") : null;
    return {
      ...row,
      AvgDTC: average(row, "DTCSum", "DTCRecords"),
      AvgCSAT: average(row, "CSATSum", "SurveysCount"),
      TopEngineer: candidates.filter(candidate => average(candidate, "DTCSum", "DTCRecords") === best).map(candidate => candidate.Engineer).join(", ") || "No data"
    };
  });
  return sortPaths(rows).map((row, index) => ({ ...row, Position: index + 1 }));
}

function engineerRows(report) {
  let previous = null;
  let rank = 0;
  return report.engineers.filter(row => row.Tickets > 0).map((row, index) => {
    const dtc = average(row, "DTCSum", "DTCRecords");
    if (dtc !== null && dtc !== previous) rank = index + 1;
    previous = dtc;
    return { ...row, Rank: dtc === null ? "-" : rank };
  });
}

function comparisonReport(data, scope, selectedPath = null) {
  const report = scopeReport(data, scope, selectedPath);
  if (scope !== "All") return report;
  const managers = new Map();
  const owners = new Map(data.cohort.map(row => [row.Engineer, row.Scope]));
  for (const row of report.engineers) {
    const manager = owners.get(row.Engineer);
    if (!managers.has(manager)) managers.set(manager, {
      Engineer: manager, ManagerAlias: manager, Tickets: 0, DTCSum: 0, DTCRecords: 0, CSATSum: 0, SurveysCount: 0,
      ReopenRecords: 0, ReopenKnownRecords: 0
    });
    const aggregate = managers.get(manager);
    for (const key of ["Tickets", "DTCSum", "DTCRecords", "CSATSum", "SurveysCount"]) aggregate[key] += row[key];
    for (const key of ["ReopenRecords", "ReopenKnownRecords"]) {
      aggregate[key] = Number.isFinite(aggregate[key]) && Number.isFinite(row[key]) ? aggregate[key] + row[key] : null;
    }
  }
  return { ...report, engineers: [...managers.values()].sort(compareDTC) };
}

function metricCases(data, scope, engineer, selectedPath, metric) {
  const cases = metric === "reopen" ? data.reopenCases : data.dtcCases;
  const value = metric === "reopen" ? "ReopenedCount" : "DTCValue";
  if (!Array.isArray(cases)) throw new Error(`Case details are unavailable. Refresh the Kusto export to load ${metric} cases.`);
  return cases.filter(row =>
    (scope === "All" || row.Scope === scope) && (engineer === null || row.Engineer === engineer) && (selectedPath === null || pathMatches(row, selectedPath))
  ).sort((a, b) => b[value] - a[value] || a.IncidentId.localeCompare(b.IncidentId));
}

function dtcCases(data, scope, engineer, selectedPath = null) {
  return metricCases(data, scope, engineer, selectedPath, "dtc");
}

function comparisonCases(data, scope, row, selectedPath = null, metric = "dtc") {
  return metricCases(data, row.ManagerAlias || scope, row.ManagerAlias ? null : row.Engineer, selectedPath, metric);
}

function reopenRate(row) {
  return row.Tickets > 0 && row.ReopenKnownRecords === row.Tickets && Number.isFinite(row.ReopenRecords)
    ? row.ReopenRecords / row.Tickets : null;
}

function reopenRows(report) {
  let previous = null;
  let rank = 0;
  return report.engineers.filter(row => row.Tickets > 0).sort((a, b) => {
    const left = reopenRate(a);
    const right = reopenRate(b);
    if (left === null && right !== null) return 1;
    if (right === null && left !== null) return -1;
    return (left === null ? 0 : left - right) || a.Engineer.localeCompare(b.Engineer);
  }).map((row, index) => {
    const rate = reopenRate(row);
    if (rate !== null && rate !== previous) rank = index + 1;
    previous = rate;
    return { ...row, ReopenRate: rate, Rank: rate === null ? "-" : rank };
  });
}

function dfmLink(caseUri) {
  if (!caseUri) return null;
  try {
    const url = new URL(caseUri);
    return url.protocol === "https:" && url.hostname === "onesupport.crm.dynamics.com" && !url.username && !url.password ? url.href : null;
  } catch {
    return null;
  }
}

function createWorkbook(ExcelJS, kind, data, scope, selectedPath = null, sort = { key: "AvgDTC", direction: "descending" }) {
  if (!["paths", "engineers", "reopen"].includes(kind)) throw new Error("Unknown report export.");
  const isReopen = kind === "reopen";
  const workbook = new ExcelJS.Workbook();
  workbook.creator = "Jarvis Review Reporter";
  workbook.calcProperties.fullCalcOnLoad = true;
  const report = comparisonReport(data, scope, selectedPath);
  const identityHeader = scope === "All" ? "Manager alias" : "Engineer (Identities Redacted)";
  const sheet = workbook.addWorksheet(isReopen ? "Re-Open comparison" : kind === "paths" ? "Support paths" : scope === "All" ? "Manager comparison" : "Engineer comparison", { views: [{ state: "frozen", ySplit: 1 }] });
  const columns = kind === "paths" ? [
    ["#", 8], ["SapSupportPathL2", 40], ["SapSupportPathL3", 55], ["Tickets", 12], ["Avg DTC (days)", 18],
    ["DTC records", 15], ["Avg CSAT", 15], ["Surveys", 12], ["Top engineer (lowest DTC)", 35], ["DTC sum", 18], ["CSAT sum", 18]
  ] : isReopen ? [
    ["Rank", 8], [identityHeader, 30], ["Tickets", 12], ["% Re-Open Cases", 20], ["re-open records", 18], ["Known re-open counts", 22]
  ] : [
    ["Rank", 8], [identityHeader, 24], ["Tickets", 12], ["Avg DTC (days)", 18], ["DTC records", 15],
    ["Avg CSAT", 15], ["Surveys", 12], ["DTC sum", 18], ["CSAT sum", 18]
  ];
  sheet.columns = columns.map(([header, width]) => ({ header, width }));
  const rows = isReopen ? reopenRows(report) : kind === "paths" ? sortPaths(pathRows(report), sort.key, sort.direction) : engineerRows(report);
  rows.forEach(row => {
    if (isReopen) {
      const added = sheet.addRow([row.Rank, row.Engineer, row.Tickets, null, row.ReopenRecords, row.ReopenKnownRecords]);
      const n = added.number;
      added.getCell(4).value = {
        formula: `IF(OR(C${n}=0,F${n}<>C${n}),"No data",E${n}/C${n})`,
        result: row.ReopenRate ?? "No data"
      };
      added.getCell(4).numFmt = "0.0%";
      return;
    }
    const values = kind === "paths"
      ? [row.Position, row.SapSupportPathL2 || "Unknown / not classified", row.SapSupportPathL3 || "Unknown / not classified", row.Tickets, null, row.DTCRecords, null, row.SurveysCount, row.TopEngineer, row.DTCSum, row.CSATSum]
      : [row.Rank, row.Engineer, row.Tickets, null, row.DTCRecords, null, row.SurveysCount, row.DTCSum, row.CSATSum];
    const added = sheet.addRow(values);
    const n = added.number;
    const dtcCol = kind === "paths" ? 5 : 4;
    const csatCol = kind === "paths" ? 7 : 6;
    added.getCell(dtcCol).value = {
      formula: kind === "paths" ? `IF(F${n}=0,"No data",J${n}/F${n})` : `IF(E${n}=0,"No data",H${n}/E${n})`,
      result: average(row, "DTCSum", "DTCRecords") ?? "No data"
    };
    added.getCell(csatCol).value = {
      formula: kind === "paths" ? `IF(H${n}=0,"No data",K${n}/H${n})` : `IF(G${n}=0,"No data",I${n}/G${n})`,
      result: average(row, "CSATSum", "SurveysCount") ?? "No data"
    };
    added.getCell(dtcCol).numFmt = "0.0";
    added.getCell(csatCol).numFmt = "0.00";
  });
  if (isReopen) sheet.getColumn(6).hidden = true;
  else {
    sheet.getColumn(kind === "paths" ? 10 : 8).hidden = true;
    sheet.getColumn(kind === "paths" ? 11 : 9).hidden = true;
  }
  if (kind === "engineers" || isReopen) {
    const casesSheet = workbook.addWorksheet(isReopen ? "Re-Open cases" : "DTC cases", { views: [{ state: "frozen", ySplit: 1 }] });
    casesSheet.columns = [
      { header: identityHeader, width: 24 }, { header: "Case ID", width: 25 },
      { header: isReopen ? "ReopenedCount" : "DTC (days)", width: 18 }, { header: "SapSupportPathL2", width: 40 }, { header: "SapSupportPathL3", width: 55 }
    ];
    rows.forEach(row => {
      const cases = comparisonCases(data, scope, row, selectedPath, isReopen ? "reopen" : "dtc");
      if (cases.length !== (isReopen ? row.ReopenRecords : row.DTCRecords)) throw new Error(`Incomplete ${isReopen ? "re-open" : "DTC"} case details for ${row.Engineer}. Refresh the report.`);
      cases.forEach(item => {
        const added = casesSheet.addRow([row.Engineer, item.IncidentId, isReopen ? item.ReopenedCount : item.DTCValue, item.SapSupportPathL2 || "Unknown / not classified", item.SapSupportPathL3 || "Unknown / not classified"]);
        added.getCell(2).numFmt = "@";
        const link = dfmLink(item.CaseUri);
        if (link) added.getCell(2).value = { text: item.IncidentId, hyperlink: link };
        else added.getCell(2).note = "DFM link unavailable in the source.";
        added.getCell(3).numFmt = isReopen ? "0" : "0.0";
      });
    });
  }
  const metadata = workbook.addWorksheet("Report context");
  metadata.columns = [{ header: "Field", width: 25 }, { header: "Value", width: 100 }];
  [
    ["Report", data.title], ["Period", data.period], ["Manager alias", scope],
    ["Support path", selectedPath === null ? "All support paths" : `${selectedPath.SapSupportPathL2} / ${selectedPath.SapSupportPathL3}`],
    ["Created start", data.start], ["Created end (exclusive)", data.endExclusive], ["Refreshed", data.generatedAt],
    ["Ownership", data.ownership], ["Source", "KPISupportData + CSI ownership snapshot"],
    ["Order", isReopen ? "Lowest re-open percentage first; exact ties share a rank" : kind === "paths" ? `${sort.key} ${sort.direction}; 10 most frequent pairs` : "Lowest average DTC first; exact ties share a rank"],
    ["DTC definition", "Closed tickets with a valid non-negative DTC; sum / valid record count"],
    ["Re-open definition", "Distinct cases with ReopenedCount > 0 / all tickets; each case counts once. Missing/invalid counts yield No data."],
    ["CSAT definition", "Valid scores (1-5); sum / scored ticket count. Missing/masked scores are No data."],
    ["Engineer identities", "Redacted; stable roster identifiers A-AM"],
    ["Case details", "DTC case IDs are internal support data; share only with authorized recipients."]
  ].forEach(row => metadata.addRow(row));
  workbook.eachSheet(worksheet => {
    worksheet.eachRow(row => row.eachCell(cell => {
      cell.font = { name: "Calibri", size: 11 };
      cell.alignment = { vertical: "top", wrapText: true };
    }));
    worksheet.getRow(1).eachCell(cell => {
      cell.font = { name: "Calibri", size: 11, bold: true, color: { argb: "FFFFFFFF" } };
      cell.fill = { type: "pattern", pattern: "solid", fgColor: { argb: "FFB11F4B" } };
    });
    worksheet.autoFilter = { from: { row: 1, column: 1 }, to: { row: Math.max(1, worksheet.rowCount), column: worksheet.columnCount } };
  });
  return workbook;
}

function startReport(data, doc) {
  const get = id => doc.getElementById(id);
  if (!data || !Array.isArray(data.rows) || !Array.isArray(data.cohort)) {
    get("status").textContent = "Report data is unavailable. Refresh the Kusto export before using this report.";
    return;
  }
  const number = (value, digits = 0) => value === null ? "No data" : value.toLocaleString("en-US", { minimumFractionDigits: digits, maximumFractionDigits: digits });
  const formatDTC = row => number(average(row, "DTCSum", "DTCRecords"), 1);
  const formatCSAT = row => number(average(row, "CSATSum", "SurveysCount"), 2);
  const addOption = (select, value, label) => {
    const option = doc.createElement("option");
    option.value = value;
    option.textContent = label;
    select.append(option);
  };
  const addRow = (body, cells) => {
    const tr = doc.createElement("tr");
    cells.forEach((value, index) => {
      const td = doc.createElement("td");
      if (typeof value === "number") td.className = "num";
      td.textContent = typeof value === "number" ? number(value) : value;
      tr.append(td);
    });
    body.append(tr);
    return tr;
  };
  const pathLabel = path => `${path.SapSupportPathL2 || "Unknown / not classified"} / ${path.SapSupportPathL3 || "Unknown / not classified"}`;
  const manager = get("manager");
  let pathSort = { key: "AvgDTC", direction: "descending" };
  const tooltip = get("dtc-tooltip");
  let tooltipButton = null;
  let hideTimer;
  function hideCases() {
    clearTimeout(hideTimer);
    tooltip.hidden = true;
    if (tooltipButton) tooltipButton.setAttribute("aria-expanded", "false");
    tooltipButton = null;
  }
  const delayHideCases = () => {
    clearTimeout(hideTimer);
    hideTimer = setTimeout(hideCases, 200);
  };
  tooltip.addEventListener("pointerenter", () => clearTimeout(hideTimer));
  tooltip.addEventListener("pointerleave", delayHideCases);
  tooltip.addEventListener("focusin", () => clearTimeout(hideTimer));
  tooltip.addEventListener("focusout", event => {
    if (!tooltip.contains(event.relatedTarget) && event.relatedTarget !== tooltipButton) delayHideCases();
  });
  doc.addEventListener("keydown", event => {
    if (event.key === "Escape" && !tooltip.hidden) {
      const button = tooltipButton;
      hideCases();
      button?.focus();
      hideCases();
    }
  });
  doc.addEventListener("click", event => {
    if (!tooltip.contains(event.target) && event.target !== tooltipButton) hideCases();
  });
  doc.defaultView.addEventListener("resize", hideCases);
  doc.addEventListener("scroll", event => {
    if (tooltipButton && !tooltip.contains(event.target)) positionCases(tooltipButton);
  }, true);
  doc.querySelectorAll("details").forEach(details => details.addEventListener("toggle", () => {
    if (!details.open) hideCases();
  }));
  manager.replaceChildren();
  addOption(manager, "All", "All");
  [...new Set(data.cohort.map(row => row.Scope))].sort().forEach(scope => addOption(manager, scope, scope));
  manager.value = data.cohort.some(row => row.Scope === "noambi") ? "noambi" : "All";
  manager.disabled = false;

  const selectedPath = (id = "path") => get(id).value === "all" ? null : scopeReport(data, manager.value).paths[Number(get(id).value)];

  function positionCases(button) {
    const rect = button.getBoundingClientRect();
    const width = doc.defaultView.innerWidth;
    const height = doc.defaultView.innerHeight;
    if (rect.bottom <= 0 || rect.top >= height) {
      hideCases();
      return;
    }
    const below = height - rect.bottom - 18;
    const above = rect.top - 18;
    const placeBelow = below >= 400 || below >= above;
    tooltip.style.maxHeight = `${Math.max(80, Math.min(400, placeBelow ? below : above))}px`;
    const top = placeBelow ? rect.bottom + 6 : rect.top - tooltip.offsetHeight - 6;
    tooltip.style.left = `${Math.max(12, Math.min(rect.left, width - tooltip.offsetWidth - 12))}px`;
    tooltip.style.top = `${Math.max(12, Math.min(top, height - tooltip.offsetHeight - 12))}px`;
  }

  function showCases(button, row, selected, metric = "dtc") {
    const isReopen = metric === "reopen";
    const count = isReopen ? row.ReopenRecords : row.DTCRecords;
    hideCases();
    tooltipButton = button;
    tooltip.replaceChildren();
    const heading = doc.createElement("p");
    heading.textContent = `${row.Engineer} - ${number(count)} ${isReopen ? "re-open" : "DTC"} records`;
    tooltip.append(heading);
    try {
      const cases = comparisonCases(data, manager.value, row, selected, metric);
      if (cases.length !== count) throw new Error("Case details do not match the record count. Refresh the report.");
      const table = doc.createElement("table");
      const head = doc.createElement("thead");
      const tr = doc.createElement("tr");
      for (const label of ["Case ID", isReopen ? "ReopenedCount" : "DTC (days)"]) {
        const th = doc.createElement("th");
        th.textContent = label;
        tr.append(th);
      }
      head.append(tr);
      const body = doc.createElement("tbody");
      cases.forEach(item => {
        const caseRow = addRow(body, [item.IncidentId, isReopen ? number(item.ReopenedCount) : number(item.DTCValue, 1)]);
        const url = dfmLink(item.CaseUri);
        if (url) {
          const link = doc.createElement("a");
          link.href = url;
          link.textContent = item.IncidentId;
          link.target = "_blank";
          link.rel = "noopener noreferrer";
          link.setAttribute("aria-label", `Open case ${item.IncidentId} in DFM`);
          caseRow.children[0].replaceChildren(link);
        } else {
          caseRow.children[0].append(" (DFM link unavailable)");
        }
      });
      if (cases.length === 0) addRow(body, [isReopen ? "No re-opened cases." : "No closed cases with valid DTC.", ""]);
      table.append(head, body);
      tooltip.append(table);
    } catch (error) {
      const message = doc.createElement("p");
      message.setAttribute("role", "alert");
      message.textContent = error.message;
      tooltip.append(message);
    }
    tooltip.hidden = false;
    button.setAttribute("aria-expanded", "true");
    positionCases(button);
  }

  function caseButton(row, selected, metric = "dtc") {
    const count = metric === "reopen" ? row.ReopenRecords : row.DTCRecords;
    const button = doc.createElement("button");
    button.type = "button";
    button.className = "case-count";
    button.textContent = number(count);
    button.setAttribute("aria-label", `${row.Engineer}: show ${count} ${metric === "reopen" ? "re-open" : "DTC"} cases`);
    button.setAttribute("aria-controls", "dtc-tooltip");
    button.setAttribute("aria-expanded", "false");
    button.addEventListener("pointerenter", () => showCases(button, row, selected, metric));
    button.addEventListener("pointerleave", delayHideCases);
    button.addEventListener("focus", () => showCases(button, row, selected, metric));
    button.addEventListener("blur", event => {
      if (!tooltip.contains(event.relatedTarget)) delayHideCases();
    });
    button.addEventListener("click", () => showCases(button, row, selected, metric));
    return button;
  }

  function renderEngineers() {
    hideCases();
    const selected = selectedPath();
    const report = comparisonReport(data, manager.value, selected);
    get("comparison-title").textContent = manager.value === "All" ? "Manager DTC comparison (Aggregated)" : "Engineer DTC comparison (Identities Redacted)";
    get("comparison-identity").textContent = manager.value === "All" ? "Manager alias" : "Engineer (Identities Redacted)";
    get("comparison-label").textContent = manager.value === "All" ? "Compare managers for" : "Compare engineers for";
    get("comparison-scope").textContent = manager.value === "All"
      ? "One row per manager, aggregating all directs. Averages use metric sums / valid record counts, not averages of engineer averages."
      : "One row per engineer with tickets in the selected scope. Engineers with zero tickets are hidden.";
    const body = get("engineers");
    body.replaceChildren();
    const max = Math.max(0, ...report.engineers.map(row => average(row, "DTCSum", "DTCRecords") || 0));
    engineerRows(report).forEach(row => {
      const dtc = average(row, "DTCSum", "DTCRecords");
      const tr = addRow(body, [row.Rank, row.Engineer, row.Tickets, formatDTC(row), dtc === null ? "No data" : "", row.DTCRecords, formatCSAT(row), row.SurveysCount]);
      tr.children[5].replaceChildren(caseButton(row, selected));
      if (dtc !== null) {
        const bar = doc.createElement("div");
        bar.className = "bar";
        bar.setAttribute("aria-label", `${row.Engineer}: ${formatDTC(row)} days`);
        const fill = doc.createElement("span");
        fill.style.width = `${max === 0 ? 0 : dtc / max * 100}%`;
        bar.append(fill);
        tr.children[4].append(bar);
      }
    });
    if (!body.children.length) {
      const tr = addRow(body, ["No tickets for this manager and support-path selection."]);
      tr.firstElementChild.colSpan = 8;
    }
  }

  function renderReopen() {
    hideCases();
    const selected = selectedPath("reopen-path");
    const all = manager.value === "All";
    get("reopen-title").textContent = all ? "Manager Re-Open comparison (Aggregated)" : "Engineer Re-Open comparison (Identities Redacted)";
    get("reopen-identity").textContent = all ? "Manager alias" : "Engineer (Identities Redacted)";
    get("reopen-label").textContent = all ? "Compare managers for" : "Compare engineers for";
    const body = get("reopen");
    body.replaceChildren();
    const rows = reopenRows(comparisonReport(data, manager.value, selected));
    if (!Array.isArray(data.reopenCases) || rows.some(row => !Number.isFinite(row.ReopenRecords) || !Number.isFinite(row.ReopenKnownRecords))) {
      const tr = addRow(body, ["Re-open data is unavailable. Refresh the Kusto export."]);
      tr.firstElementChild.colSpan = 6;
      tr.setAttribute("role", "alert");
      return;
    }
    rows.forEach(row => {
      const percent = row.ReopenRate === null ? "No data" : `${number(row.ReopenRate * 100, 1)}%`;
      const tr = addRow(body, [row.Rank, row.Engineer, row.Tickets, percent, row.ReopenRate === null ? "No data" : "", row.ReopenRecords]);
      if (row.ReopenRate !== null) {
        const bar = doc.createElement("div");
        bar.className = "bar";
        bar.setAttribute("aria-label", `${row.Engineer}: ${percent} re-opened cases`);
        const fill = doc.createElement("span");
        fill.style.width = `${row.ReopenRate * 100}%`;
        bar.append(fill);
        tr.children[4].append(bar);
      }
      tr.children[5].replaceChildren(caseButton(row, selected, "reopen"));
    });
    if (!rows.length) {
      const tr = addRow(body, ["No tickets for this manager and support-path selection."]);
      tr.firstElementChild.colSpan = 6;
    }
  }

  function renderPaths() {
    const report = scopeReport(data, manager.value);
    get("paths").replaceChildren();
    sortPaths(pathRows(report), pathSort.key, pathSort.direction).forEach(row => {
      const tr = addRow(get("paths"), [row.Position, row.SapSupportPathL2 || "Unknown / not classified", row.SapSupportPathL3 || "Unknown / not classified", row.Tickets, formatDTC(row), row.DTCRecords, formatCSAT(row), row.SurveysCount, row.TopEngineer]);
      tr.lastElementChild.className = "winner";
    });
    if (!report.paths.length) {
      const tr = addRow(get("paths"), ["No data for this manager and reporting period."]);
      tr.firstElementChild.colSpan = 9;
    }
    doc.querySelectorAll("#paths-section th[data-sort]").forEach(th => th.setAttribute("aria-sort", th.dataset.sort === pathSort.key ? pathSort.direction : "none"));
  }

  doc.querySelectorAll("#paths-section th[data-sort]").forEach(th => th.querySelector("button").addEventListener("click", () => {
    pathSort = {
      key: th.dataset.sort,
      direction: pathSort.key === th.dataset.sort && pathSort.direction === "descending" ? "ascending" : "descending"
    };
    renderPaths();
  }));

  for (const kind of ["paths", "engineers", "reopen"]) {
    const link = get(`export-${kind}`);
    link.addEventListener("click", async event => {
      event.preventDefault();
      if (link.getAttribute("aria-disabled") === "true") return;
      link.setAttribute("aria-disabled", "true");
      const status = get("export-status");
      status.hidden = false;
      status.textContent = "Creating Excel export...";
      const scope = manager.value;
      try {
        if (!globalThis.ExcelJS) throw new Error("The local Excel export library is unavailable. Restore vendor/exceljs.min.js.");
        const workbook = createWorkbook(globalThis.ExcelJS, kind, data, scope, kind === "reopen" ? selectedPath("reopen-path") : kind === "engineers" ? selectedPath() : null, pathSort);
        const buffer = await workbook.xlsx.writeBuffer();
        const blob = new Blob([buffer], { type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" });
        const url = URL.createObjectURL(blob);
        const download = doc.createElement("a");
        download.href = url;
        download.download = `rca_${kind}_${scope}_FY27.xlsx`;
        doc.body.append(download);
        download.click();
        download.remove();
        setTimeout(() => URL.revokeObjectURL(url), 30000);
        status.textContent = `Excel export ready for ${scope}. It reflects the selected filters and displayed order.`;
      } catch (error) {
        status.textContent = `Excel export failed: ${error.message}`;
      } finally {
        link.setAttribute("aria-disabled", "false");
      }
    });
  }

  function renderScope() {
    hideCases();
    pathSort = { key: "AvgDTC", direction: "descending" };
    get("export-status").hidden = true;
    const report = scopeReport(data, manager.value);
    get("members").textContent = number(report.members);
    get("tickets").textContent = number(report.summary.Tickets);
    get("dtc").textContent = formatDTC(report.summary);
    get("csat").textContent = formatCSAT(report.summary);
    get("dtc-count").textContent = `${number(report.summary.DTCRecords)} closed-ticket DTC records`;
    get("csat-count").textContent = `${number(report.summary.SurveysCount)} valid survey records`;
    get("status").textContent = report.summary.Tickets === 0
      ? `No matched tickets for ${manager.value} in this reporting period.`
      : `${manager.value}: ${number(report.summary.Tickets)} support tickets. ${report.summary.SurveysCount === 0 ? "CSAT unavailable or masked by the source." : "CSAT includes valid survey scores only."}`;
    renderPaths();
    get("customers").replaceChildren();
    report.customers.forEach((row, index) => addRow(get("customers"), [index + 1, row.Customer, row.Customer_TPID || "No data", row.Tickets]));
    if (!report.customers.length) {
      const tr = addRow(get("customers"), ["No data for this manager and reporting period."]);
      tr.firstElementChild.colSpan = 4;
    }
    get("path").replaceChildren();
    addOption(get("path"), "all", "All support paths");
    report.paths.forEach((row, index) => addOption(get("path"), String(index), pathLabel(row)));
    get("reopen-path").replaceChildren();
    addOption(get("reopen-path"), "all", "All support paths");
    report.paths.forEach((row, index) => addOption(get("reopen-path"), String(index), pathLabel(row)));
    renderEngineers();
    renderReopen();
  }
  get("provenance").textContent = `Source: KPISupportData + CSI ownership snapshot | Created range: ${data.start} to ${data.endExclusive} (exclusive) | Refreshed: ${data.generatedAt} | ${data.ownership}`;
  manager.addEventListener("change", renderScope);
  get("path").addEventListener("change", renderEngineers);
  get("reopen-path").addEventListener("change", renderReopen);
  renderScope();
  get("report").hidden = false;
}

if (typeof module !== "undefined" && module.exports) module.exports = { average, compareDTC, pathMatches, scopeReport, sortPaths, pathRows, engineerRows, dtcCases, comparisonReport, comparisonCases, reopenRate, reopenRows, dfmLink, createWorkbook };
if (typeof document !== "undefined") startReport(globalThis.RCA_REPORT_DATA, document);
