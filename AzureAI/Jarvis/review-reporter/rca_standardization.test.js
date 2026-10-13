"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const { average, compareDTC, scopeReport, sortPaths, pathRows, dtcCases, comparisonReport, comparisonCases, engineerRows, reopenRate, reopenRows, reopenComparisonReport, dfmLink, createWorkbook } = require("./rca_standardization.js");
const ExcelJS = require("./vendor/exceljs.min.js");

const metrics = (Scope, Engineer, Tickets, DTCSum, DTCRecords) => ({
  Kind: "Engineer", Scope, Engineer, Tickets, DTCSum, DTCRecords, CSATSum: 0, SurveysCount: 0
});

test("re-open ranks use all tickets, exact ties, zero rates, and explicit missing data", () => {
  const rows = [
    { Engineer: "Engineer A", Tickets: 10, ReopenRecords: 1, ReopenKnownRecords: 10 },
    { Engineer: "Engineer B", Tickets: 20, ReopenRecords: 2, ReopenKnownRecords: 20 },
    { Engineer: "Engineer C", Tickets: 5, ReopenRecords: 0, ReopenKnownRecords: 5 },
    { Engineer: "Engineer D", Tickets: 5, ReopenRecords: 1, ReopenKnownRecords: 4 },
    { Engineer: "Engineer E", Tickets: 0, ReopenRecords: 0, ReopenKnownRecords: 0 }
  ];
  const ranked = reopenRows({ engineers: rows });
  assert.deepEqual(ranked.map(row => [row.Engineer, row.Rank]), [
    ["Engineer C", 1], ["Engineer A", 2], ["Engineer B", 2], ["Engineer D", "-"]
  ]);
  assert.equal(reopenRate(rows[0]), 0.1);
  assert.equal(reopenRate(rows[2]), 0);
  assert.equal(reopenRate(rows[3]), null);
  assert.equal(reopenRate(rows[4]), null);
  assert.equal(reopenRate({ Tickets: 10 }), null);
});

test("manager re-open percentage uses summed ticket counts, not averaged engineer rates", () => {
  const sample = {
    cohort: [{ Scope: "manager", Engineer: "Engineer A" }, { Scope: "manager", Engineer: "Engineer B" }],
    rows: [
      { ...metrics("All", "Engineer A", 2, 0, 0), ReopenRecords: 1, ReopenKnownRecords: 2 },
      { ...metrics("All", "Engineer B", 8, 0, 0), ReopenRecords: 1, ReopenKnownRecords: 8 }
    ]
  };
  const row = reopenRows(comparisonReport(sample, "All"))[0];
  assert.equal(row.ManagerAlias, "manager");
  assert.equal(row.ReopenRecords, 2);
  assert.equal(row.Tickets, 10);
  assert.equal(row.ReopenRate, 0.2);
});
const data = {
  cohort: [{ Scope: "noambi", Engineer: "Engineer A" }, { Scope: "noambi", Engineer: "Engineer B" }, { Scope: "bjames", Engineer: "Engineer K" }],
  rows: [
    metrics("noambi", "Engineer A", 10, 10, 1),
    metrics("noambi", "Engineer B", 10, 90, 9),
    metrics("All", "Engineer A", 10, 10, 1),
    metrics("All", "Engineer B", 10, 90, 9),
    { ...metrics("noambi", "Engineer A", 3, 6, 3), Kind: "PathEngineer", SapSupportPathL2: "Linux", SapSupportPathL3: "Restart" }
  ]
};

test("averages use valid denominators and do not turn missing CSAT into zero", () => {
  const report = scopeReport(data, "noambi");
  assert.equal(average(report.summary, "DTCSum", "DTCRecords"), 10);
  assert.equal(average(report.summary, "CSATSum", "SurveysCount"), null);
  assert.equal(report.summary.Tickets, 20);
});

test("manager filters preserve labels and keep no-data directs", () => {
  assert.deepEqual(scopeReport(data, "bjames").engineers.map(row => row.Engineer), ["Engineer K"]);
  assert.equal(scopeReport(data, "bjames").engineers[0].DTCRecords, 0);
  assert.equal(scopeReport(data, "All").members, 3);
  assert.equal(scopeReport(data, "All").summary.Tickets, 20);
});

