"""Sends monthly X-ray summary to Telegram."""
import os, urllib.request, urllib.parse, sys
from datetime import datetime
from pathlib import Path

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
if not TOKEN or not CHAT_ID:
    print("[telegram] Missing creds"); sys.exit(0)

date = datetime.now().strftime("%Y-%m-%d")
p = Path(f"data/learning/monthly_xray_{date}.md")
summary = p.read_text()[:3500] if p.exists() else "Not generated"
msg = f"📅 *Monthly X-Ray Ready*\n\n{summary}\n\nFull review in GitHub issues."
if len(msg) > 4000:
    msg = msg[:3950] + "\n_(truncated)_"

url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
data = urllib.parse.urlencode({
    "chat_id": CHAT_ID, "text": msg,
     "disable_web_page_preview": "true",
}).encode()
try:
    urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=10)
    print("[telegram] ✅ Sent")
except Exception as e:
    print(f"[telegram] ❌ {e}")