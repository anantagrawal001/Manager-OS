@echo off
chcp 65001 > nul
title MANAGER OS — Background Server

echo.
echo  Manager OS — Second Laptop Background Server
echo  Starting background tasks...
echo.

if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

python second_laptop\server.py

echo.
echo  Background server stopped.
pause