test("path comparison matches both levels, excludes unrelated metrics, and retains missing engineers", () => {
  const report = scopeReport(data, "noambi", { SapSupportPathL2: "Linux", SapSupportPathL3: "Restart" });
  assert.equal(report.engineers[0].Engineer, "Engineer A");
  assert.equal(average(report.engineers[0], "DTCSum", "DTCRecords"), 2);
  assert.equal(report.engineers[1].DTCRecords, 0);
  assert.ok(scopeReport(data, "noambi", { SapSupportPathL2: "Windows", SapSupportPathL3: "Restart" }).engineers.every(row => row.DTCRecords === 0));
});

test("DTC comparison orders lowest first and missing last", () => {
  const rows = [metrics("All", "Engineer B", 1, 0, 0), metrics("All", "Engineer A", 1, 8, 1), metrics("All", "Engineer K", 1, 2, 1)];
  assert.deepEqual(rows.sort(compareDTC).map(row => row.Engineer), ["Engineer K", "Engineer A", "Engineer B"]);
});

test("top 10 ranks distinct pairs and customers by counts, not averages", () => {
  const rows = Array.from({ length: 12 }, (_, index) => ({
    Scope: "All", Kind: "Path", SapSupportPathL2: "Linux", SapSupportPathL3: `Scenario ${index}`, Tickets: index + 1
  }));
  rows.push(...Array.from({ length: 12 }, (_, index) => ({
    Scope: "All", Kind: "Customer", Customer: `Customer ${index}`, Customer_TPID: `${index}`, Tickets: index + 1
  })));
  const report = scopeReport({ cohort: [], rows }, "All");
  assert.equal(report.paths.length, 10);
  assert.equal(report.customers.length, 10);
  assert.equal(new Set(report.paths.map(row => `${row.SapSupportPathL2}/${row.SapSupportPathL3}`)).size, 10);
  assert.equal(report.paths[0].Tickets, 12);
  assert.equal(report.paths[9].Tickets, 3);
  assert.equal(report.customers[0].Tickets, 12);
});

test("live export preserves per-scope totals, unique pairs and anonymized identifiers", () => {
  require("./rca_standardization_FY27.data.js");
  const live = globalThis.RCA_REPORT_DATA;
  const scopes = [...new Set(live.cohort.map(row => row.Scope))];
  const all = scopeReport(live, "All");
  assert.equal(all.summary.Tickets, scopes.reduce((sum, scope) => sum + scopeReport(live, scope).summary.Tickets, 0));
  assert.equal(new Set(live.cohort.map(row => row.Engineer)).size, live.cohort.length);
  assert.ok(live.cohort.every(row => /^Engineer [A-Z]+$/.test(row.Engineer)));
  const aliases = require("node:fs").readFileSync(require("node:path").join(__dirname, "rca_standardization_FY27.kql"), "utf8")
    .split("\n").map(line => line.match(/^\s*"([^"]+)", "[^"]+", "Engineer [A-Z]+"/)?.[1]).filter(Boolean);
  const exported = JSON.stringify(live);
  assert.ok(aliases.length > 0);
  for (const alias of aliases) assert.ok(!exported.includes(`"${alias}"`), `Alias ${alias} must not be exported`);
  for (const scope of ["All", ...scopes]) {
    const report = scopeReport(live, scope);
    assert.ok(report.paths.length <= 10);
    assert.ok(report.customers.length <= 10);
    assert.equal(new Set(report.paths.map(row => JSON.stringify([row.SapSupportPathL2, row.SapSupportPathL3]))).size, report.paths.length);
    for (const path of report.paths) {
      const sum = scopeReport(live, scope, path).engineers.reduce((total, row) => total + row.Tickets, 0);
      assert.equal(sum, path.Tickets);
    }
  }
});

test("support paths default to descending unrounded DTC, with nulls last in either direction", () => {
  const report = {
    paths: [
      { SapSupportPathL2: "Linux", SapSupportPathL3: "Low", DTCSum: 4, DTCRecords: 2, CSATSum: 0, SurveysCount: 0 },
      { SapSupportPathL2: "Linux", SapSupportPathL3: "None", DTCSum: 0, DTCRecords: 0, CSATSum: 0, SurveysCount: 0 },
      { SapSupportPathL2: "Linux", SapSupportPathL3: "High", DTCSum: 20, DTCRecords: 2, CSATSum: 0, SurveysCount: 0 }
    ], rows: []
  };
  assert.deepEqual(pathRows(report).map(row => row.SapSupportPathL3), ["High", "Low", "None"]);
  assert.deepEqual(sortPaths(pathRows(report), "AvgDTC", "ascending").map(row => row.SapSupportPathL3), ["Low", "High", "None"]);
  const strings = sortPaths(pathRows(report), "SapSupportPathL3", "ascending");
  assert.deepEqual(strings.map(row => row.SapSupportPathL3), ["High", "Low", "None"]);
});

