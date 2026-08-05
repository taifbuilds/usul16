$ErrorActionPreference = 'Stop'

$researchRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $researchRoot

$env:STORE_RAW_HTML_R2 = 'false'
$env:STORE_RAW_HTML = 'true'
$env:PYTHONIOENCODING = 'utf-8'

$logPath = Join-Path $PSScriptRoot 'mirat-al-uqul-crawl-20260728.err.log'
& .\.venv\Scripts\python.exe -m eshia_research.cli crawl-mirat-al-uqul --start-volume 1 --end-volume 26 --max-pages-per-volume 5000 --concurrency 3 *>> $logPath
& .\.venv\Scripts\python.exe -m eshia_research.cli index-mirat-al-uqul *>> $logPath
