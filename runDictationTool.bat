@echo off
REM Change to the directory where this script is located
cd /d "%~dp0"

REM Run the Python script
python dictate_with_hotkey.py

REM Keep the window open if there is any output
pause
