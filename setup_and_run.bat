@echo off
setlocal enabledelayedexpansion
title UAV Vision — Setup and Launch

:: Set UTF-8 code page and Python environment variables
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
cd /d "%~dp0"

echo.
echo ============================================================
echo   UAV Vision: Construction Progress Assessment System
echo   Automated Setup ^& Server Launch
echo ============================================================
echo.

:: ── Step 1: Detect Python Interpreter ────────────────────────
echo [Step 1/4] Detecting Python installation...

set "PY_CMD="

py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)" >nul 2>nul
if !ERRORLEVEL! equ 0 (
    set "PY_CMD=py -3"
    goto :python_found
)

py -c "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)" >nul 2>nul
if !ERRORLEVEL! equ 0 (
    set "PY_CMD=py"
    goto :python_found
)

python -c "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)" >nul 2>nul
if !ERRORLEVEL! equ 0 (
    set "PY_CMD=python"
    goto :python_found
)

python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)" >nul 2>nul
if !ERRORLEVEL! equ 0 (
    set "PY_CMD=python3"
    goto :python_found
)

echo.
echo [ERROR] No working Python 3.9+ environment found!
echo Please ensure Python 3.9 or higher is installed and added to PATH.
echo Download Python: https://www.python.org/downloads/
echo.
pause
exit /b 1

:python_found
echo [OK] Using Python command: !PY_CMD!
!PY_CMD! --version
echo.

:: ── Step 2: Install Dependencies & Setup Dirs ─────────────────
echo [Step 2/4] Initializing directories and installing dependencies...
!PY_CMD! install_deps.py
if !ERRORLEVEL! neq 0 (
    echo.
    echo [WARNING] Dependency installation finished with non-zero exit code.
    echo Continuing to validation...
    echo.
)
echo.

:: ── Step 3: Run Validation Suite ──────────────────────────────
echo [Step 3/4] Running module validation tests...
!PY_CMD! validate_all.py
echo.

:: ── Step 4: Launch Server ─────────────────────────────────────
echo [Step 4/4] Starting Flask Web Server...
echo.
echo ============================================================
echo   Web Dashboard URL: http://localhost:5000
echo   Press Ctrl+C in this window to stop the server
echo ============================================================
echo.

:: Optionally launch default browser after 2 seconds in background
start "" "http://localhost:5000"

!PY_CMD! backend\app.py

echo.
echo Server stopped.
pause
