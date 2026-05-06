#!/usr/bin/env python3
"""Send late watch-only daily ideas to Telegram.

Monitoring-only. Does not create picks or trades.
"""
from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo


ET = ZoneInfo("America/New_York")


def today_et() -> str:
    return datetime.now(timezone.utc).astimezone(ET).strftime("%Y-%m-%d")


def main() -> int:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_ids = [
        c for c in [
            os.environ.get("TELEGRAM_CHAT_ID"),
            os.environ.get("TELEGRAM_GROUP_CHAT_ID"),
        ]
        if c
    ]

    path = Path("data") / f"late_daily_ideas_{today_et()}.md"
    if not path.exists():
        print(f"[late-ideas-telegram] No message file at {path}; nothing to send.")
        return 0

    msg = path.read_text(encoding="utf-8").strip()
    if not msg:
        print("[late-ideas-telegram] Empty message; nothing to send.")
        return 0

    if not token or not chat_ids:
        print("[late-ideas-telegram] Missing Telegram credentials; skipping send.")
        return 0

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    sent = 0
    for chat_id in chat_ids:
        data = urllib.parse.urlencode({
            "chat_id": chat_id,
            "text": msg,
            "disable_web_page_preview": "true",
        }).encode()
        try:
            resp = urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=10)
            result = json.loads(resp.read())
            if result.get("ok"):
                print(f"[late-ideas-telegram→{chat_id}] ✅ Sent")
                sent += 1
            else:
                print(f"[late-ideas-telegram→{chat_id}] ❌ {result}")
        except Exception as exc:
            print(f"[late-ideas-telegram→{chat_id}] ❌ {exc}")

    if sent == 0:
        print("[late-ideas-telegram] No Telegram sends confirmed.")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
