@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul
set PYTHONUTF8=1
title Manager OS Setup
echo Setting up Manager OS. Existing keys and history will be preserved.
if exist ".venv\Scripts\python.exe" goto install
py -3.11 --version >nul 2>&1
if not errorlevel 1 (
    py -3.11 -m venv .venv
    if errorlevel 1 goto failed
    goto install
)
python -c "import sys; assert sys.version_info[:2] == (3,11)" >nul 2>&1
if errorlevel 1 (
    echo Python 3.11 is required. Install Python 3.11 from python.org, then run this file again.
    goto failed
)
python -m venv .venv
if errorlevel 1 goto failed
:install
".venv\Scripts\python.exe" setup\bootstrap.py
if errorlevel 1 goto failed
echo Run startup.bat to open Manager OS.
pause
exit /b 0
:failed
echo Setup did not complete. The error above identifies the failed step.
pause
exit /b 1

rem Archived 2026-10-12, retained for rollback:
rem @echo off
rem chcp 65001 > nul
rem set PYTHONUTF8=1
rem title MANAGER OS - Setup
rem 
rem echo.
rem echo ==============================================================
rem echo.
rem echo     M A N A G E R   O S
rem echo     Auto Setup - Please Wait
rem echo.
rem echo ==============================================================
rem echo.
rem echo  Sir, this will set up Manager OS completely.
rem echo  Please do not close this window.
rem echo.
rem 
rem :: --- Check Python -----------------------------------------------------------
rem echo  [1/8] Checking Python installation...
rem python --version > nul 2>&1
rem if %errorlevel% neq 0 (
rem     echo       Python not found. Please install Python 3.11+ from https://www.python.org/downloads/
rem     echo       After installing Python, re-open this terminal and re-run this script.
rem     pause
rem     exit /b 1
rem ) else (
rem     for /f "tokens=2" %%i in ('python --version 2^>^&1') do echo       Python %%i found.
rem )
rem 
rem :: --- Create virtual environment ---------------------------------------------
rem echo.
rem echo  [2/8] Creating virtual environment...
rem if not exist ".venv" (
rem     python -m venv .venv
rem     echo       Virtual environment created.
rem ) else (
rem     echo       Virtual environment already exists.
rem )
rem 
rem :: Activate venv
rem call .venv\Scripts\activate.bat
rem 
rem :: --- Install dependencies ----------------------------------------------------
rem echo.
rem echo  [3/8] Installing dependencies (this may take 2-3 minutes)...
rem python -m pip install --upgrade pip --quiet
rem pip install -r requirements.txt --quiet
rem echo       Dependencies installed.
rem 
rem :: --- Install Playwright -----------------------------------------------------
rem echo.
rem echo  [4/8] Installing browser automation (Playwright + Chromium)...
rem python -m playwright install chromium --quiet 2>nul
rem echo       Browser automation ready.
rem 
rem :: --- Check/Install Ollama ---------------------------------------------------
rem echo.
rem echo  [5/8] Setting up local AI (Ollama)...
rem ollama version > nul 2>&1
rem if %errorlevel% neq 0 (
rem     echo       Ollama not found. Skipping local Ollama installation.
rem     echo       To enable local AI, install Ollama from https://ollama.com and run:
rem     echo         ollama pull llama3.1:8b
rem     echo         ollama pull nomic-embed-text
rem ) else (
rem     echo       Ollama already installed.
rem     start /B cmd /c "set OLLAMA_NOHISTORY=1 & ollama pull llama3.1:8b >nul 2>&1"
rem     echo       Checking AI models in background...
rem )
rem 
rem :: --- GPU drivers check -------------------------------------------------------
rem echo.
rem echo  [6/8] Checking GPU driver...
rem for /f "tokens=*" %%i in ('powershell -Command "Get-WmiObject Win32_VideoController | Select-Object -ExpandProperty DriverVersion" 2^>nul') do set GPU_DRIVER=%%i
rem echo       GPU Driver: %GPU_DRIVER%
rem echo       RTX 5060 - ensure NVIDIA drivers are up to date at nvidia.com/drivers
rem 
rem :: --- Create required directories -------------------------------------------
rem echo.
rem echo  [7/8] Creating directory structure...
rem if not exist "logs" mkdir logs
rem if not exist "backups" mkdir backups
rem if not exist "security\identity" mkdir security\identity
rem if not exist "security\voice_prints" mkdir security\voice_prints
rem if not exist "skills\registry" mkdir skills\registry
rem if not exist "skills" mkdir skills
rem if not exist "setup" mkdir setup
rem if not exist "ui\assets" mkdir ui\assets
rem if not exist "sync" mkdir sync
rem echo       Directories created.
rem 
rem :: --- First run Python setup -------------------------------------------------
rem echo.
rem echo  [8/8] Running first-time configuration...
rem echo       (API keys, voice enrollment, database setup)
rem echo.
rem echo  NOTE: You'll be asked to paste API keys for these FREE providers:
rem echo.
rem echo    1. Groq (fastest free inference)     → console.groq.com/keys
rem echo    2. Google AI Studio (Gemini free)    → aistudio.google.com/apikey
rem echo    3. NVIDIA NIM (premium free models)  → build.nvidia.com
rem echo    4. Anthropic (Claude)                → console.anthropic.com
rem echo    5. OpenRouter (100+ models)          → openrouter.ai/keys
rem echo    6. ElevenLabs (premium voice)        → elevenlabs.io
rem echo.
rem python setup\first_run.py
rem 
rem :: --- Done -------------------------------------------------------------------
rem echo.
rem echo ==============================================================
rem echo.
rem echo  Setup complete, Sir.
rem echo.
rem echo  Run startup.bat to launch Manager OS.
rem echo.
rem echo ==============================================================
rem echo.
rem pause
