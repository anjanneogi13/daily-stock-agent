#!/usr/bin/env python3
"""Send intraday alert to Telegram (dual-chat: personal + group)."""
import os, sys, json, urllib.parse, urllib.request
from pathlib import Path
from datetime import datetime, timezone

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_IDS = [c for c in [
    os.environ.get("TELEGRAM_CHAT_ID"),
    os.environ.get("TELEGRAM_GROUP_CHAT_ID"),
] if c]

if not TOKEN or not CHAT_IDS:
    print("[telegram] Missing creds — skipping"); sys.exit(0)

TODAY = datetime.now(timezone.utc).strftime("%Y-%m-%d")
ALERT_FILE = Path(f"data/intraday_alert_{TODAY}.md")

if not ALERT_FILE.exists():
    print(f"[telegram] No alert file at {ALERT_FILE} — nothing to send. ✅")
    sys.exit(0)

msg = ALERT_FILE.read_text().strip()
if not msg:
    print("[telegram] Empty alert — skipping"); sys.exit(0)

if len(msg) > 4000:
    msg = msg[:3950] + "\n\n_(truncated)_"

url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
for _cid in CHAT_IDS:
    data = urllib.parse.urlencode({
        "chat_id": _cid, "text": msg,
        "parse_mode": "Markdown", "disable_web_page_preview": "true",
    }).encode()
    try:
        resp = urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=10)
        result = json.loads(resp.read())
        print(f"[telegram→{_cid}] {'✅ Sent' if result.get('ok') else '❌ '+str(result)}")
    except Exception as e:
        print(f"[telegram→{_cid}] ❌ {e}")

# Delete the alert file so it doesn't get resent on next run if no new content
ALERT_FILE.unlink(missing_ok=True)
