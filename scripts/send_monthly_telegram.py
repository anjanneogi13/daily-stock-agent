"""Sends monthly X-ray summary to Telegram."""
import os, urllib.request, urllib.parse, sys
from datetime import datetime
from pathlib import Path

def _compact_for_telegram(md: str) -> str:
    """Remove verbose parameter inventory; keep stats + suggestions."""
    import re
    # Remove the "### 📋 Current strategy parameters" block (until next ### or end)
    md = re.sub(r"### 📋 Current strategy parameters.*?(?=\n### |\Z)", "", md, flags=re.DOTALL)
    # Collapse 3+ blank lines
    md = re.sub(r"\n{3,}", "\n\n", md)
    return md.strip()


TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_IDS = [c for c in [os.environ.get("TELEGRAM_CHAT_ID"), os.environ.get("TELEGRAM_GROUP_CHAT_ID")] if c]
if not TOKEN or not CHAT_IDS:
    print("[telegram] Missing creds"); sys.exit(0)

date = datetime.now().strftime("%Y-%m-%d")
p = Path(f"data/learning/monthly_xray_{date}.md")
summary = _compact_for_telegram(p.read_text())[:3500] if p.exists() else "Not generated"
msg = f"📅 *Monthly X-Ray Ready*\n\n{summary}\n\nFull review in GitHub issues."
if len(msg) > 4000:
    msg = msg[:3950] + "\n_(truncated)_"

url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
for _cid in CHAT_IDS:
    data = urllib.parse.urlencode({
        "chat_id": _cid, "text": msg,
         "disable_web_page_preview": "true",
    }).encode()
    try:
        urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=10)
        print("[telegram] ✅ Sent")
    except Exception as e:
        print(f"[telegram] ❌ {e}")
