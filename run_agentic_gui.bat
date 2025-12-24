@echo off
echo ============================================
echo  GitIntel Agentic Dataset Generator
echo  VS Code Copilot Style Interface
echo ============================================
echo.

cd /d "%~dp0"
cd Dataset

echo Starting GUI...
python gui/main.py

pause
