param(
    [switch]$SkipInstall,
    [switch]$NoDocker,
    [switch]$ExitAfterReady,
    [int]$BackendPort = 8000,
    [int]$ServiceDeskPort = 8001,
    [int]$FrontendPort = 5173
)

$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Net.Http

$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = Join-Path $RootDir "backend"
$ServiceDeskDir = Join-Path $RootDir "service-desk-backend"
$FrontendDir = Join-Path $RootDir "frontend"
$ComposeProject = "shpiu_project_showcase"

$BackendProcess = $null
$ServiceDeskProcess = $null
$FrontendProcess = $null

function Write-Step {
    param([string]$Message)
    Write-Host "[dev] $Message" -ForegroundColor Cyan
}

function Require-Command {
    param(
        [string]$Name,
        [string]$InstallHint
    )

    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "$Name is not installed or not in PATH. $InstallHint"
    }
}

function Copy-EnvIfMissing {
    param([string]$Directory)

    $envFile = Join-Path $Directory ".env"
    $exampleFile = Join-Path $Directory ".env.example"

    if (-not (Test-Path -LiteralPath $envFile)) {
        Copy-Item -LiteralPath $exampleFile -Destination $envFile
        Write-Step "Created $envFile"
    }
}

function Get-EnvFileValue {
    param(
        [string]$Path,
        [string]$Name
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        return $null
    }

    $match = Select-String -LiteralPath $Path -Pattern "^$([regex]::Escape($Name))=(.*)$" | Select-Object -First 1
    if (-not $match) {
        return $null
    }

    return $match.Matches[0].Groups[1].Value
}

function Find-Npm {
    $npmCmd = Get-Command npm.cmd -ErrorAction SilentlyContinue
    if ($npmCmd) {
        return $npmCmd.Source
    }

    $npm = Get-Command npm -ErrorAction SilentlyContinue
    if ($npm) {
        return $npm.Source
    }

    throw "npm is not installed or not in PATH. Install Node.js LTS/current first."
}

function Find-Node {
    $node = Get-Command node.exe -ErrorAction SilentlyContinue
    if ($node) {
        return $node.Source
    }

    $node = Get-Command node -ErrorAction SilentlyContinue
    if ($node) {
        return $node.Source
    }

    throw "node is not installed or not in PATH. Install Node.js LTS/current first."
}

function Get-WindowsBackendVenvDir {
    $baseDir = $env:LOCALAPPDATA
    if (-not $baseDir) {
        $baseDir = $env:TEMP
    }
    if (-not $baseDir) {
        $baseDir = Join-Path $RootDir ".cache"
    }

    return Join-Path $baseDir "shpiu_project_showcase\backend-venv-py314"
}

function Test-Python314 {
    param([string]$PythonExe)

    try {
        & $PythonExe -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 14) else 1)" *> $null
        return $LASTEXITCODE -eq 0
    }
    catch {
        return $false
    }
}

function Ensure-Python314 {
    param([string]$PythonExe)

    if (-not (Test-Python314 $PythonExe)) {
        throw "$PythonExe exists, but it is not Python 3.14+. Remove the venv and rerun .\dev.cmd."
    }
}

function Test-BackendDependencies {
    param([string]$PythonExe)

    $code = @"
import importlib.util

required = ('alembic', 'fastapi', 'psycopg', 'pydantic', 'sqlalchemy', 'uvicorn')
has_required = all(importlib.util.find_spec(module) for module in required)
has_multipart = any(importlib.util.find_spec(module) for module in ('python_multipart', 'multipart'))
raise SystemExit(0 if has_required and has_multipart else 1)
"@

    try {
        & $PythonExe -c $code
        return $LASTEXITCODE -eq 0
    }
    catch {
        return $false
    }
}

function Test-ServiceDeskDependencies {
    param([string]$PythonExe)

    $code = @"
import importlib.util

required = ('alembic', 'fastapi', 'psycopg', 'pydantic', 'sqlalchemy', 'uvicorn')
raise SystemExit(0 if all(importlib.util.find_spec(module) for module in required) else 1)
"@

    try {
        & $PythonExe -c $code
        return $LASTEXITCODE -eq 0
    }
    catch {
        return $false
    }
}

