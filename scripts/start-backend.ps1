$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$localStorage = Join-Path $env:LOCALAPPDATA 'BrainTumorAI/storage'
if (-not $env:STORAGE_DIR) { $env:STORAGE_DIR = $localStorage }
if (-not $env:DATABASE_URL) { $env:DATABASE_URL = 'sqlite:///' + ((Join-Path $localStorage 'braintumor.db') -replace '\\', '/') }
$projectPython = Join-Path $projectRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $projectPython)) { $projectPython = 'python' }
Set-Location (Join-Path $projectRoot 'backend')
# One process: the inference queue is owned by this API instance.
& $projectPython -m uvicorn app.main:app --host 127.0.0.1 --port 8000
