@echo off
title IEEE M.Tech Project — Full Setup
color 0A
cd /d "%~dp0"

echo.
echo ============================================================
echo    UAV Construction Progress Assessment
echo    One-Click Setup + Launch
echo ============================================================
echo.

:: ── 1. Python check ────────────────────────────────────────────
echo [Step 1/5]  Checking Python...
python --version
if errorlevel 1 (
    echo.
    echo  ERROR: Python not found in PATH.
    echo  Download Python 3.9+ from: https://www.python.org/downloads/
    echo.
    pause
    exit /b 
)
echo  Python OK.
echo.

:: ── 2. Install packages ────────────────────────────────────────
echo [Step 2/5]  Installing required packages...
echo  (This may take 2-5 minutes on first run)
echo.
python -m pip install flask flask-cors pillow opencv-python-headless numpy scipy exifread python-dotenv requests
echo.
echo  Packages installed.
echo.

:: ── 3. Create directories ──────────────────────────────────────
echo [Step 3/5]  Creating project directories...
python -c "
from pathlib import Path
dirs=['uploads/raw','processed/module1','metadata','logs','reports','models','datasets/roboflow','datasets/levir','datasets/sysu']
[Path(d).mkdir(parents=True, exist_ok=True) or print(f'  OK  {d}') for d in dirs]
print('Directories ready.')
"
echo.

:: ── 4. Run tests ───────────────────────────────────────────────
echo [Step 4/5]  Running all Module validation tests...
echo.
python validate_all.py
echo.

:: ── 5. Launch server ───────────────────────────────────────────
echo [Step 5/5]  Launching Flask server...
echo.
echo  ┌─────────────────────────────────────────────────────┐
echo  │   Open your browser at: http://localhost:5000       │
echo  │   Press Ctrl+C to stop the server                   │
echo  └─────────────────────────────────────────────────────┘
echo.
python backend\app.py
pause
