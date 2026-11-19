@echo off
setlocal
cd /d "%~dp0"
echo ====================================================================
echo   Create and Push to a New Repository on GitHub
echo ====================================================================
echo.
set /p REPO_NAME="Enter new repository name (e.g. uav-progress-assessment-execution): "
if "%REPO_NAME%"=="" set REPO_NAME=uav-progress-assessment-execution

echo.
echo Target URL: https://github.com/kavinkarthiksivakumar/%REPO_NAME%.git
echo.
echo NOTE: Make sure you created the empty repo '%REPO_NAME%' on https://github.com/new first!
echo.
pause

git remote add execution-repo https://github.com/kavinkarthiksivakumar/%REPO_NAME%.git 2>nul
git remote set-url execution-repo https://github.com/kavinkarthiksivakumar/%REPO_NAME%.git

echo Pushing main branch to %REPO_NAME%...
git push -u execution-repo main

echo.
echo Done!
pause
