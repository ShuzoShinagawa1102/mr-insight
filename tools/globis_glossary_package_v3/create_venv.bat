@echo off
setlocal
cd /d "%~dp0"

chcp 65001 >nul
set PYTHONUTF8=1

python --version >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Python is not found. Install Python 3.10+ and add to PATH.
  pause
  exit /b 1
)

if not exist ".venv" (
  echo [INFO] Creating venv...
  python -m venv .venv
)

call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
echo [DONE] venv ready.
pause
