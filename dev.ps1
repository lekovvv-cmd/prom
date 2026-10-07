[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [ValidateSet("up", "down", "restart", "logs", "status", "reset", "test", "test-unit", "test-integration", "test-e2e", "generate-contracts", "architecture-check", "create-module", "migrate-identities")]
    [string]$Command = "up",

    [Parameter(Position = 1, ValueFromRemainingArguments = $true)]
    [string[]]$Services = @()
)

$ErrorActionPreference = "Stop"
$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Path

function Invoke-PromPython {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Arguments)

    $workspacePython = Join-Path $RootDir ".venv\Scripts\python.exe"
    if (Test-Path -LiteralPath $workspacePython) {
        & $workspacePython @Arguments
        return
    }
    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) {
        & $py.Source -3.14 @Arguments
    }
    else {
        & python3 @Arguments
    }
}

Push-Location $RootDir
try {
    $DockerCommands = @("up", "down", "restart", "logs", "status", "reset", "test", "test-integration", "migrate-identities")
    if ($DockerCommands -contains $Command) {
        if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
            throw "Docker Desktop is required for '$Command'."
        }
        & docker info *> $null
        if ($LASTEXITCODE -ne 0) {
            throw "Docker is not running. Start Docker Desktop and try again."
        }
    }

    switch ($Command) {
        "up" {
            & docker compose up -d --wait postgres
            if ($LASTEXITCODE -ne 0) { throw "PostgreSQL startup failed." }
            Invoke-PromPython tools/postgres/ensure_generated_databases.py
            if ($LASTEXITCODE -ne 0) { throw "Generated module database setup failed." }
            if ($env:PROM_SKIP_LEGACY_IMPORT -ne "1") {
                Invoke-PromPython tools/postgres/import_legacy_databases.py
                if ($LASTEXITCODE -ne 0) { throw "Legacy local database import failed." }
            }
            foreach ($service in @("access-service", "projects-backend", "service-desk-backend", "platform-shell")) {
                & docker compose build $service
                if ($LASTEXITCODE -ne 0) { throw "Docker image build failed: $service" }
            }
            foreach ($job in @("access-migrate", "projects-migrate", "service-desk-migrate", "access-seed", "projects-seed", "platform-bootstrap", "service-desk-seed")) {
                & docker compose --profile tooling run --rm --no-deps $job
                if ($LASTEXITCODE -ne 0) { throw "One-shot job '$job' failed." }
            }
            Get-ChildItem -Path (Join-Path $RootDir "apps") -Directory | ForEach-Object {
                if (Test-Path -LiteralPath (Join-Path $_.FullName "platform/registration.json")) {
                    & docker compose build "$($_.Name)-backend"
                    if ($LASTEXITCODE -ne 0) { throw "Generated module build failed: $($_.Name)" }
                    & docker compose --profile tooling run --rm --no-deps "$($_.Name)-migrate"
                    if ($LASTEXITCODE -ne 0) { throw "Generated module migration failed: $($_.Name)" }
                }
            }
            & docker compose up -d --wait --remove-orphans
            if ($LASTEXITCODE -ne 0) {
                & docker compose ps
                & docker compose logs --tail 200
                throw "Docker Compose startup failed."
            }
            & docker compose ps
            Write-Host ""
            Write-Host "PROM:                 http://localhost:5173/" -ForegroundColor Green
            Write-Host "Projects:             http://localhost:5173/projects"
            Write-Host "Service Desk:         http://localhost:5173/service-desk"
            Write-Host "Access API:           http://localhost:5173/api/access/v1/"
            Write-Host "Projects API:         http://localhost:5173/api/projects/v1/"
            Write-Host "Service Desk API:     http://localhost:5173/api/service-desk/v1/"
        }
        "down" { & docker compose down }
        "restart" { & docker compose restart @Services }
        "logs" { & docker compose logs --follow --tail 200 @Services }
        "status" { & docker compose ps }
        "reset" {
            Write-Warning "This removes the shared local PROM database and attachment volumes."
            & docker compose down --volumes --remove-orphans
            if ($LASTEXITCODE -ne 0) { throw "Docker Compose reset failed." }
            $previousSkip = $env:PROM_SKIP_LEGACY_IMPORT
            try {
                $env:PROM_SKIP_LEGACY_IMPORT = "1"
                & $PSCommandPath up
            }
            finally {
                $env:PROM_SKIP_LEGACY_IMPORT = $previousSkip
            }
        }
        "test" {
            & docker compose --profile test run --rm projects-tests
            if ($LASTEXITCODE -ne 0) { throw "Projects tests failed." }
            & docker compose --profile test run --rm service-desk-tests
            if ($LASTEXITCODE -ne 0) { throw "Service Desk tests failed." }
            & docker compose --profile test run --rm frontend-tests
            if ($LASTEXITCODE -ne 0) { throw "Frontend tests failed." }
        }
        "test-unit" { & npm.cmd run test }
        "test-integration" {
            & docker compose --profile test run --rm projects-tests
            if ($LASTEXITCODE -eq 0) { & docker compose --profile test run --rm service-desk-tests }
        }
        "test-e2e" { & npm.cmd run test:e2e --workspace=@prom/platform-shell }
        "generate-contracts" { & npm.cmd run generate:contracts }
        "architecture-check" { Invoke-PromPython tools/architecture/check.py }
        "create-module" {
            if ($Services.Count -lt 1 -or $Services.Count -gt 2) { throw "Usage: .\dev.cmd create-module <module-name> [--dry-run|--check|--remove]" }
            Invoke-PromPython tools/generators/create_module.py @Services
        }
        "migrate-identities" {
            if ($Services.Count -ne 1 -or $Services[0] -notin @("--dry-run", "--apply")) {
                throw "Usage: .\dev.cmd migrate-identities {--dry-run|--apply}"
            }
            New-Item -ItemType Directory -Force -Path (Join-Path $RootDir "outputs/identity-migration") | Out-Null
            & docker compose --profile tooling run --rm --no-deps access-identity-migrate $Services[0]
        }
    }

    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code $LASTEXITCODE."
    }
}
finally {
    Pop-Location
}
