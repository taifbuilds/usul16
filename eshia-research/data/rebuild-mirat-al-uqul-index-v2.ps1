$ErrorActionPreference = 'Stop'

$researchRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $researchRoot

$env:PYTHONIOENCODING = 'utf-8'
$logPath = Join-Path $PSScriptRoot 'mirat-al-uqul-index-v2-20260728.log'

& .\.venv\Scripts\python.exe -m eshia_research.cli index-mirat-al-uqul *>> $logPath
if ($LASTEXITCODE -eq 0) {
    "completed_at=$(Get-Date -Format o)" | Add-Content -LiteralPath $logPath
}
