@echo off
title UAV Vision — Construction AI Suite Tests
cd /d "%~dp0"
echo ============================================================
echo  Running IEEE M.Tech Project Automated Tests
echo ============================================================
echo.

echo [1/5] Running Module 1 Tests (UAV Acquisition ^& Quality)...
echo ------------------------------------------------------------
python tests\test_module1.py
if %ERRORLEVEL% NEQ 0 (echo. && echo [WARNING] Module 1 Tests Failed. && echo.)

echo [2/5] Running Module 2 Tests (Advanced Processing)...
echo ------------------------------------------------------------
python tests\test_module2.py
if %ERRORLEVEL% NEQ 0 (echo. && echo [WARNING] Module 2 Tests Failed. && echo.)

echo [3/5] Running Module 3 Tests (Activity Detection)...
echo ------------------------------------------------------------
python tests\test_module3.py
if %ERRORLEVEL% NEQ 0 (echo. && echo [WARNING] Module 3 Tests Failed. && echo.)

echo [4/5] Running Module 4 Tests (Change Detection)...
echo ------------------------------------------------------------
python tests\test_module4.py
if %ERRORLEVEL% NEQ 0 (echo. && echo [WARNING] Module 4 Tests Failed. && echo.)

echo [5/5] Running Module 5 Tests (Delay Prediction ^& Progress)...
echo ------------------------------------------------------------
python tests\test_module5.py
if %ERRORLEVEL% NEQ 0 (echo. && echo [WARNING] Module 5 Tests Failed. && echo.)

echo ============================================================
echo  All Module tests execution completed.
echo  Reports saved in reports/ directory.
echo ============================================================
echo.
pause
