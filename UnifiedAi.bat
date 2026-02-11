@echo off
chcp 65001 >nul
title UnifiedAi - Meta-Intelligence Platform
cd /d "%~dp0electron"

echo.
echo    ╔══════════════════════════════════════════════════════════════╗
echo    ║                    UNIFIED AI                               ║
echo    ║              Meta-Intelligence Platform                     ║
echo    ║              Starting Desktop App...                        ║
echo    ╚══════════════════════════════════════════════════════════════╝
echo.

echo [*] Starting UnifiedAi...
echo [*] Detecting Node.js installation...
echo.

REM Auto-detect Node.js from common locations
set NODE_FOUND=0
set NODE_PATH=
set NODE_EXE=
set NPM_EXE=

REM Check A: drive first (if it exists)
if exist "A:\Nodejs\node.exe" (
    set "NODE_PATH=A:\Nodejs"
    set "NODE_EXE=A:\Nodejs\node.exe"
    set "NPM_EXE=A:\Nodejs\npm.cmd"
    set NODE_FOUND=1
    echo [*] Found Node.js at A:\Nodejs\
) else if exist "C:\Program Files\nodejs\node.exe" (
    set "NODE_PATH=C:\Program Files\nodejs"
    set "NODE_EXE=C:\Program Files\nodejs\node.exe"
    set "NPM_EXE=C:\Program Files\nodejs\npm.cmd"
    set NODE_FOUND=1
    echo [*] Found Node.js at C:\Program Files\nodejs\
) else if exist "%LOCALAPPDATA%\Programs\nodejs\node.exe" (
    set "NODE_PATH=%LOCALAPPDATA%\Programs\nodejs"
    set "NODE_EXE=%LOCALAPPDATA%\Programs\nodejs\node.exe"
    set "NPM_EXE=%LOCALAPPDATA%\Programs\nodejs\npm.cmd"
    set NODE_FOUND=1
    echo [*] Found Node.js at %LOCALAPPDATA%\Programs\nodejs\
) else (
    REM Try to find node in PATH
    where node.exe >nul 2>&1
    if %errorlevel% == 0 (
        set "NODE_EXE=node.exe"
        set "NPM_EXE=npm.cmd"
        set NODE_FOUND=1
        echo [*] Found Node.js in system PATH
    )
)

if %NODE_FOUND% == 0 (
    echo [X] Error: Node.js not found!
    echo [*] Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

REM Add Node.js to PATH if we found a specific path
if defined NODE_PATH (
    set "PATH=%NODE_PATH%;%PATH%"
)

if not exist "node_modules" (
    echo [*] Installing dependencies...
    call "%NPM_EXE%" install
    if errorlevel 1 (
        echo [X] Error: npm install failed!
        pause
        exit /b 1
    )
)

echo [*] Launching UnifiedAi...
call "%NPM_EXE%" run start
pause
