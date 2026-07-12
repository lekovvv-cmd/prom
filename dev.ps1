[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [ValidateSet("up", "down", "restart", "logs", "status", "reset", "test")]
    [string]$Command = "up",

    [Parameter(Position = 1, ValueFromRemainingArguments = $true)]
    [string[]]$Services = @()
)

$ErrorActionPreference = "Stop"
$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Path

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
            & docker compose up --build -d
            if ($LASTEXITCODE -ne 0) { throw "Docker Compose startup failed." }
            & docker compose ps
            Write-Host ""
            Write-Host "PROM:                 http://localhost:5173/" -ForegroundColor Green
            Write-Host "Projects:             http://localhost:5173/projects"
            Write-Host "Service Desk:         http://localhost:5173/service-desk"
            Write-Host "Projects Swagger:     http://localhost:8000/docs"
            Write-Host "Service Desk Swagger: http://localhost:8001/docs"
        }
        "down" { & docker compose down }
        "restart" { & docker compose restart @Services }
        "logs" { & docker compose logs --follow --tail 200 @Services }
        "status" { & docker compose ps }
        "reset" {
            Write-Warning "This removes all local PROM databases and Service Desk attachments."
            & docker compose down --volumes
            if ($LASTEXITCODE -ne 0) { throw "Docker Compose reset failed." }
            & docker compose up --build -d
        }
        "test" {
            & docker compose --profile test run --rm projects-tests
            if ($LASTEXITCODE -ne 0) { throw "Projects tests failed." }
            & docker compose --profile test run --rm service-desk-tests
            if ($LASTEXITCODE -ne 0) { throw "Service Desk tests failed." }
            & docker compose --profile test run --rm frontend-tests
            if ($LASTEXITCODE -ne 0) { throw "Frontend tests failed." }
        }
    }

    if ($LASTEXITCODE -ne 0) {
        throw "Docker Compose command failed with exit code $LASTEXITCODE."
    }
}
finally {
    Pop-Location
}
