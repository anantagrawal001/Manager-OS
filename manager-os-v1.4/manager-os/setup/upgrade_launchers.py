from pathlib import Path

launch = r'''@echo off
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
'''
setup = r'''@echo off
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
'''
for name, content in [('startup.bat', launch), ('SETUP.bat', setup)]:
    path = Path(name)
    old = path.read_text(encoding='utf-8-sig')
    path.write_text(content + '\nrem Archived 2026-10-12, retained for rollback:\n' + '\n'.join('rem '+line for line in old.splitlines())+'\n', encoding='utf-8')

# Consolidate duplicate YAML mappings, retaining original text for reference.
import yaml
p=Path('config.yaml')
source=p.read_text(encoding='utf-8')
config=yaml.safe_load(source)
config['ai_router'].update({'local_first':True,'local_only':False,'request_timeout_seconds':90})
config['voice']['enabled']=True
config['voice']['tts_engine']='pyttsx3'
config['storage']['tasks_path']='./logs/tasks.db'
config['chrome']['user_data_path']='./logs/chrome_automation'
config['chrome']['connect_existing']=False
config['trading_alerts']['enabled']=False
config['self_heal']['auto_fix']=False
p.write_text('# Active configuration — consolidated 2026-10-12\n'+yaml.safe_dump(config,sort_keys=False,allow_unicode=True)+'\n# Prior configuration retained for rollback:\n'+'\n'.join('# '+line for line in source.splitlines())+'\n',encoding='utf-8')
print('Launchers and config updated')
