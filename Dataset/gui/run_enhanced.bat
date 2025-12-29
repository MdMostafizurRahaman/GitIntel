@echo off
echo ========================================
echo   Enhanced Agentic Dataset Maker
echo   with LLM Jury System
echo ========================================
echo.

cd /d "%~dp0"

echo Checking Python installation...
python --version
if errorlevel 1 (
    echo ERROR: Python not found!
    pause
    exit /b 1
)

echo.
echo Installing/Updating requirements...
pip install -r requirements.txt -q

echo.
echo Starting Enhanced Interactive GUI...
echo.
python enhanced_interactive_gui.py

pause
