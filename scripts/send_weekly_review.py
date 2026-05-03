"""
Generate weekly self-assessment + send to Telegram.
Save markdown snapshot to reports/weekly/.

Usage:
  python scripts/send_weekly_review.py             # send + save
  python scripts/send_weekly_review.py --no-send   # save only
"""
import os
import sys
import requests
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.weekly_review import build_report, format_telegram, save_snapshot


def send(text: str) -> bool:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("⚠️  TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set — skipping send")
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        r = requests.post(url, json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown",
        }, timeout=10)
        if r.ok:
            print("✅ Sent to Telegram")
            return True
        print(f"❌ Telegram API error: {r.status_code} {r.text[:200]}")
        return False
    except Exception as e:
        print(f"❌ Send failed: {e}")
        return False


def main():
    no_send = "--no-send" in sys.argv
    r = build_report()
    text = format_telegram(r)
    out = save_snapshot(r)
    print(f"📁 Snapshot saved: {out}")
    print()
    print(text)
    print()
    if not no_send:
        send(text)


if __name__ == "__main__":
    main()
