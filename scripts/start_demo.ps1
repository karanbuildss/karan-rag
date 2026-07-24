param(
    [switch]$SkipIngestion,
    [switch]$SkipIndexing
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$BackendRoot = Join-Path $ProjectRoot 'backend'
$FrontendRoot = Join-Path $ProjectRoot 'frontend'
$IdentityRoot = Join-Path $ProjectRoot 'mock-identity-server'
$PythonExe = Join-Path $BackendRoot '.venv\Scripts\python.exe'

if (-not (Test-Path -LiteralPath $PythonExe)) {
    throw 'backend\.venv is missing. Create it and install requirements.txt first.'
}
if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) {
    throw 'Ollama is not available on PATH.'
}
if (-not (Get-Command npm.cmd -ErrorAction SilentlyContinue)) {
    throw 'npm.cmd is not available on PATH.'
}
if (-not (Test-Path -LiteralPath (Join-Path $FrontendRoot 'node_modules'))) {
    throw 'frontend\node_modules is missing. Run npm.cmd install in frontend first.'
}

& ollama show qwen2.5:3b | Out-Null
& ollama show nomic-embed-text-v2-moe | Out-Null
& $PythonExe (Join-Path $ProjectRoot 'scripts\bootstrap_local_security.py')
if (-not (Test-Path -LiteralPath (Join-Path $FrontendRoot '.env'))) {
    Copy-Item -LiteralPath (Join-Path $FrontendRoot '.env.example') -Destination (Join-Path $FrontendRoot '.env')
}

Push-Location $BackendRoot
try {
    & $PythonExe manage.py migrate --noinput
    & $PythonExe manage.py seed_demo_data
    if (-not $SkipIngestion) {
        & $PythonExe manage.py ingest_evidence
        & $PythonExe manage.py import_reviewed_budget_facts
    }
    if (-not $SkipIndexing) {
        & $PythonExe manage.py index_project_evidence --all-projects --extract-linked-pages
    }
    & $PythonExe manage.py detect_anomalies
    & $PythonExe manage.py check
}
finally {
    Pop-Location
}

$BackendLog = Join-Path $ProjectRoot 'backend-demo.log'
$BackendError = Join-Path $ProjectRoot 'backend-demo.err.log'
$IdentityLog = Join-Path $ProjectRoot 'identity-demo.log'
$IdentityError = Join-Path $ProjectRoot 'identity-demo.err.log'
$FrontendLog = Join-Path $ProjectRoot 'frontend-demo.log'
$FrontendError = Join-Path $ProjectRoot 'frontend-demo.err.log'

Start-Process -FilePath $PythonExe -ArgumentList @('manage.py', 'runserver', '127.0.0.1:8000') -WorkingDirectory $BackendRoot -WindowStyle Hidden -RedirectStandardOutput $BackendLog -RedirectStandardError $BackendError
Start-Process -FilePath $PythonExe -ArgumentList @('manage.py', 'runserver', '127.0.0.1:8001') -WorkingDirectory $IdentityRoot -WindowStyle Hidden -RedirectStandardOutput $IdentityLog -RedirectStandardError $IdentityError
Start-Process -FilePath npm.cmd -ArgumentList @('run', 'dev', '--', '--host', '127.0.0.1') -WorkingDirectory $FrontendRoot -WindowStyle Hidden -RedirectStandardOutput $FrontendLog -RedirectStandardError $FrontendError

Write-Host 'Budget Darpan demo services are starting:'
Write-Host '  App:       http://localhost:5173'
Write-Host '  API:       http://localhost:8000/api/v1/health/'
Write-Host '  API docs:  http://localhost:8000/api/docs/'
Write-Host '  Mock ID:   http://localhost:8001'
Write-Host 'Demo identity: 9800000001 / TEST-PKR-0001 / OTP 123456'