function Find-Python314Exe {
    $candidates = @()
    foreach ($name in @("python", "python3.14", "python3")) {
        $command = Get-Command $name -ErrorAction SilentlyContinue
        if ($command) {
            $candidates += $command.Source
        }
    }

    if ($env:LOCALAPPDATA) {
        $candidates += Join-Path $env:LOCALAPPDATA "Programs\Python\Python314\python.exe"
    }
    $candidates += "C:\Program Files\Python314\python.exe"

    foreach ($candidate in $candidates | Select-Object -Unique) {
        if ((Test-Path -LiteralPath $candidate) -and (Test-Python314 $candidate)) {
            return $candidate
        }
    }

    throw "Python 3.14 is required. Install Python 3.14 or make it available in PATH."
}

function New-BackendVenv {
    param([string]$VenvDir)

    $parentDir = Split-Path -Parent $VenvDir
    New-Item -ItemType Directory -Force -Path $parentDir | Out-Null

    $created = $false
    if (Get-Command py -ErrorAction SilentlyContinue) {
        try {
            & py -3.14 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 14) else 1)" *> $null
            if ($LASTEXITCODE -eq 0) {
                & py -3.14 -m venv $VenvDir
                $created = $LASTEXITCODE -eq 0
            }
        }
        catch {
            $created = $false
        }
    }

    if (-not $created) {
        $pythonExe = Find-Python314Exe
        & $pythonExe -m venv $VenvDir
        $created = $LASTEXITCODE -eq 0
    }

    if (-not $created) {
        throw "Could not create backend virtualenv."
    }
}

function Ensure-BackendVenv {
    $defaultVenv = Join-Path $BackendDir ".venv"
    $py314Venv = Get-WindowsBackendVenvDir
    $venvDir = $defaultVenv
    $venvPython = Join-Path $venvDir "Scripts\python.exe"

    if (Test-Path -LiteralPath $venvPython) {
        if (Test-Python314 $venvPython) {
            return $venvPython
        }

        Write-Step "Existing $defaultVenv is not Python 3.14+, using $py314Venv"
        $venvDir = $py314Venv
        $venvPython = Join-Path $venvDir "Scripts\python.exe"
    }

    if (Test-Path -LiteralPath $venvPython) {
        Ensure-Python314 $venvPython
        return $venvPython
    }

    Write-Step "Creating backend virtualenv at $venvDir"
    New-BackendVenv $venvDir

    if (-not (Test-Path -LiteralPath $venvPython)) {
        throw "Could not create backend virtualenv. Install Python 3.14 and try again."
    }

    Ensure-Python314 $venvPython
    return $venvPython
}

function Ensure-BackendDependencies {
    param([string]$PythonExe)

    if ($SkipInstall) {
        return
    }

    if (Test-BackendDependencies $PythonExe) {
        Write-Step "Backend dependencies already installed"
        return
    }

    Write-Step "Installing backend dependencies"
    Push-Location $BackendDir
    try {
        & $PythonExe -m pip install --upgrade pip
        & $PythonExe -m pip install -e ".[dev]"
    }
    finally {
        Pop-Location
    }
}

function Ensure-ServiceDeskDependencies {
    param([string]$PythonExe)

    if ($SkipInstall) {
        return
    }

    if (Test-ServiceDeskDependencies $PythonExe) {
        Write-Step "Service Desk backend dependencies already installed"
        return
    }

    Write-Step "Installing Service Desk backend dependencies"
    Push-Location $ServiceDeskDir
    try {
        & $PythonExe -m pip install -e ".[dev]"
    }
    finally {
        Pop-Location
    }
}

function Ensure-FrontendDependencies {
    param([string]$NpmExe)

    if ($SkipInstall) {
        return
    }

    $nodeModules = Join-Path $FrontendDir "node_modules"
    if (Test-Path -LiteralPath $nodeModules) {
        Write-Step "Frontend dependencies already installed"
        return
    }

    Write-Step "Installing frontend dependencies"
    Push-Location $FrontendDir
    try {
        & $NpmExe install
    }
    finally {
        Pop-Location
    }
}

function Wait-Database {
    if ($NoDocker) {
        return
    }

    Write-Step "Waiting for PostgreSQL"
    for ($i = 0; $i -lt 60; $i++) {
        & docker compose -p $ComposeProject exec -T db pg_isready -U project_showcase -d project_showcase *> $null
        if ($LASTEXITCODE -eq 0) {
            return
        }
        Start-Sleep -Seconds 1
    }

    throw "PostgreSQL did not become ready in time. Check Docker Desktop and run: docker compose -p $ComposeProject logs db"
}

