"""Sends weekend reflection summary to Telegram (safely)."""
import os, sys, urllib.request, urllib.parse
from datetime import datetime
from pathlib import Path

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
if not TOKEN or not CHAT_ID:
    print("[telegram] Missing creds"); sys.exit(0)

date = datetime.now().strftime("%Y-%m-%d")
p = Path(f"data/learning/weekly_review_{date}.md")
summary = p.read_text() if p.exists() else "Weekly review not generated."

# Trim to fit Telegram limit
if len(summary) > 3500:
    summary = summary[:3500] + "\n...(truncated — see GitHub issue for full review)"

msg = f"🧠 Weekend Review Ready\n\n{summary}\n\n📋 Full review + action items in your GitHub issues."

# IMPORTANT: send as PLAIN TEXT (no parse_mode) to avoid Markdown 400 errors
url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
data = urllib.parse.urlencode({
    "chat_id": CHAT_ID,
    "text": msg,
    "disable_web_page_preview": "true",
}).encode()

try:
    resp = urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=10)
    print("[telegram] ✅ Sent")
except Exception as e:
    print(f"[telegram] ❌ {e}")
    sys.exit(1)
    