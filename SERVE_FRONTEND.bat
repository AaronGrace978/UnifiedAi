@echo off
chcp 65001 >nul
title UnifiedAi - Frontend Server
cd /d "%~dp0frontend"

echo.
echo    ╔══════════════════════════════════════════════════════════════╗
echo    ║                    UNIFIED AI                               ║
echo    ║              Frontend Server                                ║
echo    ╚══════════════════════════════════════════════════════════════╝
echo.

echo [*] Starting frontend server...
echo [*] Frontend will be available at: http://localhost:10001
echo [*] Press Ctrl+C to stop
echo.

REM Try Python from multiple locations (like AgentPrime does)
set PYTHON_EXE=

REM Try C:\Python314 first (like Cortex uses)
if exist "C:\Python314\python.exe" (
    set PYTHON_EXE=C:\Python314\python.exe
    goto :python_found
)

REM Try common AppData locations
if exist "C:\Users\AGrac\AppData\Local\Programs\Python\Python313\python.exe" (
    set PYTHON_EXE=C:\Users\AGrac\AppData\Local\Programs\Python\Python313\python.exe
    goto :python_found
)

if exist "C:\Users\AGrac\AppData\Local\Programs\Python\Python311\python.exe" (
    set PYTHON_EXE=C:\Users\AGrac\AppData\Local\Programs\Python\Python311\python.exe
    goto :python_found
)

REM Try py launcher
py --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON_EXE=py
    goto :python_found
)

REM Try python command from PATH
python --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON_EXE=python
    goto :python_found
)

echo [X] Error: Python not found!
pause
exit /b 1

:python_found
%PYTHON_EXE% -m http.server 10001
pause
