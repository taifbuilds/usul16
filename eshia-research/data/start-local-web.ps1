$ErrorActionPreference = 'Stop'

$researchRoot = Split-Path -Parent $PSScriptRoot
$workspaceRoot = Split-Path -Parent $researchRoot
$webRoot = Join-Path $workspaceRoot 'web'
Set-Location -LiteralPath $webRoot

$logPath = Join-Path $PSScriptRoot 'local-web.log'
& node .\node_modules\next\dist\bin\next dev . --webpack --port 3000 *>> $logPath
