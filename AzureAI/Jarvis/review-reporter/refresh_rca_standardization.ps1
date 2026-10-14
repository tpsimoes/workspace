[CmdletBinding()]
param([Parameter(Mandatory)][string]$ClosureEvidencePath)

$ErrorActionPreference = 'Stop'
$evidence = Get-Content -LiteralPath $ClosureEvidencePath -Raw | ConvertFrom-Json -Depth 100
if ($evidence.schemaVersion -ne 2 -or -not $evidence.collectionComplete -or -not $evidence.complete -or
    $evidence.checkedCount -ne $evidence.candidateCount -or @($evidence.records).Count -ne $evidence.checkedCount -or
    -not $evidence.completedAt) {
    throw 'Selected-manager re-open evidence collection is incomplete; existing report data was not changed.'
}
$dataPath = Join-Path $PSScriptRoot 'rca_standardization_FY27.data.js'
$text = Get-Content -LiteralPath $dataPath -Raw
$payload = ($text -replace '^globalThis.RCA_REPORT_DATA\s*=\s*', '' -replace ';\s*$', '') | ConvertFrom-Json -Depth 100
if ($payload.generatedAt -ne $evidence.snapshotGeneratedAt -or $evidence.managerAlias -notin $payload.cohort.Scope) {
    throw 'Evidence does not match the current snapshot or maintained manager; report data was not changed.'
}
$candidates = if ($null -ne $payload.reopenCandidates) { @($payload.reopenCandidates) } else { @($payload.reopenCases) }
$selected = @($candidates | Where-Object Scope -eq $evidence.managerAlias)
if ($selected.Count -ne $evidence.candidateCount) { throw 'Selected-manager candidate coverage changed.' }
$ids = [System.Collections.Generic.HashSet[string]]::new()
$verified = foreach ($record in $evidence.records) {
    $source = @($selected | Where-Object IncidentId -eq $record.IncidentId)
    if (-not $ids.Add($record.IncidentId) -or $source.Count -ne 1 -or
        $record.CurrentScope -ne $source[0].Scope -or $record.CurrentEngineer -ne $source[0].Engineer -or
        $record.AuditReopenedCount -ne $source[0].ReopenedCount -or $record.AuditReopenedCount -le 0 -or
        -not $record.ClosureAuditId -or -not $record.InitialClosureActorId -or -not $record.InitialClosedAt) {
        throw "Invalid or mismatched attribution for $($record.IncidentId); report data was not changed."
    }
    $uri = [uri]$source[0].CaseUri
    if ($uri.Scheme -ne 'https' -or $uri.Host -ne 'onesupport.crm.dynamics.com' -or
        $uri.Query -notmatch '(?:^\?|&)id=([0-9a-fA-F-]{36})(?:&|$)' -or $Matches[1] -ne $record.IncidentGuid) {
        throw "Evidence incident GUID disagrees with source DFM link for $($record.IncidentId)."
    }
    $member = @($payload.cohort | Where-Object { $_.Scope -eq $record.Scope -and $_.Engineer -eq $record.Engineer })
    if ((-not $record.OutsideRoster -and $member.Count -ne 1) -or
        ($record.OutsideRoster -and ($record.Scope -or $record.Engineer))) { throw 'Invalid initial-closer roster mapping.' }
    $sameOwner = [bool](-not $record.OutsideRoster -and $record.Engineer -eq $source[0].Engineer)
    if ($record.CurrentOwnerMatchesInitial -ne $sameOwner) { throw 'Owner comparison disagrees with verified initial closer.' }
    [pscustomobject]@{
        IncidentId = $source[0].IncidentId
        CaseUri = $source[0].CaseUri
        SapSupportPathL2 = $source[0].SapSupportPathL2
        SapSupportPathL3 = $source[0].SapSupportPathL3
        ReopenedCount = $source[0].ReopenedCount
        Scope = $record.Scope
        Engineer = $record.Engineer
        CurrentScope = $source[0].Scope
        CurrentEngineer = $source[0].Engineer
        CurrentOwnerMatchesInitial = $sameOwner
        OutsideRoster = [bool]$record.OutsideRoster
        InitialClosedAt = ([datetimeoffset]$record.InitialClosedAt).UtcDateTime.ToString('o')
        VerifiedAt = $record.VerifiedAt
    }
}
$existing = if ($payload.reopenAttribution -eq 'Selected-manager reopened cases: DFM initial closer') {
    @($payload.reopenCases | Where-Object CurrentScope -ne $evidence.managerAlias)
} else { @() }
$coverage = if ($payload.reopenVerifiedScopes) { @($payload.reopenVerifiedScopes) } else { @() }
$coverage = @(@($coverage) + @($evidence.managerAlias) | Select-Object -Unique)
$payload | Add-Member -Force -NotePropertyName reopenCandidates -NotePropertyValue @($candidates)
$payload | Add-Member -Force -NotePropertyName reopenCases -NotePropertyValue @(@($existing) + @($verified))
$payload | Add-Member -Force -NotePropertyName reopenVerifiedScopes -NotePropertyValue $coverage
$payload | Add-Member -Force -NotePropertyName reopenAttribution -NotePropertyValue 'Selected-manager reopened cases: DFM initial closer'
$payload | Add-Member -Force -NotePropertyName reopenDenominator -NotePropertyValue 'Currently assigned FY27 tickets'
$payload | Add-Member -Force -NotePropertyName closureVerifiedAt -NotePropertyValue $evidence.completedAt
$payload.PSObject.Properties.Remove('closureCases')
$payload.PSObject.Properties.Remove('reopenIncompleteScopes')
$json = $payload | ConvertTo-Json -Depth 100 -Compress
$temporary = "$dataPath.tmp"
[System.IO.File]::WriteAllText($temporary, "globalThis.RCA_REPORT_DATA = $json;`n", [System.Text.UTF8Encoding]::new($false))
[System.IO.File]::Move($temporary, $dataPath, $true)
& node (Join-Path $PSScriptRoot 'build_shareable_report.js')
if ($LASTEXITCODE -ne 0) { throw 'Report data was updated, but the shareable HTML build failed.' }
Write-Output "Updated $($evidence.managerAlias): $($verified.Count) reopened cases verified; current-ticket metrics unchanged."
