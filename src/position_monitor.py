"""Position lifecycle monitor — flags positions exceeding max_hold_days.

Reads data/picks_log.csv as single source of truth (no positions.json
to avoid sync bugs). Returns alert list for Telegram dispatch.

Usage:
    from src.position_monitor import scan_open_positions
    alerts = scan_open_positions()
    for a in alerts:
        print(a['message'])

MAX_HOLD per trade_type (calendar days):
    day:    1
    swing:  10
    multi:  30
    (default if unknown): 14
"""
import csv
from datetime import date, datetime
from pathlib import Path

PICKS_LOG = Path("data/picks_log.csv")

MAX_HOLD_DAYS = {
    "day": 1,
    "swing": 10,
    "multi": 30,
}
DEFAULT_MAX_HOLD = 14


def _parse_date(s: str) -> date | None:
    if not s:
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        return None


def _max_hold_for(trade_type: str) -> int:
    return MAX_HOLD_DAYS.get((trade_type or "").lower(), DEFAULT_MAX_HOLD)


def scan_open_positions(today: date | None = None) -> list[dict]:
    """Return alert dicts for positions exceeding max_hold.

    Alert dict shape:
        {
            'ticker': 'NVDA',
            'pick_date': '2026-04-22',
            'days_open': 11,
            'max_hold': 10,
            'trade_type': 'swing',
            'entry': 105.50,
            'severity': 'over' | 'near',  # near = within 1 day of max
            'message': 'Telegram-ready string'
        }
    """
    if today is None:
        today = date.today()
    if not PICKS_LOG.exists():
        return []

    with PICKS_LOG.open() as f:
        rows = list(csv.DictReader(f))

    alerts = []
    for r in rows:
        if r.get("evaluation_status") != "pending":
            continue
        pick_d = _parse_date(r.get("pick_date", ""))
        if pick_d is None:
            continue
        days_open = (today - pick_d).days
        max_hold = _max_hold_for(r.get("trade_type", ""))

        if days_open >= max_hold:
            severity = "over"
        elif days_open == max_hold - 1:
            severity = "near"
        else:
            continue  # within budget

        try:
            entry = float(r.get("entry", 0))
        except Exception:
            entry = 0.0

        ticker = r.get("ticker", "?")
        emoji = "🚨" if severity == "over" else "⏰"
        verb = "EXCEEDED" if severity == "over" else "near"
        msg = (
            f"{emoji} <b>{ticker}</b> {r.get('trade_type','?')} "
            f"open {days_open}d (max {max_hold}d {verb}) | "
            f"entry ${entry:.2f}"
        )

        alerts.append({
            "ticker": ticker,
            "pick_date": r.get("pick_date", ""),
            "days_open": days_open,
            "max_hold": max_hold,
            "trade_type": r.get("trade_type", ""),
            "entry": entry,
            "severity": severity,
            "message": msg,
        })

    # Sort: most overdue first
    alerts.sort(key=lambda a: a["days_open"] - a["max_hold"], reverse=True)
    return alerts


def format_telegram_summary(alerts: list[dict]) -> str:
    """Build a single Telegram message for all alerts."""
    if not alerts:
        return ""
    over = [a for a in alerts if a["severity"] == "over"]
    near = [a for a in alerts if a["severity"] == "near"]
    parts = ["⏰ <b>POSITION MONITOR</b>"]
    if over:
        parts.append(f"\n🚨 <b>{len(over)} OVERDUE</b>")
        for a in over:
            parts.append(f"  • {a['message']}")
    if near:
        parts.append(f"\n⚠️ <b>{len(near)} APPROACHING MAX-HOLD</b>")
        for a in near:
            parts.append(f"  • {a['message']}")
    return "\n".join(parts)