test("DTC case lists match scope, engineer and both path levels", () => {
  const sample = { dtcCases: [
    { Scope: "noambi", Engineer: "Engineer A", IncidentId: "0001234567890123", SapSupportPathL2: "Linux", SapSupportPathL3: "Restart", DTCValue: 2 },
    { Scope: "noambi", Engineer: "Engineer A", IncidentId: "0001234567890124", SapSupportPathL2: "Windows", SapSupportPathL3: "Restart", DTCValue: 9 },
    { Scope: "bjames", Engineer: "Engineer K", IncidentId: "0001234567890125", SapSupportPathL2: "Linux", SapSupportPathL3: "Restart", DTCValue: 5 }
  ] };
  assert.equal(dtcCases(sample, "All", "Engineer A").length, 2);
  assert.equal(dtcCases(sample, "bjames", "Engineer A").length, 0);
  assert.equal(dtcCases(sample, "noambi", "Engineer A", { SapSupportPathL2: "Linux", SapSupportPathL3: "Restart" })[0].IncidentId, "0001234567890123");
  assert.throws(() => dtcCases({}, "All", "Engineer A"), /unavailable/);
});

test("live DTC case IDs and sums exactly match every engineer comparison", () => {
  require("./rca_standardization_FY27.data.js");
  const live = globalThis.RCA_REPORT_DATA;
  assert.equal(new Set(live.dtcCases.map(row => row.IncidentId)).size, live.dtcCases.length);
  for (const scope of ["All", ...new Set(live.cohort.map(row => row.Scope))]) {
    const all = scopeReport(live, scope);
    for (const path of [null, ...all.paths]) {
      for (const row of scopeReport(live, scope, path).engineers) {
        const cases = dtcCases(live, scope, row.Engineer, path);
        assert.equal(cases.length, row.DTCRecords);
        const sum = cases.reduce((total, item) => total + item.DTCValue, 0);
        assert.ok(Math.abs(sum - row.DTCSum) < 1e-8);
        assert.ok(cases.every(item => typeof item.IncidentId === "string" && Number.isFinite(item.DTCValue) && item.DTCValue >= 0));
      }
    }
  }
});

test("Excel exports round-trip with filters, sort, formulas, cached results, and string case IDs", async () => {
  require("./rca_standardization_FY27.data.js");
  const live = globalThis.RCA_REPORT_DATA;
  const scope = "noambi";
  const report = scopeReport(live, scope);
  const sort = { key: "Tickets", direction: "ascending" };
  for (const kind of ["paths", "engineers"]) {
    const selected = kind === "engineers" ? report.paths[0] : null;
    const workbook = createWorkbook(ExcelJS, kind, live, scope, selected, sort);
    const buffer = await workbook.xlsx.writeBuffer();
    assert.equal(buffer[0], 0x50);
    assert.equal(buffer[1], 0x4b);
    const loaded = new ExcelJS.Workbook();
    await loaded.xlsx.load(buffer);
    const sheet = loaded.worksheets[0];
    const expected = kind === "paths" ? sortPaths(pathRows(report), sort.key, sort.direction) : engineerRows(comparisonReport(live, scope, selected));
    assert.equal(sheet.rowCount, expected.length + 1);
    expected.forEach((row, index) => {
      const excelRow = sheet.getRow(index + 2);
      assert.equal(excelRow.getCell(kind === "paths" ? 3 : 2).value, kind === "paths" ? row.SapSupportPathL3 || "Unknown / not classified" : row.Engineer);
      assert.equal(excelRow.getCell(kind === "paths" ? 5 : 4).result, average(row, "DTCSum", "DTCRecords") ?? "No data");
      assert.equal(excelRow.getCell(kind === "paths" ? 7 : 6).result, average(row, "CSATSum", "SurveysCount") ?? "No data");
    });
    const context = loaded.getWorksheet("Report context");
    assert.equal(context.getCell("B4").value, scope);
    if (kind === "engineers") {
      const cases = loaded.getWorksheet("DTC cases");
      assert.equal(cases.rowCount - 1, expected.reduce((sum, row) => sum + row.DTCRecords, 0));
      cases.eachRow((row, index) => {
        if (index > 1) assert.equal(typeof row.getCell(2).text, "string");
      });
    }
    loaded.eachSheet(worksheet => worksheet.eachRow(row => row.eachCell(cell => {
      assert.equal(cell.type === ExcelJS.ValueType.Error, false);
      if (cell.type === ExcelJS.ValueType.Formula) {
        assert.ok(cell.value.formula.startsWith("IF("));
        assert.ok(typeof cell.result === "number" || cell.result === "No data");
      }
    })));
  }
});

