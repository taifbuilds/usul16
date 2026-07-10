[CmdletBinding(SupportsShouldProcess)]
param(
    [string]$DatabaseDirectory = (Join-Path $PSScriptRoot "..\eshia-research"),
    [ValidateRange(1, 1000)]
    [int]$KeepNewest = 7,
    [ValidateRange(0, 3650)]
    [int]$MinimumAgeDays = 14,
    [switch]$Apply
)

$ErrorActionPreference = "Stop"

$resolvedDirectory = (Resolve-Path -LiteralPath $DatabaseDirectory).Path
$liveDatabase = Join-Path $resolvedDirectory "eshia_research.db"
$cutoff = (Get-Date).AddDays(-$MinimumAgeDays)

$backups = Get-ChildItem -LiteralPath $resolvedDirectory -File |
    Where-Object {
        $_.FullName -ne $liveDatabase -and
        ($_.Name -like "eshia_research.before-*.db" -or
         $_.Name -like "eshia_research.backup-*.db" -or
         $_.Name -like "eshia_research.db.bak-*")
    } |
    Sort-Object LastWriteTime -Descending

$protected = @($backups | Select-Object -First $KeepNewest)
$candidates = @(
    $backups |
        Select-Object -Skip $KeepNewest |
        Where-Object { $_.LastWriteTime -lt $cutoff }
)

$totalBytes = ($backups | Measure-Object -Property Length -Sum).Sum
$candidateBytes = ($candidates | Measure-Object -Property Length -Sum).Sum

Write-Host "Database directory: $resolvedDirectory"
Write-Host "Live database (never touched): $liveDatabase"
Write-Host "Backups found: $($backups.Count) ($([math]::Round($totalBytes / 1GB, 2)) GiB)"
Write-Host "Protected newest backups: $($protected.Count)"
Write-Host "Eligible backups older than $MinimumAgeDays days: $($candidates.Count) ($([math]::Round($candidateBytes / 1GB, 2)) GiB)"

if (-not $candidates) {
    return
}

$candidates |
    Select-Object Name, LastWriteTime, @{Name = "GiB"; Expression = { [math]::Round($_.Length / 1GB, 2) }} |
    Format-Table -AutoSize

if (-not $Apply) {
    Write-Host "Dry run only. Re-run with -Apply to remove the listed snapshots."
    return
}

foreach ($candidate in $candidates) {
    if ($candidate.DirectoryName -ne $resolvedDirectory) {
        throw "Refusing to remove a file outside the database directory: $($candidate.FullName)"
    }
    if ($PSCmdlet.ShouldProcess($candidate.FullName, "Remove expired database snapshot")) {
        Remove-Item -LiteralPath $candidate.FullName
    }
}

