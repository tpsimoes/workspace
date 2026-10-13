[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$OutputPath,
    [Parameter(Mandatory)][string]$ManagerAlias,
    [switch]$Resume,
    [switch]$RefreshReport
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type -AssemblyName System.Windows.Forms
Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class DfmEdgeFocus {
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr window);
    [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
}
'@

$account = 'tiagosimoes@techsupport.microsoft.com'
$base = 'https://onesupport.crm.dynamics.com/api/data/v9.2/'
$statePath = Join-Path $env:LOCALAPPDATA 'Microsoft\Edge\User Data\Local State'
$state = Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json -AsHashtable
$profiles = @($state.profile.info_cache.GetEnumerator() | Where-Object { $_.Value.user_name -eq $account })
if ($profiles.Count -ne 1) { throw "Expected exactly one Edge profile for $account." }
$edgePaths = @(
    "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe",
    "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe"
)
$edge = $edgePaths | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if (-not $edge) { throw 'Microsoft Edge was not found.' }
Start-Process -FilePath $edge -ArgumentList "--profile-directory=`"$($profiles[0].Key)`"", "`"$($base)WhoAmI`""
Start-Sleep -Seconds 2
$process = Get-Process -Name msedge | Where-Object { $_.MainWindowTitle -like '*WhoAmI*' } | Select-Object -First 1
if (-not $process) { throw 'The external TSE API tab is unavailable. Complete sign-in in external Edge first.' }
$window = [System.Windows.Automation.AutomationElement]::FromHandle($process.MainWindowHandle)
$window.GetCurrentPattern([System.Windows.Automation.WindowPattern]::Pattern).SetWindowVisualState(
    [System.Windows.Automation.WindowVisualState]::Normal
)
$textCondition = [System.Windows.Automation.PropertyCondition]::new(
    [System.Windows.Automation.AutomationElement]::ControlTypeProperty,
    [System.Windows.Automation.ControlType]::Text
)

function Read-BrowserJson {
    param([string]$Url, [string]$ExpectedIncident, [string]$PreviousFirstAudit, [string]$ExpectedAlias, [string]$ExpectedUserId)
    if (-not $Url.StartsWith($base, [StringComparison]::Ordinal)) { throw 'Only the DFM read-only API origin is allowed.' }
    $handle = [IntPtr]$window.Current.NativeWindowHandle
    if ([DfmEdgeFocus]::GetForegroundWindow() -ne $handle) {
        $pattern = $window.GetCurrentPattern([System.Windows.Automation.WindowPattern]::Pattern)
        $pattern.SetWindowVisualState([System.Windows.Automation.WindowVisualState]::Minimized)
        Start-Sleep -Milliseconds 300
        $pattern.SetWindowVisualState([System.Windows.Automation.WindowVisualState]::Normal)
        [void][DfmEdgeFocus]::SetForegroundWindow($handle)
    }
    if ([DfmEdgeFocus]::GetForegroundWindow() -ne $handle) {
        throw 'The approved external Edge window could not gain foreground focus. No keyboard input was sent.'
    }
    $address = $window.FindFirst(
        [System.Windows.Automation.TreeScope]::Descendants,
        [System.Windows.Automation.PropertyCondition]::new(
            [System.Windows.Automation.AutomationElement]::NameProperty, 'Address and search bar'
        )
    )
    if (-not $address) { throw 'External Edge address bar is unavailable.' }
    $address.SetFocus()
    $address.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).SetValue($Url)
    if ([DfmEdgeFocus]::GetForegroundWindow() -ne $handle) { throw 'External Edge lost foreground focus before navigation. No keyboard input was sent.' }
    [System.Windows.Forms.SendKeys]::SendWait('{ENTER}')
    Start-Sleep -Milliseconds 1500
    $navigatedUrl = $address.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).Current.Value
    if ([uri]::UnescapeDataString($navigatedUrl.Trim()) -ne [uri]::UnescapeDataString($Url)) {
        throw 'External Edge navigated to a different URL, possibly an autocomplete history suggestion. No response was accepted.'
    }
    $resourceName = ($Url.Substring($base.Length) -split '[?(]')[0]
    $deadline = [DateTime]::UtcNow.AddSeconds(120)
    $accessibilityRetries = 0
    do {
        try {
            $texts = $window.FindAll([System.Windows.Automation.TreeScope]::Descendants, $textCondition)
        }
        catch [System.Management.Automation.MethodInvocationException] {
            $failure = $_.Exception.InnerException
            if ($failure -isnot [System.Runtime.InteropServices.COMException] -or
                $failure.HResult -notin @(-2147467259, -2147418113, -2147220991) -or
                $accessibilityRetries -ge 3) { throw }
            $accessibilityRetries++
            Write-Warning "External Edge accessibility interface failed; reacquiring the same approved window (retry $accessibilityRetries/3)."
            Start-Sleep -Seconds 2
            $window = [System.Windows.Automation.AutomationElement]::FromHandle($handle)
            continue
        }
        foreach ($text in $texts) {
            $value = $text.Current.Name
            if ($value.StartsWith('{"error"')) { throw "DFM API rejected the request: $value" }
            if ($value.StartsWith('{"@odata.context"')) {
                $response = $value | ConvertFrom-Json -Depth 100
                if ($response.'@odata.context' -like "*$resourceName*") {
                    if ($ExpectedUserId -and $response.systemuserid -ne $ExpectedUserId) { continue }
                    if ($ExpectedAlias -and @($response.value | Where-Object {
                        ($_.domainname -split '@')[0] -ne $ExpectedAlias -and
                        ($_.internalemailaddress -split '@')[0] -ne $ExpectedAlias
                    }).Count) { continue }
                    if ($PreviousFirstAudit -and -not $ExpectedIncident -and $response.value.Count -and
                        $response.value[0].auditid -eq $PreviousFirstAudit) { continue }
                    if ($ExpectedIncident) {
                        $rows = @($response.AuditDetailCollection.AuditDetails)
                        if ($rows.Count -and @($rows | Where-Object { $_.AuditRecord._objectid_value -ne $ExpectedIncident }).Count) { continue }
                        if ($PreviousFirstAudit -and $rows.Count -and $rows[0].AuditRecord.auditid -eq $PreviousFirstAudit) { continue }
                    }
                    return $response
                }
            }
        }
        Start-Sleep -Milliseconds 300
    } while ([DateTime]::UtcNow -lt $deadline)
    throw 'DFM JSON response unavailable. Sign-in, access restrictions, or browser navigation requires attention. No token is extracted.'
}

