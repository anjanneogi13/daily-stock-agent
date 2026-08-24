#!/usr/bin/env python3
"""PAT-expiry pre-alert — Cluster G (scheduler robustness).

The external scheduler (cron-job.org) fires `workflow_dispatch` with a GitHub
PAT. When that PAT expires the dispatch silently stops (observed 2026-08-18:
"External scheduler appears DOWN … rotate the GitHub PAT if expired") and only
the after-the-fact missed-window alert fires.

This script alerts BEFORE expiry: if the scheduler PAT is available in the
environment (optional `SCHEDULER_PAT` secret), GitHub returns its expiry in
the `github-authentication-token-expiration` response header for fine-grained
PATs. If expiry is within the warning window, send one actionable Telegram
alert. Degrades gracefully (exit 0, informative log) when no PAT is
configured, the header is absent (classic PATs), or the network is down.

Usage:  python scripts/check_pat_expiry.py [--warn-days N]
"""
from __future__ import annotations

import argparse
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone

WARN_DAYS_DEFAULT = 7
EXPIRY_HEADER = "github-authentication-token-expiration"

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHATS = [c for c in (os.environ.get("TELEGRAM_CHAT_ID"),
                     os.environ.get("TELEGRAM_GROUP_CHAT_ID")) if c]


def fetch_expiry(pat: str) -> datetime | None:
    """Return the PAT's expiry datetime, or None if not exposed/unreachable."""
    req = urllib.request.Request(
        "https://api.github.com/rate_limit",
        headers={"Authorization": "Bearer " + pat,
                 "User-Agent": "daily-stock-agent-pat-check"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.headers.get(EXPIRY_HEADER)
    except Exception as e:
        print(f"[pat-check] could not reach GitHub API: {e}")
        return None
    return parse_expiry(raw)


def parse_expiry(raw: str | None) -> datetime | None:
    """Parse the expiration header (e.g. '2026-09-01 11:22:33 UTC')."""
    if not raw:
        return None
    raw = raw.strip()
    for fmt in ("%Y-%m-%d %H:%M:%S %Z", "%Y-%m-%d %H:%M:%S %z"):
        try:
            dt = datetime.strptime(raw, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(raw).replace(tzinfo=timezone.utc)
    except ValueError:
        print(f"[pat-check] unparseable expiry header: {raw!r}")
        return None


def build_alert(days_left: int, expiry: datetime) -> str:
    return (
        "🔑 *Scheduler PAT expiring soon*\n\n"
        f"The GitHub PAT used by the external scheduler expires in *{days_left} day(s)* "
        f"(`{expiry.strftime('%Y-%m-%d %H:%M UTC')}`).\n\n"
        "Rotate it now to avoid missed premarket runs:\n"
        "1. Generate a new fine-grained PAT (Actions: read/write on this repo).\n"
        "2. Update the cron-job.org request header with the new token.\n"
        "3. Update the optional `SCHEDULER_PAT` repo secret so this check keeps working.\n\n"
        "See docs/SCHEDULER_RELIABILITY.md for the full procedure."
    )


def send(text: str) -> None:
    if not TOKEN or not CHATS:
        print("[telegram] no creds — dry-run print only")
        print(text)
        return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    for chat in CHATS:
        payload = {"chat_id": chat, "text": text, "parse_mode": "Markdown"}
        try:
            data = urllib.parse.urlencode(payload).encode()
            with urllib.request.urlopen(url, data=data, timeout=20) as r:
                if r.status == 200:
                    print("[telegram] OK")
        except Exception as e:
            print(f"[telegram] send failed: {e}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--warn-days", type=int, default=WARN_DAYS_DEFAULT)
    args = ap.parse_args(argv)

    pat = os.environ.get("SCHEDULER_PAT")
    if not pat:
        print("[pat-check] SCHEDULER_PAT not configured — skipping (optional check)")
        return 0

    expiry = fetch_expiry(pat)
    if expiry is None:
        print("[pat-check] no expiry exposed (classic PAT or API issue) — nothing to do")
        return 0

    days_left = (expiry - datetime.now(timezone.utc)).days
    print(f"[pat-check] scheduler PAT expires {expiry.isoformat()} ({days_left} day(s) left)")
    if days_left <= args.warn_days:
        send(build_alert(days_left, expiry))
    return 0


if __name__ == "__main__":
    sys.exit(main())
