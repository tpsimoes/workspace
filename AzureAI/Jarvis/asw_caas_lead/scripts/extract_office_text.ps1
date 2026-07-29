# Extract text from MIP-protected pptx/xlsx via Office COM automation.
# Requires Office desktop installed and current user has decrypt permission.
param(
    [Parameter(Mandatory=$true)][string]$In,
    [Parameter(Mandatory=$true)][string]$Out
)

$ErrorActionPreference = "Stop"
$In = (Resolve-Path $In).Path
$ext = [IO.Path]::GetExtension($In).ToLower()

if ($ext -in @(".pptx", ".ppt")) {
    $ppt = New-Object -ComObject PowerPoint.Application
    # PowerPoint requires Visible for some operations
    $ppt.Visible = [Microsoft.Office.Core.MsoTriState]::msoTrue
    try {
        $pres = $ppt.Presentations.Open($In, [Microsoft.Office.Core.MsoTriState]::msoTrue, [Microsoft.Office.Core.MsoTriState]::msoTrue, [Microsoft.Office.Core.MsoTriState]::msoFalse)
        $sb = New-Object System.Text.StringBuilder
        $null = $sb.AppendLine("# $([IO.Path]::GetFileName($In))")
        $null = $sb.AppendLine("_slides: $($pres.Slides.Count)_")
        $null = $sb.AppendLine("")
        for ($i = 1; $i -le $pres.Slides.Count; $i++) {
            $slide = $pres.Slides.Item($i)
            $null = $sb.AppendLine("## Slide $i")
            foreach ($shape in $slide.Shapes) {
                try {
                    if ($shape.HasTextFrame -eq -1 -and $shape.TextFrame.HasText -eq -1) {
                        $t = $shape.TextFrame.TextRange.Text
                        if ($t) {
                            $lines = $t -split "[`r`n`v]+" | Where-Object { $_.Trim() -ne "" }
                            foreach ($l in $lines) { $null = $sb.AppendLine("- $($l.Trim())") }
                        }
                    }
                } catch {}
                try {
                    if ($shape.HasTable -eq -1) {
                        $tbl = $shape.Table
                        $rows = $tbl.Rows.Count
                        $cols = $tbl.Columns.Count
                        $null = $sb.AppendLine("")
                        for ($r = 1; $r -le $rows; $r++) {
                            $rowText = @()
                            for ($c = 1; $c -le $cols; $c++) {
                                $ct = $tbl.Cell($r, $c).Shape.TextFrame.TextRange.Text
                                $rowText += (($ct -replace "[`r`n`v]+", " ").Trim())
                            }
                            $null = $sb.AppendLine("| " + ($rowText -join " | ") + " |")
                            if ($r -eq 1) { $null = $sb.AppendLine("|" + (("---|") * $cols)) }
                        }
                        $null = $sb.AppendLine("")
                    }
                } catch {}
            }
            # Notes
            try {
                if ($slide.HasNotesPage -eq -1) {
                    $notes = ""
                    foreach ($ns in $slide.NotesPage.Shapes) {
                        if ($ns.HasTextFrame -eq -1 -and $ns.TextFrame.HasText -eq -1) {
                            $nt = $ns.TextFrame.TextRange.Text
                            if ($nt -and $nt.Trim() -ne "") { $notes += "`n" + $nt.Trim() }
                        }
                    }
                    if ($notes.Trim()) { $null = $sb.AppendLine(""); $null = $sb.AppendLine("> **Notes:** " + $notes.Trim()) }
                }
            } catch {}
            $null = $sb.AppendLine("")
        }
        [IO.File]::WriteAllText($Out, $sb.ToString(), [Text.Encoding]::UTF8)
        $pres.Close()
    } finally {
        $ppt.Quit()
        [System.Runtime.InteropServices.Marshal]::ReleaseComObject($ppt) | Out-Null
    }
} elseif ($ext -in @(".xlsx", ".xls")) {
    $excel = New-Object -ComObject Excel.Application
    $excel.Visible = $false
    $excel.DisplayAlerts = $false
    try {
        $wb = $excel.Workbooks.Open($In, 0, $true) # ReadOnly=$true
        $sb = New-Object System.Text.StringBuilder
        $null = $sb.AppendLine("# $([IO.Path]::GetFileName($In))")
        $sheetNames = @()
        foreach ($ws in $wb.Worksheets) { $sheetNames += $ws.Name }
        $null = $sb.AppendLine("_sheets: $($sheetNames -join ', ')_")
        $null = $sb.AppendLine("")
        foreach ($ws in $wb.Worksheets) {
            $null = $sb.AppendLine("## Sheet: $($ws.Name)")
            $used = $ws.UsedRange
            $rows = if ($used) { $used.Rows.Count } else { 0 }
            $cols = if ($used) { $used.Columns.Count } else { 0 }
            $null = $sb.AppendLine("_dims: $rows rows x $cols cols_")
            if ($rows -gt 0 -and $cols -gt 0) {
                $maxR = [Math]::Min($rows, 50)
                $vals = $used.Value2
                for ($r = 1; $r -le $maxR; $r++) {
                    $rowVals = @()
                    for ($c = 1; $c -le $cols; $c++) {
                        $v = if ($rows -eq 1 -and $cols -eq 1) { $vals } elseif ($rows -eq 1) { $vals[1,$c] } elseif ($cols -eq 1) { $vals[$r,1] } else { $vals[$r,$c] }
                        if ($null -eq $v) { $rowVals += "" }
                        else { $rowVals += (($v.ToString() -replace "[`r`n`v]+", " ").Substring(0, [Math]::Min(80, $v.ToString().Length))) }
                    }
                    $null = $sb.AppendLine("| " + ($rowVals -join " | ") + " |")
                }
                if ($rows -gt $maxR) { $null = $sb.AppendLine("... ($($rows - $maxR) more rows)") }
            }
            $null = $sb.AppendLine("")
        }
        [IO.File]::WriteAllText($Out, $sb.ToString(), [Text.Encoding]::UTF8)
        $wb.Close($false)
    } finally {
        $excel.Quit()
        [System.Runtime.InteropServices.Marshal]::ReleaseComObject($excel) | Out-Null
    }
} else {
    throw "Unsupported file type: $ext"
}

Write-Host "Wrote: $Out"