function Save-Progress {
    $json = $result | ConvertTo-Json -Depth 30
    $temporary = "$OutputPath.tmp"
    [System.IO.File]::WriteAllText($temporary, $json, [System.Text.UTF8Encoding]::new($false))
    [System.IO.File]::Move($temporary, $OutputPath, $true)
}

$identity = Read-BrowserJson "$($base)WhoAmI"
$user = Read-BrowserJson "$($base)systemusers($($identity.UserId))?`$select=systemuserid,domainname" -ExpectedUserId $identity.UserId
if ($user.domainname -ne $account) { throw "DFM authenticated as $($user.domainname), not the requested TSE account." }
$rosterText = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'rca_standardization_FY27.kql') -Raw
$roster = @([regex]::Matches($rosterText, '"(?<alias>[^"]+)",\s*"(?<manager>[^"]+)",\s*"(?<engineer>Engineer [A-Z]+)"') | ForEach-Object {
    [pscustomobject]@{ Alias = $_.Groups['alias'].Value; Scope = $_.Groups['manager'].Value; Engineer = $_.Groups['engineer'].Value }
})
if ($roster.Count -eq 0) { throw 'The maintenance roster is empty.' }
if ($ManagerAlias -notin $roster.Scope) { throw 'Select one maintained manager alias; All does not trigger a broad audit scan.' }
$snapshotText = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'rca_standardization_FY27.data.js') -Raw
$snapshot = ($snapshotText -replace '^globalThis.RCA_REPORT_DATA\s*=\s*', '' -replace ';\s*$', '') | ConvertFrom-Json -Depth 100
$sourceCases = if ($null -ne $snapshot.reopenCandidates) { @($snapshot.reopenCandidates) } else { @($snapshot.reopenCases) }
$candidates = @($sourceCases | Where-Object { $_.Scope -eq $ManagerAlias -and $_.ReopenedCount -gt 0 })
$candidateIds = [System.Collections.Generic.HashSet[string]]::new()
foreach ($candidate in $candidates) {
    if (-not $candidateIds.Add($candidate.IncidentId)) { throw 'Duplicate candidate case ID in the snapshot.' }
    $uri = [uri]$candidate.CaseUri
    if ($uri.Scheme -ne 'https' -or $uri.Host -ne 'onesupport.crm.dynamics.com' -or
        $uri.Query -notmatch '(?:^\?|&)id=([0-9a-fA-F-]{36})(?:&|$)') { throw "No authoritative DFM GUID link for $($candidate.IncidentId)." }
    $candidate | Add-Member -NotePropertyName IncidentGuid -NotePropertyValue $Matches[1]
}
$result = [ordered]@{
    schemaVersion = 2
    managerAlias = $ManagerAlias
    snapshotGeneratedAt = $snapshot.generatedAt
    source = 'DFM RetrieveRecordChangeHistory via authenticated external Edge TSE profile'
    startedAt = [DateTime]::UtcNow.ToString('o')
    completedAt = $null
    complete = $false
    collectionComplete = $false
    candidateCount = $candidates.Count
    checkedCount = 0
    records = [System.Collections.Generic.List[object]]::new()
}
$checked = [System.Collections.Generic.HashSet[string]]::new()
if ($Resume) {
    if (-not (Test-Path -LiteralPath $OutputPath)) { throw 'Resume requires an existing private evidence file.' }
    $saved = Get-Content -LiteralPath $OutputPath -Raw | ConvertFrom-Json -Depth 100
    if ($saved.schemaVersion -ne 2 -or $saved.collectionComplete -or $saved.managerAlias -ne $ManagerAlias -or
        $saved.snapshotGeneratedAt -ne $snapshot.generatedAt) {
        throw 'Cannot resume completed, incompatible, or differently scoped evidence.'
    }
    foreach ($record in @($saved.records)) {
        if (-not $candidateIds.Contains($record.IncidentId)) { throw 'Candidate coverage changed; existing evidence cannot be resumed safely.' }
        if (-not $checked.Add($record.IncidentGuid)) { throw 'Duplicate incident in saved evidence.' }
        $result.records.Add($record)
    }
    $result.checkedCount = $checked.Count
    $result.startedAt = $saved.startedAt
    Write-Output "Resuming $($checked.Count) previously verified incident histories."
}
Save-Progress
Write-Output "Validating only $($candidates.Count) reopened cases currently assigned to $ManagerAlias directs."
$actors = @{}
foreach ($candidate in ($candidates | Sort-Object IncidentId)) {
    $id = $candidate.IncidentGuid
    if ($checked.Contains($id)) { continue }
    $details = [System.Collections.Generic.List[object]]::new()
    $page = 1
    $cookie = $null
    $previousFirstAudit = $null
    do {
        $target = [uri]::EscapeDataString((@{ '@odata.id' = "incidents($id)" } | ConvertTo-Json -Compress))
        $paging = @{ PageNumber = $page; Count = 100; ReturnTotalRecordCount = $true }
        if ($cookie) { $paging.PagingCookie = $cookie }
        $historyUrl = "$($base)RetrieveRecordChangeHistory(Target=@target,PagingInfo=@paginginfo)?@target=$target&@paginginfo=$([uri]::EscapeDataString(($paging | ConvertTo-Json -Compress)))"
        $history = (Read-BrowserJson $historyUrl $id $previousFirstAudit).AuditDetailCollection
        if ($null -eq $history -or $null -eq $history.MoreRecords) { throw "Invalid audit response for $id." }
        foreach ($detail in $history.AuditDetails) {
            if ($detail.AuditRecord._objectid_value -ne $id) { throw "Stale or mismatched browser response for $id." }
            $details.Add($detail)
        }
        $cookie = $history.PagingCookie
        if ($history.AuditDetails.Count) { $previousFirstAudit = $history.AuditDetails[0].AuditRecord.auditid }
        if ($history.MoreRecords -and -not $cookie) { throw "Missing audit paging cookie for $id." }
        $page++
    } while ($history.MoreRecords)
    if (@($details | Select-Object -ExpandProperty AuditRecord | Select-Object -ExpandProperty auditid -Unique).Count -ne $details.Count -or
        $history.TotalRecordCount -ne $details.Count) { throw "Incomplete or duplicate audit pagination for $id." }
    $creation = @($details | Where-Object { $_.AuditRecord.operation -eq 1 } | Sort-Object { $_.AuditRecord.createdon })
    $closures = @($details | Where-Object {
        $_.OldValue.statecode -eq 0 -and $_.NewValue.statecode -eq 1
    } | Sort-Object { $_.AuditRecord.createdon })
    if ($creation.Count -ne 1) { throw "Cannot verify full history from case creation for $id; audit retention or access may be incomplete." }
    $createdAt = $creation[0].NewValue.overriddencreatedon
    if (-not $createdAt) { $createdAt = $creation[0].AuditRecord.createdon }
    if ([datetimeoffset]$createdAt -lt [datetimeoffset]'2026-07-01T00:00:00Z' -or
        [datetimeoffset]$createdAt -ge [datetimeoffset]'2027-07-01T00:00:00Z' -or $closures.Count -eq 0) {
        throw "Candidate $($candidate.IncidentId) is not a verifiable FY27 initial closure."
    }
    $incidentId = $creation[0].NewValue.ticketnumber
    if ($incidentId -ne $candidate.IncidentId) { throw "Audit case number disagrees with candidate $($candidate.IncidentId)." }
    $actorId = $closures[0].AuditRecord._userid_value
    if ($actorId -notmatch '^[0-9a-fA-F-]{36}$') { throw "Missing or invalid initial closure actor for $incidentId." }
    if (-not $actors.ContainsKey($actorId)) {
        $actors[$actorId] = Read-BrowserJson "$($base)systemusers($actorId)?`$select=systemuserid,domainname,internalemailaddress,applicationid" -ExpectedUserId $actorId
    }
    $actor = $actors[$actorId]
    if ($actor.applicationid -or $actor.domainname -notmatch '^[^@\s]+@[^@\s]+$') {
        throw "Application/system initial closer for $incidentId requires Audit/Timeline confirmation. No owner substitution."
    }
    $aliases = @(@($actor.domainname, $actor.internalemailaddress) | Where-Object { $_ } | ForEach-Object {
        ($_ -split '@')[0].ToLowerInvariant()
    } | Where-Object { $_ -in $roster.Alias } | Select-Object -Unique)
    if ($aliases.Count -gt 1) { throw "Ambiguous initial closer for $incidentId." }
    $member = if ($aliases.Count) { $roster | Where-Object Alias -eq $aliases[0] } else { $null }
    $reopens = @($details | Where-Object {
        $_.OldValue.statecode -eq 1 -and $_.NewValue.statecode -eq 0 -and
        [datetimeoffset]$_.AuditRecord.createdon -gt [datetimeoffset]$closures[0].AuditRecord.createdon
    })
    if ($reopens.Count -ne $candidate.ReopenedCount) { throw "Source/audit reopen-count disagreement for $incidentId." }
    $result.records.Add([ordered]@{
            IncidentGuid = $id
            IncidentId = $incidentId
            InitialCloserAlias = if ($member) { $member.Alias } else { $null }
            Scope = if ($member) { $member.Scope } else { $null }
            Engineer = if ($member) { $member.Engineer } else { $null }
            OutsideRoster = -not [bool]$member
            InitialClosureActorId = $actorId
            CurrentScope = $candidate.Scope
            CurrentEngineer = $candidate.Engineer
            CurrentOwnerMatchesInitial = [bool]($member -and $member.Engineer -eq $candidate.Engineer)
            CreatedAt = $createdAt
            InitialClosedAt = $closures[0].AuditRecord.createdon
            ClosureAuditId = $closures[0].AuditRecord.auditid
            AuditReopenedCount = $reopens.Count
            AuditRows = $details.Count
            VerifiedAt = [DateTime]::UtcNow.ToString('o')
    })
    $result.checkedCount++
    Save-Progress
    Write-Output "Verified $($result.checkedCount)/$($result.candidateCount) reopened cases."
}
$result.collectionComplete = $true
$result.complete = $true
$result.completedAt = [DateTime]::UtcNow.ToString('o')
Save-Progress
Write-Output "Complete: $($result.records.Count) reopened cases for $ManagerAlias. Evidence saved to $OutputPath."
if ($RefreshReport) {
    & (Join-Path $PSScriptRoot 'refresh_rca_standardization.ps1') -ClosureEvidencePath $OutputPath
}
