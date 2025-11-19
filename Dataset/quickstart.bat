@echo off
REM Dataset Management System - Quick Start Script for Windows
REM Windows-এর জন্য দ্রুত শুরুর স্ক্রিপ্ট

setlocal enabledelayedexpansion

echo.
echo ================================================================================
echo    Dataset Management System - Quick Start (Windows)
echo ================================================================================
echo.

REM Check Python
echo [*] Checking Python installation...
where python > nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
    echo [+] Python !PYTHON_VERSION! found
) else (
    echo [-] Python not found. Please install Python 3.8 or higher.
    echo.
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Check if in correct directory
if not exist "requirements.txt" (
    echo [-] requirements.txt not found.
    echo     Please run this script from Dataset directory.
    pause
    exit /b 1
)

echo [+] In correct directory

REM Create virtual environment if not exists
if not exist "venv" (
    echo.
    echo [*] Creating virtual environment...
    python -m venv venv
    if %errorlevel% equ 0 (
        echo [+] Virtual environment created
    ) else (
        echo [-] Failed to create virtual environment
        pause
        exit /b 1
    )
) else (
    echo [+] Virtual environment already exists
)

REM Activate virtual environment
echo.
echo [*] Activating virtual environment...
call venv\Scripts\activate.bat
if %errorlevel% equ 0 (
    echo [+] Virtual environment activated
) else (
    echo [-] Failed to activate virtual environment
    pause
    exit /b 1
)

REM Install requirements
echo.
echo [*] Installing Python packages...
echo     (This may take a few minutes on first run)
python -m pip install --upgrade pip -q
python -m pip install -r requirements.txt -q

if %errorlevel% equ 0 (
    echo [+] Packages installed successfully
) else (
    echo [-] Failed to install packages
    pause
    exit /b 1
)

REM Verify installation
echo.
echo [*] Verifying installation...
python verify_installation.py

if %errorlevel% equ 0 (
    cls
    echo.
    echo ================================================================================
    echo [+] Installation Complete! System Ready to Use
    echo ================================================================================
    echo.
    echo Next Steps:
    echo.
    echo 1. READ DOCUMENTATION:
    echo    - docs/SETUP.md          (Configuration & Neo4j setup)
    echo    - docs/EXAMPLES.md       (Complete usage examples)
    echo    - docs/ARCHITECTURE.md   (System design)
    echo.
    echo 2. CONFIGURE NEO4J:
    echo    - Create .env file with Neo4j credentials
    echo    - Or set environment variables
    echo    - Test connection: python -m cli.main status
    echo.
    echo 3. CHOOSE YOUR INTERFACE:
    echo.
    echo    A) Command-Line Interface (CLI):
    echo       python -m cli.main --help
    echo       python -m cli.main list-datasets
    echo.
    echo    B) Desktop GUI Application (PyQt5):
    echo       python -m gui.app
    echo.
    echo    C) REST API Server (FastAPI):
    echo       python -m api.server
    echo       (Access at http://127.0.0.1:8000)
    echo.
    echo ================================================================================
    echo [+] Quick Commands Reference:
    echo ================================================================================
    echo.
    echo Extract Data:
    echo   python -m cli.main extract --dataset-type defects4j --source C:\path\to\repo --output data.json
    echo.
    echo Process Data:
    echo   python -m cli.main process --input data.json --output processed.json --normalize-code
    echo.
    echo Label Data:
    echo   python -m cli.main label --input data.json --output labeled.json --label-type bug_severity
    echo.
    echo Import to Neo4j:
    echo   python -m cli.main import-to-neo4j --input labeled.json --dataset-name "My Dataset"
    echo.
    echo ================================================================================
    echo.
    echo To get started, read docs/SETUP.md and choose your interface above.
    echo.
    pause
) else (
    echo.
    echo ================================================================================
    echo [-] Installation Verification Failed
    echo ================================================================================
    echo.
    echo Please fix the issues shown above and try again.
    echo.
    echo For help, see docs/SETUP.md
    echo.
    pause
    exit /b 1
)