function Wait-ServiceDeskDatabase {
    if ($NoDocker) {
        return
    }

    Write-Step "Waiting for Service Desk PostgreSQL"
    for ($i = 0; $i -lt 60; $i++) {
        & docker compose -p $ComposeProject exec -T service_desk_db pg_isready -U service_desk -d service_desk *> $null
        if ($LASTEXITCODE -eq 0) {
            return
        }
        Start-Sleep -Seconds 1
    }

    throw "Service Desk PostgreSQL did not become ready in time. Check Docker Desktop and run: docker compose -p $ComposeProject logs service_desk_db"
}

function Start-AppProcess {
    param(
        [string]$FilePath,
        [string]$Arguments,
        [string]$WorkingDirectory,
        [string]$Name
    )

    $process = [System.Diagnostics.Process]::new()
    $process.StartInfo.FileName = $FilePath
    $process.StartInfo.Arguments = $Arguments
    $process.StartInfo.WorkingDirectory = $WorkingDirectory
    $process.StartInfo.UseShellExecute = $false
    $process.StartInfo.CreateNoWindow = $false

    if (-not $process.Start()) {
        throw "Could not start $Name"
    }

    return $process
}

function Wait-Url {
    param(
        [string]$Url,
        [string]$Name,
        [System.Diagnostics.Process]$Process
    )

    Write-Step "Waiting for $Name at $Url"
    for ($i = 0; $i -lt 90; $i++) {
        if ($Process.HasExited) {
            throw "$Name exited before becoming ready"
        }

        $client = $null
        $response = $null
        try {
            $client = [System.Net.Http.HttpClient]::new()
            $client.Timeout = [TimeSpan]::FromSeconds(2)
            $response = $client.GetAsync($Url).GetAwaiter().GetResult()
            $statusCode = [int]$response.StatusCode
            if ($statusCode -ge 200 -and $statusCode -lt 500) {
                return
            }
        }
        catch {
            Start-Sleep -Seconds 1
        }
        finally {
            if ($response) {
                $response.Dispose()
            }
            if ($client) {
                $client.Dispose()
            }
        }
    }

    throw "$Name did not become ready in time"
}

function Test-LocalPortOpen {
    param([int]$Port)

    $client = New-Object System.Net.Sockets.TcpClient
    try {
        $asyncResult = $client.BeginConnect("127.0.0.1", $Port, $null, $null)
        if (-not $asyncResult.AsyncWaitHandle.WaitOne(300, $false)) {
            return $false
        }
        $client.EndConnect($asyncResult)
        return $true
    }
    catch {
        return $false
    }
    finally {
        $client.Close()
    }
}

function Assert-PortFree {
    param(
        [int]$Port,
        [string]$Name
    )

    if (Test-LocalPortOpen $Port) {
        throw "$Name port $Port is already in use. Stop the old process or run .\dev.cmd with another port."
    }
}

function Stop-ChildProcess {
    param(
        [System.Diagnostics.Process]$Process,
        [string]$Name
    )

    if ($Process -and -not $Process.HasExited) {
        Write-Step "Stopping $Name"
        try {
            $Process.Kill()
        }
        catch {
            Stop-Process -Id $Process.Id -Force -ErrorAction SilentlyContinue
        }
    }
}

