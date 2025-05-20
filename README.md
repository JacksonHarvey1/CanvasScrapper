# Canvas File Scraper

A tool to download all files from your Canvas courses while maintaining the original folder structure.

## Features

- Automatically logs in to your Canvas account
- Downloads all files from all accessible courses
- Finds files in multiple locations:
  - Course homepages (direct links and links to pages with files)
  - Course modules
  - Files section
- Maintains the original folder structure from Canvas
- Supports different authentication methods (Microsoft, Google, Canvas native)
- Shows download progress with progress bars
- Option to skip already downloaded files
- Handles various Canvas instances (not just instructure.com)
- Detailed logging for troubleshooting
- Screenshots of each step for debugging
- Configurable delay between actions for visibility

## Requirements

- Python 3.7 or higher
- Chrome browser installed

## Installation

1. Clone this repository or download the files
2. Install the required packages:

```bash
pip install -r requirements.txt
```

## Usage

### Windows

Double-click the `run_canvas_scraper.bat` file to run the script interactively.

You can also run it with command-line arguments:
```
run_canvas_scraper.bat --url https://ycp.instructure.com --username your_email@example.com
```

### macOS and Linux

1. Make the script executable (one-time setup):
   ```bash
   chmod +x run_canvas_scraper.sh
   ```

2. Run the script interactively:
   ```bash
   ./run_canvas_scraper.sh
   ```

3. Or run it with command-line arguments:
   ```bash
   ./run_canvas_scraper.sh --url https://ycp.instructure.com --username your_email@example.com
   ```

### Manual Execution

You can also run the script directly with Python:

```bash
python CanvasScraper.py  # Windows
python3 CanvasScraper.py  # macOS/Linux
```

The script will prompt you for:
- Your Canvas URL (e.g., https://ycp.instructure.com)
- Your username/email
- Your password
- Download directory (default: Canvas_Downloads)
- Whether to skip existing files

### Command-Line Arguments

For automation or scripting, you can use command-line arguments:

```bash
python CanvasScraper.py --url https://ycp.instructure.com --username your_email@example.com --dir MyDownloads
```

Available options:
- `--url`, `-u`: Canvas URL (e.g., https://ycp.instructure.com)
- `--username`, `-e`: Canvas username/email
- `--password`, `-p`: Canvas password (not recommended, use interactive prompt instead)
- `--dir`, `-d`: Download directory (default: Canvas_Downloads)
- `--no-skip`: Don't skip existing files (re-download all)
- `--headless`: Run Chrome in headless mode (no visible browser)
- `--delay`: Delay in seconds between actions for visibility (default: 2)
- `--debug`: Enable debug logging

For security reasons, it's better to omit the password and let the script prompt you for it.

## How It Works

1. The script opens a Chrome browser window and logs in to your Canvas account
2. It navigates to your courses page and identifies all available courses
3. For each course, it:
   - First checks the course homepage for files and clickable links that lead to files
   - Then checks the Modules section for files
   - Finally checks the Files section
4. It recursively processes all folders and downloads all files
5. Files are saved in a directory structure that matches Canvas, with separate folders for:
   - Homepage files
   - Module files (organized by module)
   - Files section files (maintaining the original folder structure)

## Troubleshooting

### Login Issues

If you're having trouble logging in:
- Try manually logging in to Canvas in a browser first
- Make sure your credentials are correct
- If your institution uses a different authentication method, the script will try to detect it automatically
- Check the screenshots in the `screenshots` directory to see where the login process failed
- Review the log file for detailed error messages

### Download Issues

If files aren't downloading correctly:
- Check your internet connection
- Ensure you have write permissions for the download directory
- Try running the script again with the "skip existing files" option set to No to re-download problematic files
- Use the `--debug` flag to enable more detailed logging
- Increase the `--delay` value if actions are happening too quickly

### Finding Files Issues

If the script isn't finding all the files you expect:
- The script now checks multiple locations for files:
  - Direct downloadable links on course homepages
  - Links on course homepages that lead to pages with downloadable files
  - Files in course modules
  - Files in the dedicated Files section
- If files are still missing, try increasing the `--delay` value to give pages more time to load
- Check the log file to see which pages were visited and what files were found

### Debugging

The script creates two types of debugging information:
1. **Log Files**: Detailed logs are saved to a file named `canvas_scraper_YYYYMMDD_HHMMSS.log` in the current directory
2. **Screenshots**: Screenshots of each step are saved to the `screenshots` directory

These files can be helpful for troubleshooting issues or understanding what happened during the scraping process.

## Privacy & Security

- Your credentials are only used for logging in and are not stored anywhere
- All downloads happen locally on your computer
- No data is sent to any third-party servers

## License

This project is open source and available for anyone to use and modify.
