# UAV Vision — Construction Progress Assessment PowerShell Launcher
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  UAV Vision: Construction Progress Assessment System" -ForegroundColor Cyan
Write-Host "  PowerShell Quick Launcher" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Find Python executable
$PythonCmd = $null
if (Get-Command py -ErrorAction SilentlyContinue) {
    $PythonCmd = "py"
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $PythonCmd = "python"
} elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
    $PythonCmd = "python3"
}

if (-not $PythonCmd) {
    Write-Host "[ERROR] Python 3.9+ was not found on your system PATH." -ForegroundColor Red
    Write-Host "Please install Python from https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

Write-Host "[OK] Using Python command: $PythonCmd" -ForegroundColor Green

# Ensure .env file
if (-not (Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "[INFO] Created .env configuration file." -ForegroundColor Yellow
    }
}

# Menu
Write-Host ""
Write-Host "Please select an option:" -ForegroundColor White
Write-Host "  [1] Start Web Dashboard Server (Default)" -ForegroundColor White
Write-Host "  [2] Run Setup & Dependency Installer" -ForegroundColor White
Write-Host "  [3] Run Full Validation Suite" -ForegroundColor White
Write-Host "  [4] Exit" -ForegroundColor White
Write-Host ""

$choice = Read-Host "Enter option (1-4) [default: 1]"
if ([string]::IsNullOrWhiteSpace($choice)) { $choice = "1" }

switch ($choice) {
    "1" {
        Write-Host ""
        Write-Host "Starting Flask Server at http://localhost:5000 ..." -ForegroundColor Green
        Start-Process "http://localhost:5000"
        & $PythonCmd backend/app.py
    }
    "2" {
        Write-Host ""
        Write-Host "Running Installer & Directory Setup..." -ForegroundColor Cyan
        & $PythonCmd install_deps.py
    }
    "3" {
        Write-Host ""
        Write-Host "Executing Validation Suite..." -ForegroundColor Cyan
        & $PythonCmd validate_all.py
    }
    "4" {
        Write-Host "Exiting."
        exit 0
    }
    Default {
        Write-Host "Invalid option. Starting server by default..." -ForegroundColor Green
        Start-Process "http://localhost:5000"
        & $PythonCmd backend/app.py
    }
}
