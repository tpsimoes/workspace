[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$bodyPath = [System.IO.Path]::GetTempFileName()
$responsePath = [System.IO.Path]::GetTempFileName()
try {
    $queryPath = Join-Path $PSScriptRoot 'rca_standardization_FY27.kql'
    $body = @{
        db = 'KPISupportData'
        csl = Get-Content -LiteralPath $queryPath -Raw
    } | ConvertTo-Json -Compress
    [System.IO.File]::WriteAllText($bodyPath, $body)
    & az rest --method post `
        --uri 'https://supportrptwus3prod.westus3.kusto.windows.net/v2/rest/query' `
        --resource 'https://kusto.kusto.windows.net' `
        --headers 'Content-Type=application/json' `
        --body "@$bodyPath" --output-file $responsePath --only-show-errors
    if ($LASTEXITCODE -ne 0) {
        throw "Kusto export failed (Azure CLI exit code $LASTEXITCODE). Existing report data was not changed."
    }
    $response = Get-Content -LiteralPath $responsePath -Raw | ConvertFrom-Json
    $completion = @($response | Where-Object FrameType -eq 'DataSetCompletion')
    if ($completion.Count -ne 1 -or $completion[0].HasErrors -or $completion[0].Cancelled) {
        throw "Kusto returned an incomplete or failed query. Existing report data was not changed. $($completion | ConvertTo-Json -Depth 20 -Compress)"
    }
    $primary = @($response | Where-Object { $_.FrameType -eq 'DataTable' -and $_.TableKind -eq 'PrimaryResult' })
    if ($primary.Count -ne 1 -or $primary[0].Rows.Count -ne 1) {
        throw 'Expected exactly one primary payload row; report data was not changed.'
    }
    $payload = $primary[0].Rows[0][0]
    if ($payload -is [string]) { $payload = $payload | ConvertFrom-Json }
    if ($null -eq $payload.rows -or $null -eq $payload.cohort -or $null -eq $payload.dtcCases) {
        throw 'Report payload lacks rows, cohort, or DTC cases; report data was not changed.'
    }
    $caseIds = [System.Collections.Generic.HashSet[string]]::new()
    foreach ($case in $payload.dtcCases) {
        if ([string]::IsNullOrWhiteSpace($case.IncidentId) -or -not $caseIds.Add($case.IncidentId)) {
            throw 'DTC cases contain empty or duplicate case IDs; report data was not changed.'
        }
    }
    foreach ($engineer in @($payload.rows | Where-Object Kind -eq 'Engineer')) {
        $matching = @($payload.dtcCases | Where-Object {
            $_.Engineer -eq $engineer.Engineer -and ($engineer.Scope -eq 'All' -or $_.Scope -eq $engineer.Scope)
        })
        if ($matching.Count -ne $engineer.DTCRecords) {
            throw "DTC case list is incomplete for $($engineer.Scope) / $($engineer.Engineer); report data was not changed."
        }
    }
    $dataPath = Join-Path $PSScriptRoot 'rca_standardization_FY27.data.js'
    $json = $payload | ConvertTo-Json -Depth 30 -Compress
    [System.IO.File]::WriteAllText($dataPath, "globalThis.RCA_REPORT_DATA = $json;`n", [System.Text.UTF8Encoding]::new($false))
    Write-Output "Refreshed $dataPath ($($payload.rows.Count) aggregate rows)."
}
finally {
    Remove-Item -LiteralPath $bodyPath, $responsePath -ErrorAction SilentlyContinue
}