test("empty and zero DTC export values are valid, and incomplete case exports fail explicitly", async () => {
  const sample = {
    ...data, dtcCases: [{ Scope: "noambi", Engineer: "Engineer A", IncidentId: "0001234567890123", SapSupportPathL2: "Linux", SapSupportPathL3: "Restart", DTCValue: 0 }],
    rows: [metrics("noambi", "Engineer A", 1, 0, 1), metrics("noambi", "Engineer B", 2, 0, 0)]
  };
  const loaded = new ExcelJS.Workbook();
  await loaded.xlsx.load(await createWorkbook(ExcelJS, "engineers", sample, "noambi").xlsx.writeBuffer());
  assert.equal(loaded.worksheets[0].getCell("D2").result, 0);
  assert.equal(loaded.getWorksheet("DTC cases").getCell("B2").value, "0001234567890123");
  assert.equal(loaded.worksheets[0].getCell("D3").result, "No data");
  const empty = createWorkbook(ExcelJS, "paths", { ...sample, rows: [] }, "noambi");
  assert.equal(empty.worksheets[0].rowCount, 1);
  assert.throws(() => createWorkbook(ExcelJS, "engineers", { ...sample, dtcCases: [] }, "noambi"), /Incomplete/);
});

test("All comparison aggregates by manager with weighted metrics and excludes zero-ticket rows", () => {
  const sample = {
    cohort: data.cohort,
    rows: [
      metrics("All", "Engineer A", 2, 2, 1),
      metrics("All", "Engineer B", 8, 90, 9),
      metrics("All", "Engineer K", 0, 0, 0)
    ]
  };
  const report = comparisonReport(sample, "All");
  const visible = engineerRows(report);
  assert.equal(visible.length, 1);
  assert.equal(visible[0].ManagerAlias, "noambi");
  assert.equal(visible[0].Tickets, 10);
  assert.equal(average(visible[0], "DTCSum", "DTCRecords"), 9.2);
  assert.equal(engineerRows(scopeReport(data, "bjames")).length, 0);
  const withTickets = metrics("noambi", "Engineer A", 2, 0, 0);
  assert.equal(engineerRows({ engineers: [withTickets] })[0].Rank, "-");
});

test("manager case lists match aggregated records and sums for every All path", () => {
  const live = globalThis.RCA_REPORT_DATA;
  for (const path of [null, ...scopeReport(live, "All").paths]) {
    const rows = engineerRows(comparisonReport(live, "All", path));
    const expected = scopeReport(live, "All", path).engineers;
    assert.equal(rows.reduce((sum, row) => sum + row.Tickets, 0), expected.reduce((sum, row) => sum + row.Tickets, 0));
    for (const row of rows) {
      const cases = comparisonCases(live, "All", row, path);
      assert.ok(cases.every(item => item.Scope === row.ManagerAlias));
      assert.equal(cases.length, row.DTCRecords);
      assert.ok(Math.abs(cases.reduce((sum, item) => sum + item.DTCValue, 0) - row.DTCSum) < 1e-8);
    }
  }
});

test("DFM links use only valid authoritative HTTPS source URLs", () => {
  const uri = "https://onesupport.crm.dynamics.com/main.aspx?pagetype=entityrecord&etn=incident&id=845f11e1-9db5-f111-aaac-3833c5e88e06";
  assert.equal(dfmLink(uri), uri);
  for (const invalid of ["", null, "javascript:alert(1)", "https://example.com", "https://onesupport.crm.dynamics.com.evil.test", "http://onesupport.crm.dynamics.com", "https://user:pass@onesupport.crm.dynamics.com"]) {
    assert.equal(dfmLink(invalid), null);
  }
  const example = globalThis.RCA_REPORT_DATA.dtcCases.find(row => row.IncidentId === "2609210030002648");
  assert.ok(example);
  assert.ok(dfmLink(example.CaseUri));
});

