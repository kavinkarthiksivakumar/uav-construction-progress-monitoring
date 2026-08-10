@echo off
title UAV Vision — Construction Progress Assessment (All Modules)
cd /d "%~dp0"
echo.
echo ============================================================
echo  IEEE M.Tech Project
echo  Explainable Vision-Based Construction Progress Assessment
echo ============================================================
echo.
echo  Module 1  : UAV Image Acquisition ^& Quality Assessment
echo  Module 2  : Image Processing (LEVIR-CD + Roboflow)
echo  Module 3  : Construction Activity Detection
echo  Module 4  : Construction Change Detection
echo  Module 5  : Delay Prediction ^& Progress Assessment
echo.
echo  Open browser at: http://localhost:5000
echo.
echo  Dataset paths : Configure LEVIR_CD_PATH and ROBOFLOW_PATH in .env
echo.
echo ============================================================
echo.
python backend\app.py
pause
