$ErrorActionPreference = 'Stop'

$researchRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $researchRoot

$env:DATABASE_URL = 'sqlite:///./eshia_research.local-server.db'
$env:PYTHONIOENCODING = 'utf-8'

$logPath = Join-Path $PSScriptRoot 'local-api.log'
& .\.venv\Scripts\python.exe -m uvicorn eshia_research.api.main:app --host 127.0.0.1 --port 8000 *>> $logPath