test("All manager Excel export matches aggregated comparison and preserves source DFM hyperlinks", async () => {
  const live = globalThis.RCA_REPORT_DATA;
  for (const selected of [null, scopeReport(live, "All").paths[0]]) {
    const workbook = createWorkbook(ExcelJS, "engineers", live, "All", selected);
    const loaded = new ExcelJS.Workbook();
    await loaded.xlsx.load(await workbook.xlsx.writeBuffer());
    const expected = engineerRows(comparisonReport(live, "All", selected));
    const sheet = loaded.getWorksheet("Manager comparison");
    assert.equal(sheet.getCell("B1").value, "Manager alias");
    assert.equal(sheet.rowCount, expected.length + 1);
    expected.forEach((row, index) => {
      assert.equal(sheet.getCell(`B${index + 2}`).value, row.ManagerAlias);
      assert.equal(sheet.getCell(`D${index + 2}`).result, average(row, "DTCSum", "DTCRecords") ?? "No data");
    });

    const cases = loaded.getWorksheet("DTC cases");
    assert.equal(cases.rowCount - 1, expected.reduce((sum, row) => sum + row.DTCRecords, 0));
    cases.eachRow((row, index) => {
      if (index === 1) return;
      const original = live.dtcCases.find(item => item.IncidentId === row.getCell(2).text);
      assert.equal(row.getCell(1).value, original.Scope);
      const link = dfmLink(original.CaseUri);
      if (link) assert.equal(row.getCell(2).value.hyperlink, link);
    });
  }
});

function initialClosureFixture() {
  const closures = [
    ["2609140030002725", "noambi", "Engineer D", "Linux", "Restart", 2],
    ["2600000000000002", "noambi", "Engineer D", "Linux", "Restart", 0],
    ["2600000000000003", "noambi", "Engineer A", "Linux", "Slow", 0],
    ["2600000000000004", "bjames", "Engineer K", "Linux", "Restart", 1]
  ].map(([IncidentId, Scope, Engineer, SapSupportPathL2, SapSupportPathL3, ReopenedCount]) => ({
    IncidentId, Scope, Engineer, SapSupportPathL2, SapSupportPathL3, ReopenedCount,
    InitialClosedAt: "2026-09-29T15:32:34.018Z",
    CaseUri: "https://onesupport.crm.dynamics.com/main.aspx?pagetype=entityrecord&etn=incident&id=d5c3d6aa-36b0-f111-aaac-7ced8d19e499"
  }));
  return {
    ...data,
    rows: data.rows.map(row => ({ ...row, ReopenKnownRecords: row.Tickets })),
    cohort: [...data.cohort, { Scope: "noambi", Engineer: "Engineer D" }, { Scope: "xinxia", Engineer: "Engineer AM" }],
    reopenAttribution: "Selected-manager reopened cases: DFM initial closer", closureVerifiedAt: "2026-10-10T00:00:00Z",
    reopenVerifiedScopes: ["noambi", "bjames"],
    reopenCandidates: closures.filter(row => row.ReopenedCount > 0).map(row => ({
      ...row, Engineer: row.Scope === "noambi" ? "Engineer B" : row.Engineer
    })),
    reopenCases: closures.filter(row => row.ReopenedCount > 0).map(row => ({
      ...row, CurrentScope: row.Scope, CurrentEngineer: row.Scope === "noambi" ? "Engineer B" : row.Engineer,
      CurrentOwnerMatchesInitial: row.Scope !== "noambi", OutsideRoster: false
    }))
  };
}

