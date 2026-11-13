$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
try {
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        throw 'Docker Desktop is required for PostgreSQL mode. Install/start Docker Desktop, or use START_BRAINTUMOR.cmd for local mode.'
    }
    & docker info *> $null
    if ($LASTEXITCODE -ne 0) { throw 'Docker is not running. Start Docker Desktop and try again.' }
    $dockerState = Join-Path $env:LOCALAPPDATA 'BrainTumorAI'
    New-Item -ItemType Directory -Force -Path $dockerState | Out-Null
    $dockerEnv = Join-Path $dockerState 'docker.env'
    if (-not (Test-Path -LiteralPath $dockerEnv)) {
        $databasePassword = $env:POSTGRES_PASSWORD
        if (-not $databasePassword) {
            $randomBytes = New-Object byte[] 24
            $generator = [System.Security.Cryptography.RandomNumberGenerator]::Create()
            try { $generator.GetBytes($randomBytes) } finally { $generator.Dispose() }
            $databasePassword = [Convert]::ToBase64String($randomBytes).Replace('+','-').Replace('/','_').TrimEnd('=')
        }
        if ($databasePassword -notmatch '^[A-Za-z0-9_-]+$') { throw 'POSTGRES_PASSWORD must use URL-safe letters, digits, underscores or hyphens.' }
        [System.IO.File]::WriteAllText($dockerEnv, ('POSTGRES_PASSWORD=' + $databasePassword + [Environment]::NewLine))
    }
    $savedPasswordLine = Get-Content -LiteralPath $dockerEnv | Where-Object { $_.StartsWith('POSTGRES_PASSWORD=') } | Select-Object -First 1
    if (-not $savedPasswordLine) { throw 'Saved Docker configuration has no POSTGRES_PASSWORD.' }
    $savedPassword = $savedPasswordLine.Substring('POSTGRES_PASSWORD='.Length)
    if ($env:POSTGRES_PASSWORD -and $env:POSTGRES_PASSWORD -ne $savedPassword) {
        throw 'POSTGRES_PASSWORD differs from the saved database configuration. Remove the shell override or use the matching value.'
    }
    Write-Host 'Starting PostgreSQL, FastAPI and the production interface...'
    & docker compose --env-file $dockerEnv up --build --detach --wait --wait-timeout 180
    if ($LASTEXITCODE -ne 0) { throw 'Docker startup failed. Inspect: docker compose logs' }
    $demoUrl = 'http://127.0.0.1:8080/'
    Start-Process $demoUrl
    Write-Host 'Ready: http://127.0.0.1:8080'
    Write-Host 'PostgreSQL data is persisted in the pgdata volume.'
    Write-Host 'To stop without deleting data, run scripts/stop-postgres.ps1.'
} catch {
    Write-Error $_
    exit 1
}
