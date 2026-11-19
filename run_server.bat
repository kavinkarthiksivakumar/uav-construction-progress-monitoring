@echo off
setlocal enabledelayedexpansion
title UAV Vision — Server Launcher

:: Set UTF-8 code page and Python environment variables
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
cd /d "%~dp0"

echo.
echo ============================================================
echo   UAV Vision: Construction Progress Assessment System
echo ============================================================
echo.

:: Detect Python
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

echo [ERROR] No working Python 3.9+ found! Please install Python.
pause
exit /b 1

:python_found
:: Ensure .env exists if missing
if not exist ".env" (
    if exist ".env.example" (
        copy /Y ".env.example" ".env" >nul
        echo [INFO] Created .env configuration from .env.example
    )
)

echo  Python: !PY_CMD!
echo.
echo  ============================================================
echo   Starting Server...
echo   Local Dashboard : http://localhost:5000
echo   Health API      : http://localhost:5000/api/v1/health
echo   Press Ctrl+C to shutdown server
echo  ============================================================
echo.

!PY_CMD! backend\app.py

echo.
echo Server has stopped.
pause