test("re-open credits initial closer, using current-ticket denominator; zero-ticket credits remain visible", () => {
  const fixture = initialClosureFixture();
  assert.equal(scopeReport(fixture, "noambi").engineers.find(row => row.Engineer === "Engineer D").Tickets, 0);
  const rows = reopenRows(reopenComparisonReport(fixture, "noambi"));
  const initialCloser = rows.find(row => row.Engineer === "Engineer D");
  assert.equal(initialCloser.Tickets, 0);
  assert.equal(initialCloser.ReopenRecords, 1);
  assert.equal(initialCloser.ReopenRate, null);
  assert.equal(comparisonCases(fixture, "noambi", initialCloser, null, "reopen")[0].IncidentId, "2609140030002725");
  assert.ok(!rows.some(row => row.Engineer === "Engineer C"));
  assert.equal(reopenComparisonReport(fixture, "All").engineers.find(row => row.ManagerAlias === "noambi").Tickets, 20);
  assert.equal(reopenComparisonReport(fixture, "noambi").engineers.find(row => row.Engineer === "Engineer B").ReopenRecords, 0);
  assert.deepEqual(scopeReport(fixture, "noambi").summary, scopeReport(data, "noambi").summary);
});

test("unresolved coverage stays visible, withholding affected rates and all-manager ranks", () => {
  const fixture = initialClosureFixture();
  const missing = reopenRows(reopenComparisonReport(fixture, "xinxia"));
  assert.equal(missing.length, 1);
  assert.equal(missing[0].ReopenRate, null);
  assert.equal(missing[0].Rank, "-");
  assert.ok(reopenRows(reopenComparisonReport(fixture, "All")).every(row => row.Rank === "-"));
  assert.equal(reopenRows(reopenComparisonReport(fixture, "noambi"))[0].Rank, 1);
});

test("legacy latest-owner snapshots cannot publish initial-closer rates or exports", () => {
  const legacy = { ...initialClosureFixture(), reopenAttribution: undefined };
  assert.throws(() => reopenComparisonReport(legacy, "All"), /Initial-closer evidence is unavailable/);
  assert.throws(() => createWorkbook(ExcelJS, "reopen", legacy, "All"), /Initial-closer evidence is unavailable/);
});

test("invalid or inconsistent initial-closure evidence is rejected", () => {
  const fixture = initialClosureFixture();
  assert.throws(() => reopenComparisonReport({ ...fixture, reopenCases: [...fixture.reopenCases, fixture.reopenCases[0]] }, "All"), /Duplicate/);
  assert.throws(() => reopenComparisonReport({ ...fixture, reopenCases: fixture.reopenCases.slice(1) }, "noambi"), /Incomplete/);
  assert.throws(() => reopenComparisonReport({ ...fixture, reopenCases: fixture.reopenCases.map(row => ({ ...row, Engineer: "Engineer ZZ" })) }, "All"), /Invalid/);
});

test("verified re-open case lists match every manager/engineer and support-path denominator", () => {
  const live = initialClosureFixture();
  assert.equal(new Set(live.reopenCases.map(row => row.IncidentId)).size, live.reopenCases.length);
  assert.ok(live.reopenCases.every(row => row.ReopenedCount > 0));
  for (const scope of ["All", ...new Set(live.cohort.map(row => row.Scope))]) {
    for (const path of [null, { SapSupportPathL2: "Linux", SapSupportPathL3: "Restart" }, { SapSupportPathL2: "Linux", SapSupportPathL3: "Slow" }]) {
      const report = reopenComparisonReport(live, scope, path);
      const ranked = reopenRows(report);
      const engineers = report.engineers;
      assert.equal(ranked.reduce((sum, row) => sum + row.ReopenRecords, 0), engineers.reduce((sum, row) => sum + row.ReopenRecords, 0));
      for (const row of ranked) {
        const cases = comparisonCases(live, scope, row, path, "reopen");
        assert.equal(cases.length, row.ReopenRecords);
        assert.ok(row.ReopenKnownRecords <= row.Tickets);
        assert.equal(row.ReopenRate, !row.CoverageIncomplete && row.Tickets > 0 && row.ReopenKnownRecords === row.Tickets ? cases.length / row.Tickets : null);
        if (path) assert.ok(cases.every(item => item.SapSupportPathL2 === path.SapSupportPathL2 && item.SapSupportPathL3 === path.SapSupportPathL3));
        assert.ok(cases.every(item => row.ManagerAlias ? item.Scope === row.ManagerAlias : item.Engineer === row.Engineer));
      }
    }
  }
});

