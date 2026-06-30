#!/usr/bin/env python3
"""Daily heartbeat sender (vision item #29).

Posts a positive "I'm alive + what I logged today" message to Telegram so a
SILENT failure of the morning pipeline does not stay silent. `watchdog.yml`
only alarms on failure; this is the complementary liveness signal.

Channel resolution prefers HEARTBEAT_CHAT_ID, then falls back to the existing
TELEGRAM_CHAT_ID / TELEGRAM_GROUP_CHAT_ID chain -- so the heartbeat works
immediately (routes to the main channel) and self-separates onto its own
channel once HEARTBEAT_CHAT_ID is configured (groundwork for #4/#14).

Honesty: v1 reports liveness + today's pick-artifact/picks status derived from
DURABLE files on disk. It does NOT fabricate a full "everything I sent" recap --
per-report send ledgers are deleted post-send, so a complete sent-list is not
durably queryable. Reports only what is verifiable.

Safety: never creates picks, never bypasses any timing gate, never enables
trading. Missing creds / no data => prints a notice and exits 0 (a heartbeat
must never be the thing that breaks a workflow).
"""
from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


def _chat_ids() -> list[str]:
    """Heartbeat channel preferred; fall back to main, then group.

    Returns truthy chat ids in priority order. Empty list => no creds, caller
    skips gracefully.
    """
    return [c for c in [
        os.environ.get("HEARTBEAT_CHAT_ID"),
        os.environ.get("TELEGRAM_CHAT_ID"),
        os.environ.get("TELEGRAM_GROUP_CHAT_ID"),
    ] if c]


def _today_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _picks_rows_today(data_dir: Path, today: str) -> int:
    """Count rows in picks_log.csv whose date column is today. Never raises."""
    csv = data_dir / "picks_log.csv"
    if not csv.exists():
        return 0
    try:
        n = 0
        for line in csv.read_text().splitlines():
            if line.startswith(today + ",") or line.startswith(today + "\t"):
                n += 1
        return n
    except Exception:
        return 0


def _pick_artifact_today(data_dir: Path, today: str) -> str | None:
    """Return the filename of today's official pick / no-pick artifact if any."""
    try:
        for f in sorted(data_dir.glob("*.json")):
            name = f.name
            if today in name and ("official_pick" in name or "no_pick" in name
                                  or "premarket" in name):
                return name
    except Exception:
        pass
    return None


def _compose_message(data_dir: Path | str = Path("data")) -> str:
    """Build the heartbeat text from durable artifacts. Pure + side-effect free."""
    data_dir = Path(data_dir)
    today = _today_iso()
    rows = _picks_rows_today(data_dir, today)
    artifact = _pick_artifact_today(data_dir, today)

    if rows > 0:
        picks_line = f"Morning picks: {rows} row(s) logged \u2705"
    else:
        picks_line = "Morning picks: not yet logged today"

    artifact_line = (f"Last pick artifact: {artifact}" if artifact
                     else "Last pick artifact: none today")

    return (
        f"\u2705 daily-stock-agent alive \u2014 {today}\n"
        f"{picks_line}\n"
        f"{artifact_line}\n"
        f"(monitoring-only; no trading)"
    )


def _send(token: str, chat_ids: list[str], msg: str) -> bool:
    """Send msg to each chat via the Telegram Bot API (mirrors the intraday
    sender's urllib primitive). Returns True if any send confirmed ok."""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    if len(msg) > 4000:
        msg = msg[:3950] + "\n\n_(truncated)_"
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
                urllib.request.Request(url, data=data), timeout=10,
            )
            result = json.loads(resp.read())
            if result.get("ok"):
                sent_any = True
            print(f"[heartbeat\u2192{chat_id}] {'\u2705 Sent' if result.get('ok') else '\u274c '+str(result)}")
        except Exception as e:
            print(f"[heartbeat\u2192{chat_id}] \u274c {e}")
    return sent_any


def main() -> int:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_ids = _chat_ids()
    if not token or not chat_ids:
        print("[heartbeat] Missing Telegram creds \u2014 skipping (exit 0)")
        return 0
    msg = _compose_message()
    _send(token, chat_ids, msg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
