$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$dockerEnv = Join-Path $env:LOCALAPPDATA 'BrainTumorAI/docker.env'
if (-not (Test-Path -LiteralPath $dockerEnv)) { throw 'No PostgreSQL launcher configuration exists.' }
Set-Location -LiteralPath $projectRoot
# Keep pgdata and casefiles; no volume deletion.
& docker compose --env-file $dockerEnv down
exit $LASTEXITCODE
