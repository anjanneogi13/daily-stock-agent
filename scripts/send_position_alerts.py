"""Send Telegram alerts for positions exceeding max_hold_days.

Pattern follows scripts/send_weekend_telegram.py:
  - Direct POST to Telegram API
  - Dedup via dedup_sender.should_send_report
  - Silent exit (code 0) on missing creds or no alerts
  - FORCE_RESEND=1 to override dedup

Run after the daily evaluator (or on its own schedule).
"""
import os
import sys
from datetime import date
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.dedup_sender import should_send_report, mark_report_sent
from src.position_monitor import scan_open_positions, format_telegram_summary

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT = os.environ.get("TELEGRAM_CHAT_ID")
TODAY = date.today().isoformat()
REPORT_TYPE = "position_alerts"

if not TOKEN or not CHAT:
    print("[position_alerts] Missing TELEGRAM_BOT_TOKEN/CHAT_ID — exit 0")
    sys.exit(0)

alerts = scan_open_positions()
if not alerts:
    print("[position_alerts] No overdue/near positions — nothing to send")
    sys.exit(0)

if not should_send_report(REPORT_TYPE, TODAY):
    print(f"[position_alerts] ⏭  Already sent today ({TODAY}) — "
          "set FORCE_RESEND=1 to override")
    sys.exit(0)

msg = format_telegram_summary(alerts)
print(f"[position_alerts] {len(alerts)} alert(s) — sending...")

url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
payload = {
    "chat_id": CHAT,
    "text": msg,
    "parse_mode": "HTML",
    "disable_web_page_preview": True,
}

try:
    r = requests.post(url, json=payload, timeout=10)
    if r.status_code == 200:
        mark_report_sent(REPORT_TYPE, TODAY)
        print("[position_alerts] ✅ Sent")
    else:
        # Fallback to plain text if HTML parse fails (matches BUG fix pattern)
        print(f"[position_alerts] ⚠  HTML send failed: {r.status_code} — "
              "trying plain text")
        plain = msg.replace("<b>", "").replace("</b>", "")
        payload["text"] = plain
        payload.pop("parse_mode", None)
        r2 = requests.post(url, json=payload, timeout=10)
        if r2.status_code == 200:
            mark_report_sent(REPORT_TYPE, TODAY)
            print("[position_alerts] ✅ Sent (plain text fallback)")
        else:
            print(f"[position_alerts] ❌ Plain also failed: {r2.status_code} "
                  f"{r2.text[:200]}")
            sys.exit(1)
except Exception as e:
    print(f"[position_alerts] ❌ Exception: {e}")
    sys.exit(1)
