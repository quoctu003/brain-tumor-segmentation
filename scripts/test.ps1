$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$projectPython = Join-Path $projectRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $projectPython)) { $projectPython = 'python' }
$testRoot = Join-Path $env:LOCALAPPDATA 'BrainTumorAI-tests'
New-Item -ItemType Directory -Force -Path $testRoot | Out-Null
$testDirectory = [System.IO.Path]::GetFullPath((Join-Path $testRoot ('run-' + [guid]::NewGuid().ToString('N'))))
if (-not $testDirectory.StartsWith($testRoot + '\', [System.StringComparison]::OrdinalIgnoreCase)) {
    throw 'Unexpected test workspace'
}
Set-Location (Join-Path $projectRoot 'backend')
& $projectPython -m pytest tests -q --tb=short --basetemp $testDirectory
exit $LASTEXITCODE
