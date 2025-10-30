@echo off
REM Setup script for Git Analysis Tool
REM Run this script to install dependencies and set up the tool

echo Installing Git Analysis Tool Dependencies...
echo =============================================

REM Install Python dependencies
pip install -r requirements.txt

echo.
echo Dependencies installed successfully!
echo.
echo Usage Examples:
echo ===============
echo.
echo 1. Interactive mode:
echo    python llm_git_cli.py --interactive
echo.
echo 2. Direct command:
echo    python llm_git_cli.py "Find packages with 500+ lines and create Excel"
echo.
echo 3. Clone and analyze:
echo    python llm_git_cli.py "Clone https://github.com/spring-projects/spring-boot and analyze"
echo.
echo 4. Release analysis:
echo    python llm_git_cli.py "Check releases and show changes"
echo.
echo ✅ Setup complete! You can now use the tool.
pause