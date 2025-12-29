@echo off
REM GitIntel Dataset Generator - Simple Launcher
REM Usage: Set your API key and run

echo.
echo ========================================
echo   GitIntel Dataset Generator
echo ========================================
echo.

REM Check if API key is already set in environment
if defined GOOGLE_API_KEY (
    echo [OK] GOOGLE_API_KEY found in environment
    goto :run_app
)

REM Ask user for API key
echo [!] GOOGLE_API_KEY not found
echo.
set /p api_key="Enter your Google Gemini API Key: "

if "%api_key%"=="" (
    echo [ERROR] API key cannot be empty!
    pause
    exit /b 1
)

REM Set API key for this session
set GOOGLE_API_KEY=%api_key%
echo [OK] API key set for this session

:run_app
echo.
echo [*] Starting GitIntel Dataset Generator...
echo.
python main.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Application failed to start
    echo.
    echo Common issues:
    echo   1. Python not installed or not in PATH
    echo   2. Missing dependencies: pip install -r ../requirements.txt
    echo   3. Invalid API key
    echo.
    pause
)
