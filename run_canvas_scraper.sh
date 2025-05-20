#!/bin/bash

echo "Canvas File Scraper"
echo "=================="
echo
echo "Available options:"
echo "--url, -u       : Canvas URL (e.g., https://ycp.instructure.com)"
echo "--username, -e  : Canvas username/email"
echo "--password, -p  : Canvas password (not recommended)"
echo "--dir, -d       : Download directory (default: Canvas_Downloads)"
echo "--no-skip       : Don't skip existing files (re-download all)"
echo "--headless      : Run Chrome in headless mode (no visible browser)"
echo "--delay         : Delay in seconds between actions (default: 2)"
echo "--debug         : Enable debug logging"
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed or not in your PATH."
    echo "Please install Python 3 using your package manager:"
    echo "  - For Ubuntu/Debian: sudo apt install python3 python3-pip"
    echo "  - For macOS: brew install python3"
    echo
    read -p "Press Enter to exit..."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "pip3 is not installed or not in your PATH."
    echo "Please install pip3 using your package manager:"
    echo "  - For Ubuntu/Debian: sudo apt install python3-pip"
    echo "  - For macOS: brew install python3"
    echo
    read -p "Press Enter to exit..."
    exit 1
fi

# Check if requirements are installed
echo "Checking and installing required packages..."
pip3 install -r requirements.txt

echo
echo "Starting Canvas Scraper..."
echo

# Pass all command-line arguments to the Python script
python3 CanvasScraper.py "$@"

echo
read -p "Press Enter to exit..."
