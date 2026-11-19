@echo off
title UAV Construction Monitor -- Demo Launcher
echo.
echo ============================================================
echo   UAV Construction Monitor -- Demo Launcher
echo ============================================================
echo.
echo [1] Starting Flask backend server on port 5000 ...
start "Flask Server" cmd /k "cd /d %~dp0 && py -m flask --app backend.app run --port 5000"
echo     Server process started.
echo.
echo [2] Waiting 6 seconds for server to initialise ...
timeout /t 6 /nobreak > nul
echo.
echo [3] Seeding demo project with real sample images ...
py create_demo_project.py http://localhost:5000
echo.
echo [4] Opening dashboard in browser ...
start http://localhost:5000
echo.
echo ============================================================
echo   Dashboard is now open at: http://localhost:5000
echo   Navigate to: Projects -- UAV Monitoring -- Site Alpha
echo ============================================================
echo.
pause
