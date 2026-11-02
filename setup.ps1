# Setup script for Global Compliance Intelligence (ComplyIQ) on Windows
# Uses `uv` (or fallback to python venv/pip) and `npm`

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $ScriptDir

Write-Host "==========================================================" -ForegroundColor Green
Write-Host "  Setting up Global Compliance Intelligence (Windows)     " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green

# 1. Check Node and npm
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Error "Node.js is required but not installed. Install it via 'winget install OpenJS.NodeJS.LTS' or https://nodejs.org"
    exit 1
}
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    Write-Error "npm is required but not installed."
    exit 1
}
$nodeVer = node -v
$npmVer = npm -v
Write-Host "[✓] Node:   $nodeVer" -ForegroundColor Cyan
Write-Host "[✓] npm:    $npmVer" -ForegroundColor Cyan

# 2. Check or install uv
$useUv = $false
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "uv not found in PATH. Checking if we can install uv..." -ForegroundColor Yellow
    try {
        powershell -ExecutionPolicy ByPass -Command "irm https://astral.sh/uv/install.ps1 | iex"
        $localAppData = [Environment]::GetFolderPath("LocalApplicationData")
        $uvPath = Join-Path $localAppData "Programs\uv"
        $cargoBin = Join-Path $env:USERPROFILE ".cargo\bin"
        if (Test-Path $uvPath) { $env:PATH = "$uvPath;$env:PATH" }
        if (Test-Path $cargoBin) { $env:PATH = "$cargoBin;$env:PATH" }
    } catch {
        Write-Host "Notice: uv automatic install skipped or not available." -ForegroundColor DarkGray
    }
}

if (Get-Command uv -ErrorAction SilentlyContinue) {
    $uvVer = uv --version
    Write-Host "[✓] uv:     $uvVer" -ForegroundColor Cyan
    $useUv = $true
} else {
    Write-Host "uv not found; falling back to Python venv/pip." -ForegroundColor Yellow
    if (-not (Get-Command python -ErrorAction SilentlyContinue) -and -not (Get-Command py -ErrorAction SilentlyContinue)) {
        Write-Error "Python 3.11+ is required but not found. Install from python.org or 'winget install Python.Python.3.12'"
        exit 1
    }
    $pyVer = python --version 2>$null
    Write-Host "[✓] Python: $pyVer" -ForegroundColor Cyan
}

# 3. Setup .env file
if (-not (Test-Path ".env")) {
    Write-Host "Creating .env from .env.example..." -ForegroundColor Cyan
    Copy-Item ".env.example" ".env"
}

# 4. Setup Python virtual environment & dependencies
$venvPath = Join-Path $ScriptDir "backend\.venv"
$venvPython = Join-Path $venvPath "Scripts\python.exe"

if ($useUv) {
    if (-not (Test-Path $venvPath)) {
        Write-Host "Creating virtual environment with uv at $venvPath..." -ForegroundColor Cyan
        uv venv $venvPath
    }
    Write-Host "Installing backend dependencies with uv..." -ForegroundColor Cyan
    $env:VIRTUAL_ENV = $venvPath
    uv pip install -r "backend\requirements.txt"
} else {
    if (-not (Test-Path $venvPath)) {
        Write-Host "Creating virtual environment at $venvPath..." -ForegroundColor Cyan
        python -m venv $venvPath
    }
    Write-Host "Installing backend dependencies with pip..." -ForegroundColor Cyan
    & $venvPython -m pip install --upgrade pip
    & $venvPython -m pip install -r "backend\requirements.txt"
}

# 5. Run database migrations
Write-Host "Running database migrations with Alembic..." -ForegroundColor Cyan
Push-Location "backend"
$env:PYTHONPATH = "."
& ".\.venv\Scripts\alembic.exe" upgrade head
Pop-Location

# 6. Install frontend dependencies using npm
Write-Host "Installing frontend dependencies using npm..." -ForegroundColor Cyan
Push-Location "frontend"
npm install
Pop-Location

# 7. Ensure data directories exist and sync vectors
$dirs = @(
    "data\uploads",
    "data\qdrant",
    "data\company\g-inc\uploads",
    "data\legal\india\dpdp",
    "data\legal\india\it_act"
)
foreach ($d in $dirs) {
    if (-not (Test-Path $d)) {
        New-Item -ItemType Directory -Force -Path $d | Out-Null
    }
}

Write-Host "Syncing vectors into local Qdrant..." -ForegroundColor Cyan
& $venvPython "scripts\sync_vectors.py"

Write-Host "==========================================================" -ForegroundColor Green
Write-Host "  Windows setup completed successfully!                   " -ForegroundColor Green
Write-Host "  Run .\start.ps1 to launch Backend and Frontend.         " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
