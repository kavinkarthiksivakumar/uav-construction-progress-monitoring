@echo off
setlocal enabledelayedexpansion
title UAV Vision — Test Suite Runner

:: Set UTF-8 code page and Python environment variables
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
cd /d "%~dp0"

echo.
echo ============================================================
echo   UAV Vision: Master Test Suite Runner
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

echo [ERROR] No working Python 3.9+ found!
pause
exit /b 1

:python_found
echo Running Master Validation Tests using: !PY_CMD!
echo.
!PY_CMD! validate_all.py

echo.
echo ============================================================
echo   Validation run completed.
echo   Reports are saved in: reports/
echo ============================================================
echo.
pause
