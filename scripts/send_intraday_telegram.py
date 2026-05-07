#!/usr/bin/env python3
"""Send intraday alert to Telegram (dual-chat: personal + group)."""
import os, sys, json, urllib.parse, urllib.request
from pathlib import Path
from datetime import datetime, timezone

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_ROOT))

from intraday_scanner import append_opening_range_run_status


def _chat_ids() -> list[str]:
    return [c for c in [
        os.environ.get("TELEGRAM_CHAT_ID"),
        os.environ.get("TELEGRAM_GROUP_CHAT_ID"),
    ] if c]


def main() -> int:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_ids = _chat_ids()

    if not token or not chat_ids:
        append_opening_range_run_status(
            event="telegram_completed",
            result="skipped",
            reason="missing Telegram credentials",
            telegram_sent=False,
        )
        print("[telegram] Missing creds — skipping")
        return 0

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    alert_file = Path(f"data/intraday_alert_{today}.md")

    if not alert_file.exists():
        append_opening_range_run_status(
            event="telegram_completed",
            result="skipped",
            reason="no intraday alert file to send",
            telegram_sent=False,
        )
        print(f"[telegram] No alert file at {alert_file} — nothing to send. ✅")
        return 0

    msg = alert_file.read_text().strip()
    if not msg:
        append_opening_range_run_status(
            event="telegram_completed",
            result="skipped",
            reason="empty intraday alert message",
            telegram_sent=False,
        )
        print("[telegram] Empty alert — skipping")
        return 0

    if len(msg) > 4000:
        msg = msg[:3950] + "\n\n_(truncated)_"

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    sent_any = False

    for chat_id in chat_ids:
        data = urllib.parse.urlencode({
            "chat_id": chat_id,
            "text": msg,
            "parse_mode": "Markdown",
            "disable_web_page_preview": "true",
        }).encode()
        try:
            resp = urllib.request.urlopen(
                urllib.request.Request(url, data=data),
                timeout=10,
            )
            result = json.loads(resp.read())
            if result.get("ok"):
                sent_any = True
            print(f"[telegram→{chat_id}] {'✅ Sent' if result.get('ok') else '❌ '+str(result)}")
        except Exception as e:
            print(f"[telegram→{chat_id}] ❌ {e}")

    append_opening_range_run_status(
        event="telegram_completed",
        result="success" if sent_any else "failed",
        reason="intraday Telegram sender completed" if sent_any else "no Telegram sends confirmed",
        telegram_sent=sent_any,
    )

    # Delete the alert file so it doesn't get resent on next run if no new content.
    alert_file.unlink(missing_ok=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
