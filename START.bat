@echo off
chcp 65001 >nul
title UnifiedAi - Meta-Intelligence Platform
cd /d "%~dp0backend"

echo.
echo    ╔══════════════════════════════════════════════════════════════╗
echo    ║                    UNIFIED AI                               ║
echo    ║              Meta-Intelligence Platform                     ║
echo    ║              Starting Backend Server...                      ║
echo    ╚══════════════════════════════════════════════════════════════╝
echo.

echo [*] Starting UnifiedAi backend server...
echo [*] Server will run on http://localhost:10000
echo.

REM Try Python from multiple locations (like AgentPrime does)
set PYTHON_EXE=

REM Try C:\Python314 first (like Cortex uses)
if exist "C:\Python314\python.exe" (
    set PYTHON_EXE=C:\Python314\python.exe
    echo [*] Using Python at C:\Python314\python.exe
    goto :python_found
)

REM Try common AppData locations
if exist "C:\Users\AGrac\AppData\Local\Programs\Python\Python313\python.exe" (
    set PYTHON_EXE=C:\Users\AGrac\AppData\Local\Programs\Python\Python313\python.exe
    echo [*] Using Python at C:\Users\AGrac\AppData\Local\Programs\Python\Python313\python.exe
    goto :python_found
)

if exist "C:\Users\AGrac\AppData\Local\Programs\Python\Python311\python.exe" (
    set PYTHON_EXE=C:\Users\AGrac\AppData\Local\Programs\Python\Python311\python.exe
    echo [*] Using Python at C:\Users\AGrac\AppData\Local\Programs\Python\Python311\python.exe
    goto :python_found
)

REM Try py launcher
py --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON_EXE=py
    echo [*] Using Python via py launcher
    goto :python_found
)

REM Try python command from PATH
python --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON_EXE=python
    echo [*] Using Python from PATH
    goto :python_found
)

echo [X] Error: Python not found!
echo [*] Checked locations:
echo     - C:\Python314\python.exe
echo     - C:\Users\AGrac\AppData\Local\Programs\Python\Python313\python.exe
echo     - C:\Users\AGrac\AppData\Local\Programs\Python\Python311\python.exe
echo     - py launcher
echo     - PATH environment variable
pause
exit /b 1

:python_found
echo [*] Installing/updating dependencies...
%PYTHON_EXE% -m pip install --upgrade pip --quiet
%PYTHON_EXE% -m pip install -r requirements.txt
if errorlevel 1 (
    echo [X] Error: Failed to install dependencies!
    echo [*] Trying to install pydantic-settings separately...
    %PYTHON_EXE% -m pip install pydantic-settings
    if errorlevel 1 (
        echo [X] Error: Could not install pydantic-settings!
        pause
        exit /b 1
    )
)

REM Ensure pydantic-settings is installed (required by config.py)
%PYTHON_EXE% -m pip install pydantic-settings --quiet
if errorlevel 1 (
    echo [WARNING] pydantic-settings installation had issues, but continuing...
)

echo [OK] Dependencies ready!
echo.
echo [*] Starting backend server...
echo [*] Press Ctrl+C to stop
echo.

%PYTHON_EXE% run.py
pause
