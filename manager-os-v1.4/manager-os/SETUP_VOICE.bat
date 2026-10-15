@echo off
setlocal
cd /d "%~dp0"
set PYTHONUTF8=1
if not exist ".venv\Scripts\python.exe" (
    echo Run SETUP.bat first.
    pause
    exit /b 1
)
".venv\Scripts\python.exe" -m pip install openai-whisper==20231117
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -c "import whisper; whisper.load_model('base',device='cpu'); print('Local speech model ready')"
if errorlevel 1 goto failed
echo Local speech is ready. Use Local mic in the dashboard.
pause
exit /b 0
:failed
echo Voice setup failed. See the error above. Text chat still works.
pause
exit /b 1
