# Launcher for Global Compliance Intelligence (ComplyIQ) on Windows
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $ScriptDir

# Check if environment is initialized
if (-not (Test-Path "backend\.venv") -or -not (Test-Path "frontend\node_modules")) {
    Write-Host "Environment not initialized. Running .\setup.ps1 first..." -ForegroundColor Yellow
    & ".\setup.ps1"
}

$venvPython = Join-Path $ScriptDir "backend\.venv\Scripts\python.exe"

Write-Host "==========================================================" -ForegroundColor Green
Write-Host "  Starting ComplyIQ Platform (Windows)                    " -ForegroundColor Green
Write-Host "  Backend API:  http://localhost:8000                     " -ForegroundColor Cyan
Write-Host "  API Docs:     http://localhost:8000/docs                " -ForegroundColor Cyan
Write-Host "  Health Check: http://localhost:8000/health              " -ForegroundColor Cyan
Write-Host "  Frontend UI:  http://localhost:5173                     " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop all services.`n" -ForegroundColor Yellow

$backendProcess = $null

try {
    Write-Host "Starting FastAPI backend on port 8000..." -ForegroundColor Cyan
    $env:PYTHONPATH = "."
    $backendProcess = Start-Process -FilePath $venvPython `
        -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload" `
        -WorkingDirectory (Join-Path $ScriptDir "backend") `
        -PassThru

    Start-Sleep -Seconds 2

    Write-Host "Starting Vite frontend on port 5173..." -ForegroundColor Cyan
    Set-Location (Join-Path $ScriptDir "frontend")
    npm run dev -- --host
}
finally {
    Write-Host "`nShutting down ComplyIQ services..." -ForegroundColor Yellow
    if ($backendProcess -and -not $backendProcess.HasExited) {
        Stop-Process -Id $backendProcess.Id -Force -ErrorAction SilentlyContinue
    }
    Set-Location $ScriptDir
}