test("re-open Excel exports preserve percentage formulas, source links, filters and zero values", async () => {
  const live = initialClosureFixture();
  for (const scope of ["All", "noambi", "bjames", "xinxia"]) {
    for (const path of [null, { SapSupportPathL2: "Linux", SapSupportPathL3: "Restart" }]) {
      const expected = reopenRows(reopenComparisonReport(live, scope, path));
      const loaded = new ExcelJS.Workbook();
      await loaded.xlsx.load(await createWorkbook(ExcelJS, "reopen", live, scope, path).xlsx.writeBuffer());
      const sheet = loaded.getWorksheet("Re-Open comparison");
      assert.equal(sheet.rowCount, expected.length + 1);
      expected.forEach((row, index) => {
        const cell = sheet.getCell(`D${index + 2}`);
        assert.equal(cell.result, row.ReopenRate ?? "No data");
        assert.equal(cell.numFmt, "0.0%");
        assert.ok(cell.value.formula.includes(`E${index + 2}/C${index + 2}`));
        if (row.CoverageIncomplete) {
          assert.equal(sheet.getCell(`C${index + 2}`).value, row.Tickets);
          assert.equal(sheet.getCell(`F${index + 2}`).value, -1);
        }
      });
      const cases = loaded.getWorksheet("Re-Open cases");
      assert.equal(cases.rowCount, expected.reduce((sum, row) => sum + row.ReopenRecords, 1));
      cases.eachRow((row, index) => {
        if (index === 1) return;
        const source = live.reopenCases.find(item => item.IncidentId === row.getCell(2).text);
        assert.ok(source);
        assert.equal(row.getCell(3).value, source.ReopenedCount);
        if (dfmLink(source.CaseUri)) assert.equal(row.getCell(2).value.hyperlink, dfmLink(source.CaseUri));
      });
    }
  }
  assert.throws(() => createWorkbook(ExcelJS, "reopen", { ...live, reopenCases: [] }, "All"), /Incomplete/);
});

test("outside-manager credits stay separate in manager, All, path and Excel views", async () => {
  const fixture = initialClosureFixture();
  const item = fixture.reopenCases[0];
  item.Scope = "bjames";
  item.Engineer = "Engineer K";
  item.CurrentOwnerMatchesInitial = false;
  for (const scope of ["noambi", "All"]) {
    const report = reopenComparisonReport(fixture, scope);
    assert.equal(report.outsideCases.length, 1);
    assert.equal(report.outsideCases[0].CurrentScope, "noambi");
    assert.equal(report.engineers.find(row => scope === "All" ? row.ManagerAlias === "noambi" : row.Engineer === "Engineer B").ReopenRecords, 0);
    if (scope === "All") assert.equal(report.engineers.find(row => row.ManagerAlias === "bjames").ReopenRecords, 1);
    const loaded = new ExcelJS.Workbook();
    await loaded.xlsx.load(await createWorkbook(ExcelJS, "reopen", fixture, scope).xlsx.writeBuffer());
    assert.equal(loaded.getWorksheet("Outside-manager credits").getCell("A2").text, item.IncidentId);
    assert.equal(loaded.getWorksheet("Outside-manager credits").getCell("E2").text, "Engineer K");
  }
  assert.equal(reopenComparisonReport(fixture, "bjames").outsideCases.length, 0);
  assert.equal(reopenComparisonReport(fixture, "noambi", { SapSupportPathL2: "Linux", SapSupportPathL3: "Slow" }).outsideCases.length, 0);
  item.Scope = null;
  item.Engineer = null;
  item.OutsideRoster = true;
  assert.equal(reopenComparisonReport(fixture, "noambi").outsideCases.length, 1);
  assert.equal(createWorkbook(ExcelJS, "reopen", fixture, "noambi").getWorksheet("Outside-manager credits").getCell("E2").text, "Outside roster (redacted)");
});

test("verified credits can exceed current ownership, without losing records or inventing a denominator", () => {
  const fixture = initialClosureFixture();
  fixture.rows.push({ ...metrics("noambi", "Engineer D", 1, 0, 0), ReopenKnownRecords: 1 });
  const extra = { ...fixture.reopenCases[0], IncidentId: "2600000000000005" };
  fixture.reopenCases.push(extra);
  fixture.reopenCandidates.push({ ...extra, Scope: extra.CurrentScope, Engineer: extra.CurrentEngineer });
  const row = reopenRows(reopenComparisonReport(fixture, "noambi")).find(item => item.Engineer === "Engineer D");
  assert.equal(row.Tickets, 1);
  assert.equal(row.ReopenRecords, 2);
  assert.equal(row.ReopenRate, 2);
  assert.equal(comparisonCases(fixture, "noambi", row, null, "reopen").length, 2);
});
