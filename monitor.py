import time
import requests
import os
import re
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# --- CONFIGURATION ---
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
WEBSITE_URL = "https://cyberleek.perma.online/"
SAVE_FILE = "last_leaks.txt"
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB Telegram limit

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"}
    requests.post(url, json=payload)

def send_telegram_file(file_path, caption=""):
    is_video = file_path.lower().endswith(('.mp4', '.mov', '.mkv', '.webm'))
    endpoint = "sendVideo" if is_video else "sendDocument"
    file_key = "video" if is_video else "document"
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/{endpoint}"
    with open(file_path, "rb") as f:
        files = {file_key: f}
        data = {"chat_id": TELEGRAM_CHAT_ID, "caption": caption[:1024]}
        requests.post(url, data=data, files=files)

def resolve_download_link(driver, mirror_url):
    """Visits the host landing page and attempts to find the actual download URL."""
    try:
        driver.get(mirror_url)
        time.sleep(5)  # Wait for host page to load
        
        # Look for standard download buttons or direct video source tags
        links = driver.find_elements(By.TAG_NAME, "a")
        for link in links:
            href = link.get_attribute("href")
            text = (link.text or "").lower()
            if href and any(term in text for term in ["download", "telecharger", "get file", "direct"]):
                return href
            if href and href.lower().endswith(('.mp4', '.zip', '.rar', '.mkv')):
                return href
                
        # If no explicit button matched, check for direct HTML5 video elements
        videos = driver.find_elements(By.TAG_NAME, "video")
        for v in videos:
            src = v.get_attribute("src")
            if src:
                return src
                
    except Exception as e:
        print(f"Failed to resolve {mirror_url}: {e}")
    return mirror_url  # Fallback to landing page if unresolvable

def check_for_leaks():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    
    try:
        driver.get(WEBSITE_URL)
        time.sleep(15)
        
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
                # 1. Collect all mirror button links from the main page
                links_elements = driver.find_elements(By.TAG_NAME, "a")
                mirror_links = []
                for el in links_elements:
                    href = el.get_attribute("href")
                    if href and ("bedrive" in href or "temp.sh" in href or "mirror" in (el.text or "").lower()):
                        mirror_links.append((el.text.strip(), href))
                
                # Send the initial text notification
                send_telegram_message(
                    f"🚨 <b>New CyberLeek Dropped!</b>\n\n"
                    f"{leeks_section[:400]}...\n\n"
                    f"🌐 {WEBSITE_URL}"
                )
                
                # 2. Iterate through mirrors and attempt download
                for title, mirror_url in mirror_links:
                    print(f"Resolving mirror: {mirror_url}")
                    final_download_url = resolve_download_link(driver, mirror_url)
                    
                    filename = "temp_leak.mp4"
                    try:
                        headers = {"User-Agent": "Mozilla/5.0"}
                        with requests.get(final_download_url, headers=headers, stream=True, timeout=30) as r:
                            if r.status_code == 200:
                                with open(filename, "wb") as f:
                                    for chunk in r.iter_content(chunk_size=8192):
                                        f.write(chunk)
                                
                                size = os.path.getsize(filename)
                                # Check if the downloaded file is actually a video and not an HTML error page
                                if size <= MAX_FILE_SIZE and size > 50000:
                                    send_telegram_file(filename, caption=f"🎬 {title}\nMirror: {mirror_url}")
                                else:
                                    send_telegram_message(f"🔗 <b>{title}</b> ({mirror_url})\n(File > 50MB or HTML page)")
                            else:
                                send_telegram_message(f"⚠️ <b>{title}</b> link returned status {r.status_code} (Dead/Deleted mirror).")
                    except Exception as err:
                        print(f"Download error on {mirror_url}: {err}")
                    finally:
                        if os.path.exists(filename):
                            os.remove(filename)

                # 3. Update memory
                with open(SAVE_FILE, "w", encoding="utf-8") as f:
                    f.write(leeks_section)
                    
    finally:
        driver.quit()

if __name__ == "__main__":
    for i in range(5):
        check_for_leaks()
        if i < 4:
            time.sleep(45)
