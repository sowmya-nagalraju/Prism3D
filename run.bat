@echo off
title Prism3D - Image to 3D Smooth Printable Model Studio
echo ========================================================
echo    Prism3D: Image to 3D Studio Launcher
echo    Drawings, Photos, Blueprints, Anime & Cartoons to 3D
echo ========================================================
echo.

cd /d "%~dp0"

echo [1/3] Verifying Python environment...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH!
    echo Please install Python 3.10+ and re-run.
    pause
    exit /b 1
)

echo [2/3] Terminating any previous instance on port 8000...
powershell -NoProfile -Command "Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }" >nul 2>&1

echo [3/3] Starting Prism3D Web Studio on http://127.0.0.1:8000 ...
start "" http://127.0.0.1:8000
python app.py

pause
