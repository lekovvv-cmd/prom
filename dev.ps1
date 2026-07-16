[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [ValidateSet("up", "down", "restart", "logs", "status", "reset", "test", "test-unit", "test-integration", "test-e2e", "generate-contracts", "architecture-check", "create-module")]
    [string]$Command = "up",

    [Parameter(Position = 1, ValueFromRemainingArguments = $true)]
    [string[]]$Services = @()
)

$ErrorActionPreference = "Stop"
$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Path

function Invoke-PromPython {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Arguments)

    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) {
        & $py.Source -3.14 @Arguments
    }
    else {
        & python3 @Arguments
    }
}

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Docker Desktop is required. Install it and make sure Docker is running."
}

Push-Location $RootDir
try {
    & docker info *> $null
    if ($LASTEXITCODE -ne 0) {
        throw "Docker is not running. Start Docker Desktop and try again."
    }

    switch ($Command) {
        "up" {
            & docker compose --profile full up --build -d --wait
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
            Write-Warning "This removes all local PROM databases and Service Desk attachments."
            & docker compose down --volumes
            if ($LASTEXITCODE -ne 0) { throw "Docker Compose reset failed." }
            & docker compose --profile full up --build -d --wait
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
            if ($Services.Count -ne 1) { throw "Usage: .\dev.cmd create-module <module-name>" }
            Invoke-PromPython tools/generators/create_module.py $Services[0]
        }
    }

    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code $LASTEXITCODE."
    }
}
finally {
    Pop-Location
}
