@echo off
setlocal
cd /d "%~dp0"

chcp 65001 >nul
set PYTHONUTF8=1

if not exist ".venv\Scripts\activate.bat" (
  echo [ERROR] Run create_venv.bat first.
  pause
  exit /b 1
)

call .venv\Scripts\activate.bat
python -X utf8 globis_glossary_by_category.py --output "glossary_terms.txt" --log "run.log" %*

echo.
echo [DONE] glossary_terms.txt created.
echo [DONE] run.log updated.
pause
