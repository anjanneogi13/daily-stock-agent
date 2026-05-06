#!/usr/bin/env python3
"""Send Telegram alert when official premarket picks miss the cutoff.

This is intentionally separate from send_layman_daily.py so late scheduled or
manual daily-picks runs cannot accidentally send normal actionable picks.
"""
from __future__ import annotations

import os
import urllib.parse
import urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo


TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHATS = [
    c for c in (
        os.environ.get("TELEGRAM_CHAT_ID"),
        os.environ.get("TELEGRAM_GROUP_CHAT_ID"),
    )
    if c
]


def build_message(now: datetime | None = None) -> str:
    now = now or datetime.now(ZoneInfo("America/New_York"))
    stamp = now.strftime("%Y-%m-%d %H:%M ET")
    return (
        "⚠️ *Premarket window missed*\n\n"
        f"Time: `{stamp}`\n\n"
        "Official daily picks were *not sent* because the 09:20 ET cutoff "
        "has passed.\n\n"
        "No normal premarket buy entries are actionable from this run. "
        "Use only intraday monitor alerts after market open.\n\n"
        "_Educational only. Not financial advice._"
    )


def send(text: str) -> bool:
    if not TOKEN or not CHATS:
        print("[telegram] no creds — dry-run print only")
        print(text)
        return True

    sent_any = False
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    for chat in CHATS:
        for parse_mode in ("Markdown", None):
            payload = {"chat_id": chat, "text": text}
            if parse_mode:
                payload["parse_mode"] = parse_mode
            data = urllib.parse.urlencode(payload).encode()
            try:
                with urllib.request.urlopen(url, data=data, timeout=20) as r:
                    if r.status == 200:
                        print(f"[telegram] missed-window chat={chat[:6]}… OK")
                        sent_any = True
                        break
                    print(f"[telegram] missed-window chat={chat[:6]}… HTTP {r.status}")
            except Exception as e:
                print(f"[telegram] missed-window chat={chat[:6]}… failed: {e}")
    return sent_any


def main() -> int:
    return 0 if send(build_message()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
