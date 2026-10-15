@echo off
cd /d "%~dp0"
".venv\Scripts\python.exe" setup\reset_passphrase.py
if errorlevel 1 (
  pause
  exit /b 1
)
call startup.bat
