# Advanced Monitoring System (AMS)

## Warning
**This code is designed for ethical and educational purposes only.**  
**It should never be used without explicit permission from the owner of the system being monitored.**  
Unauthorized monitoring, keylogging, clipboard reading, or capturing of sensitive information is illegal in most jurisdictions and is a violation of privacy.  
By running this software, you agree to take full responsibility for your actions and ensure that you comply with all applicable laws and regulations.

## Features

- **Keystroke Logging**: Captures and logs keystrokes (excluding sensitive fields) to the terminal and JSON log file.
- **Credential Capture**: Detects sensitive fields like login forms and captures usernames and passwords typed or copied into them.
- **Sensitive Field Detection**: Automatically identifies fields like username, password, and credit card numbers.
- **Screenshot Capture**: Takes screenshots at regular intervals (configurable) and saves them to the `screenshots` directory.
- **Clipboard Monitoring**: Captures clipboard data (if configured) and checks if it contains sensitive information.
- **Email Reporting**: Sends an email with activity reports (last 20 entries) at regular intervals (configurable).
- **Activity Logging**: Logs all activities in a JSON file with timestamps and window titles, including keystrokes, clipboard data, and screenshots.

## Installation

### Dependencies

This script requires the following Python libraries:
- `keyboard`
- `pyautogui`
- `pyscreenshot`
- `requests`
- `beautifulsoup4`
- `pywin32`

You can install them using pip:

```bash
pip install keyboard pyautogui pyscreenshot requests beautifulsoup4 pywin32
