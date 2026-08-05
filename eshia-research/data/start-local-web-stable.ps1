$ErrorActionPreference = 'Stop'

$researchRoot = Split-Path -Parent $PSScriptRoot
$workspaceRoot = Split-Path -Parent $researchRoot
$webRoot = Join-Path $workspaceRoot 'web'
Set-Location -LiteralPath $webRoot

$logPath = Join-Path $PSScriptRoot 'local-web-stable.log'
& node .\node_modules\next\dist\bin\next start . --hostname 127.0.0.1 --port 3001 *>> $logPath