try {
    if (-not $NoDocker) {
        Require-Command "docker" "Install Docker Desktop and start it."
    }
    $NpmExe = Find-Npm
    $NodeExe = Find-Node

    Copy-EnvIfMissing $BackendDir
    Copy-EnvIfMissing $ServiceDeskDir
    Copy-EnvIfMissing $FrontendDir

    $BackendPython = Ensure-BackendVenv
    Ensure-BackendDependencies $BackendPython
    Ensure-ServiceDeskDependencies $BackendPython
    Ensure-FrontendDependencies $NpmExe

    if (-not $NoDocker) {
        Write-Step "Starting PostgreSQL"
        Push-Location $RootDir
        try {
            & docker compose -p $ComposeProject up -d db service_desk_db
        }
        finally {
            Pop-Location
        }
        Wait-Database
        Wait-ServiceDeskDatabase
    }

    Write-Step "Applying migrations"
    Push-Location $BackendDir
    try {
        & $BackendPython -m alembic upgrade head
        & $BackendPython scripts\seed.py
    }
    finally {
        Pop-Location
    }

    Write-Step "Applying Service Desk migrations"
    Push-Location $ServiceDeskDir
    try {
        & $BackendPython -m alembic upgrade head

        Write-Step "Seeding Service Desk demo data"
        $previousIdentityDatabaseUrl = $env:SERVICE_DESK_IDENTITY_DATABASE_URL
        $identityDatabaseUrl = Get-EnvFileValue (Join-Path $BackendDir ".env") "DATABASE_URL"
        if ($identityDatabaseUrl) {
            $env:SERVICE_DESK_IDENTITY_DATABASE_URL = $identityDatabaseUrl
        }
        try {
            & $BackendPython scripts\seed.py
        }
        finally {
            if ($null -eq $previousIdentityDatabaseUrl) {
                Remove-Item Env:\SERVICE_DESK_IDENTITY_DATABASE_URL -ErrorAction SilentlyContinue
            }
            else {
                $env:SERVICE_DESK_IDENTITY_DATABASE_URL = $previousIdentityDatabaseUrl
            }
        }
    }
    finally {
        Pop-Location
    }

    Assert-PortFree $BackendPort "Backend"
    Assert-PortFree $ServiceDeskPort "Service Desk backend"
    Assert-PortFree $FrontendPort "Frontend"

    Write-Step "Starting backend"
    $backendArgs = "-m uvicorn app.main:app --host 127.0.0.1 --port $BackendPort"
    $BackendProcess = Start-AppProcess $BackendPython $backendArgs $BackendDir "backend"

    Wait-Url "http://127.0.0.1:$BackendPort/api/health" "backend" $BackendProcess

    Write-Step "Starting Service Desk backend"
    $serviceDeskArgs = "-m uvicorn app.main:app --host 127.0.0.1 --port $ServiceDeskPort"
    $ServiceDeskProcess = Start-AppProcess $BackendPython $serviceDeskArgs $ServiceDeskDir "Service Desk backend"

    Wait-Url "http://127.0.0.1:$ServiceDeskPort/health/live" "Service Desk backend" $ServiceDeskProcess

    Write-Step "Starting frontend"
    $env:VITE_SERVICE_DESK_API_BASE_URL = "http://localhost:$ServiceDeskPort"
    $viteBin = Join-Path $FrontendDir "node_modules\vite\bin\vite.js"
    if (-not (Test-Path -LiteralPath $viteBin)) {
        throw "Vite is not installed. Run .\dev.cmd without -SkipInstall first."
    }
    $frontendArgs = "`"$viteBin`" --host 127.0.0.1 --port $FrontendPort --strictPort"
    $FrontendProcess = Start-AppProcess $NodeExe $frontendArgs $FrontendDir "frontend"

    Wait-Url "http://127.0.0.1:$FrontendPort" "frontend" $FrontendProcess

    Write-Host ""
    Write-Host "Application is running:" -ForegroundColor Green
    Write-Host "  UI:                   http://localhost:$FrontendPort"
    Write-Host "  Projects Swagger:     http://localhost:$BackendPort/docs"
    Write-Host "  Service Desk Swagger: http://localhost:$ServiceDeskPort/docs"
    Write-Host ""
    Write-Host "Demo users:"
    Write-Host "  admin@utmn.ru"
    Write-Host "  manager@utmn.ru"
    Write-Host "  employee@utmn.ru"
    Write-Host "  code: 000000"
    Write-Host ""
    Write-Host "Press Ctrl+C to stop backend and frontend." -ForegroundColor Yellow

    if ($ExitAfterReady) {
        Write-Step "ExitAfterReady is set; stopping after successful smoke check"
        return
    }

    while ($true) {
        if ($BackendProcess.HasExited) {
            throw "Backend process stopped"
        }
        if ($FrontendProcess.HasExited) {
            throw "Frontend process stopped"
        }
        if ($ServiceDeskProcess.HasExited) {
            throw "Service Desk backend process stopped"
        }
        Start-Sleep -Seconds 2
    }
}
finally {
    Stop-ChildProcess $FrontendProcess "frontend"
    Stop-ChildProcess $ServiceDeskProcess "Service Desk backend"
    Stop-ChildProcess $BackendProcess "backend"
}
