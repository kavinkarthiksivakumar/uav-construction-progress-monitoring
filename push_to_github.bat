@echo off
cd /d "%~dp0"
echo ====================================================================
echo   Pushing Essential Code to GitHub: kavinkarthiksivakumar
echo ====================================================================
echo.
git remote -v
echo.
echo Pushing commit to origin main...
git push -u origin main
echo.
if %ERRORLEVEL% EQU 0 (
    echo ====================================================================
    echo   SUCCESS: All essential codes have been pushed to GitHub!
    echo   Repository: https://github.com/kavinkarthiksivakumar/uav-construction-progress-monitoring
    echo ====================================================================
) else (
    echo ====================================================================
    echo   Push paused: GitHub authentication required.
    echo.
    echo   If prompted by Git Credential Manager in your browser, please
    echo   authorize your account.
    echo.
    echo   Alternatively, if you have a GitHub Personal Access Token (PAT):
    echo   Run: git push https://YOUR_TOKEN@github.com/kavinkarthiksivakumar/uav-construction-progress-monitoring.git main
    echo ====================================================================
)
pause
