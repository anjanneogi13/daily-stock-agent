"""T50 — Sunday weekly Self-Improvement Report → Telegram (plain English).

For amateur users. No jargon. Reads what the brain learned this week
and explains it the way a friend would over coffee.
"""
import os
import sys
import urllib.request
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.meta_brain import build_self_improvement_digest, format_telegram_digest


def _send(token, chat_id, text):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text":    text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": "true",
    }).encode()
    try:
        with urllib.request.urlopen(url, data=data, timeout=20) as r:
            return r.status == 200
    except Exception as e:
        print(f"[telegram] markdown failed ({e}) — retrying plain text")
        # Fallback: plain text
        plain = text.replace("*","").replace("_","")
        data = urllib.parse.urlencode({"chat_id": chat_id, "text": plain}).encode()
        try:
            with urllib.request.urlopen(url, data=data, timeout=20) as r:
                return r.status == 200
        except Exception as e2:
            print(f"[telegram] plain text also failed: {e2}")
            return False


def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chats = [c for c in [os.environ.get("TELEGRAM_CHAT_ID"),
                          os.environ.get("TELEGRAM_GROUP_CHAT_ID")] if c]
    if not token or not chats:
        print("[meta-brain] No Telegram creds — printing only")
        digest = build_self_improvement_digest()
        print(format_telegram_digest(digest))
        return 0

    digest = build_self_improvement_digest()
    text = format_telegram_digest(digest)
    print(text)
    print("")
    for chat in chats:
        ok = _send(token, chat, text)
        print(f"[telegram] chat={chat[:6]}… → {'OK' if ok else 'FAIL'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
