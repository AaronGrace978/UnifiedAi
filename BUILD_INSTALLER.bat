@echo off
chcp 65001 >nul
title UnifiedAi - Build Windows Installer
cd /d "%~dp0"

echo.
echo    ╔══════════════════════════════════════════════════════════════╗
echo    ║              UNIFIEDAI - BUILD INSTALLER                      ║
echo    ║              Windows NSIS installer (exe)                    ║
echo    ╚══════════════════════════════════════════════════════════════╝
echo.

REM Check Node.js
where node >nul 2>&1
if errorlevel 1 (
    echo [X] Node.js not found. Install from https://nodejs.org/
    pause
    exit /b 1
)

echo [*] Building installer from electron folder...
cd electron

if not exist "node_modules" (
    echo [*] Installing dependencies...
    call npm install
    if errorlevel 1 (
        echo [X] npm install failed
        cd ..
        pause
        exit /b 1
    )
)

echo [*] Running electron-builder for Windows (NSIS)...
echo [*] Code signing disabled (avoids symlink privilege issue on Windows)
set CSC_IDENTITY_AUTO_DISCOVERY=false
call npm run build:win
if errorlevel 1 (
    echo [X] Build failed
    cd ..
    pause
    exit /b 1
)

cd ..
echo.
echo [OK] Installer built successfully!
echo.
echo    Output folder:  %~dp0electron\dist
echo    Look for:       UnifiedAi Setup 1.0.0.exe  (or similar)
echo.
echo    Users need Python 3.11+ installed for the backend to run.
echo    See INSTALLER_README.md for details.
echo.
pause
