@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul
set PYTHONUTF8=1
title Manager OS
if not exist ".venv\Scripts\python.exe" (
    echo First-time setup is required. Starting SETUP.bat...
    call SETUP.bat
    if errorlevel 1 exit /b 1
)
".venv\Scripts\python.exe" setup\launch.py
if errorlevel 1 (
    echo Manager OS could not start. See the error above, or run SETUP.bat to repair packages.
    pause
)
exit /b

rem Archived 2026-10-12, retained for rollback:
rem @echo off
rem chcp 65001 > nul
rem set PYTHONUTF8=1
rem title MANAGER OS — Startup
rem 
rem echo.
rem echo  Starting Manager OS...
rem echo.
rem 
rem :: Activate venv if exists
rem if exist ".venv\Scripts\activate.bat" (
rem     call .venv\Scripts\activate.bat
rem )
rem 
rem rem OLD (2026-05-24): start /B cmd /c "ollama serve 2>nul"
rem rem NEW (2026-05-27): silence all handles to avoid "handle is invalid" errors
rem start /B cmd /c "set OLLAMA_NOHISTORY=1 & ollama serve >nul 2>&1"
rem timeout /t 2 /nobreak > nul
rem 
rem rem OLD (2026-05-25): Used python directly without venv path
rem if exist ".venv\Scripts\python.exe" (
rem     .venv\Scripts\python.exe main.py
rem ) else (
rem     python main.py
rem )
rem 
rem echo.
rem echo  Manager OS has stopped.
rem pause
