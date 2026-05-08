#!/usr/bin/env python3
"""Send late watch-only daily ideas to Telegram.

Monitoring-only. Does not create picks or trades.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo


ET = ZoneInfo("America/New_York")
DATA_DIR = Path("data")


def today_et() -> str:
    return datetime.now(timezone.utc).astimezone(ET).strftime("%Y-%m-%d")


def late_ideas_message_path(date_str: str, data_dir: Path = DATA_DIR) -> Path:
    return data_dir / f"late_daily_ideas_{date_str}.md"


def late_ideas_sent_path(date_str: str, data_dir: Path = DATA_DIR) -> Path:
    return data_dir / f"late_daily_ideas_sent_{date_str}.json"


def _message_checksum(msg: str) -> str:
    return hashlib.sha256(msg.encode("utf-8")).hexdigest()


def _load_sent_ledger(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _write_sent_ledger(path: Path, *, date_str: str, msg: str, sent_count: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "artifact": "late_daily_ideas_sent",
        "date": date_str,
        "sent_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "sent_count": int(sent_count),
        "message_sha256": _message_checksum(msg),
        "mode": "monitoring_only",
        "watch_only": True,
        "paper_trading_enabled": False,
        "live_trading_enabled": False,
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None, *, data_dir: Path = DATA_DIR) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force resend even if late watch-only ideas were already sent today.",
    )
    args = parser.parse_args(argv)

    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_ids = [
        c for c in [
            os.environ.get("TELEGRAM_CHAT_ID"),
            os.environ.get("TELEGRAM_GROUP_CHAT_ID"),
        ]
        if c
    ]

    date_str = today_et()
    path = late_ideas_message_path(date_str, data_dir=data_dir)
    sent_path = late_ideas_sent_path(date_str, data_dir=data_dir)
    if not path.exists():
        print(f"[late-ideas-telegram] No message file at {path}; nothing to send.")
        return 0

    msg = path.read_text(encoding="utf-8").strip()
    if not msg:
        print("[late-ideas-telegram] Empty message; nothing to send.")
        return 0

    sent_ledger = _load_sent_ledger(sent_path)
    if sent_ledger and not args.force:
        print(f"[late-ideas-telegram] Already sent for {date_str}; skipping duplicate send. Use --force to resend.")
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

    _write_sent_ledger(sent_path, date_str=date_str, msg=msg, sent_count=sent)
    print(f"[late-ideas-telegram] Recorded sent ledger at {sent_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
