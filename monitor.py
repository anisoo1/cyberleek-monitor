import time
import requests
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# Pulls your secrets safely from GitHub
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
WEBSITE_URL = "https://cyberleek.perma.online/"
SAVE_FILE = "last_leaks.txt"

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
    requests.post(url, json=payload)

def check_for_leaks():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    
    try:
        driver.get(WEBSITE_URL)
        time.sleep(15) # Wait for API to load
        
        body_text = driver.find_element(By.TAG_NAME, "body").text
        
        if "LEEKS ▼" in body_text and "POLL ▼" in body_text:
            leeks_section = body_text.split("LEEKS ▼")[1].split("POLL ▼")[0].strip()
            
            if "loading..." in leeks_section.lower() or not leeks_section:
                return

            last_leaks = ""
            if os.path.exists(SAVE_FILE):
                with open(SAVE_FILE, "r", encoding="utf-8") as f:
                    last_leaks = f.read()

            if leeks_section != last_leaks:
                message = f"🚨 New activity on CyberLeek!\n\n{leeks_section[:500]}...\n\nLink: {WEBSITE_URL}"
                send_telegram_message(message)
                
                with open(SAVE_FILE, "w", encoding="utf-8") as f:
                    f.write(leeks_section)
    finally:
        driver.quit()

if __name__ == "__main__":
    # GitHub cron runs every 5 mins. 
    # We loop 3 times per run. 15s load + 75s wait = 90 seconds (1:30 min checks)
    for i in range(3):
        check_for_leaks()
        if i < 2:
            time.sleep(75)
