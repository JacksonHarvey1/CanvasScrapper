@echo off
echo Canvas File Scraper
echo ==================
echo.
echo Available options:
echo --url, -u       : Canvas URL (e.g., https://ycp.instructure.com)
echo --username, -e  : Canvas username/email
echo --password, -p  : Canvas password (not recommended)
echo --dir, -d       : Download directory (default: Canvas_Downloads)
echo --no-skip       : Don't skip existing files (re-download all)
echo --headless      : Run Chrome in headless mode (no visible browser)
echo --delay         : Delay in seconds between actions (default: 2)
echo --debug         : Enable debug logging
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in your PATH.
    echo Please install Python from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b
)

REM Check if requirements are installed
echo Checking and installing required packages...
pip install -r requirements.txt

echo.
echo Starting Canvas Scraper...
echo.

REM Pass all command-line arguments to the Python script
python CanvasScraper.py %*

echo.
pause
