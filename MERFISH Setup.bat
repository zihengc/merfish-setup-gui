@echo off
rem Double-click launcher for the MERFISH Setup GUI on Windows.
rem Uses the Python launcher (py/pyw) or python on PATH; pythonw keeps a console window from staying open.
setlocal
cd /d "%~dp0"
set "APP=app\merfish_setup_gui.py"
set "CHECK=import sys, tkinter; sys.exit(0 if sys.version_info >= (3, 9) else 1)"

py -3 -c "%CHECK%" >nul 2>&1
if not errorlevel 1 (
    start "" pyw -3 "%APP%"
    exit /b 0
)
python -c "%CHECK%" >nul 2>&1
if not errorlevel 1 (
    start "" pythonw "%APP%"
    exit /b 0
)

echo Python 3.9 or newer was not found.
echo Install it from https://www.python.org/downloads/ (tick "Add python.exe to PATH"),
echo then double-click "MERFISH Setup.bat" again.
pause
exit /b 1
