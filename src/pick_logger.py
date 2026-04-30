"""Logs every generated pick to a CSV for later evaluation."""
import csv
from datetime import datetime
from pathlib import Path
from typing import List, Dict

LOG_PATH = Path("data/picks_log.csv")
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

FIELDS = [
    "pick_date", "pick_time", "ticker", "company", "tag", "trade_type",
    "score", "multiplier", "entry", "stop_loss", "take_profit",
    "risk_reward", "qty", "days_to_earnings",
    "regime", "spy_close", "cape",
    "evaluation_status",   # "pending" | "tp_hit" | "sl_hit" | "expired" | "open"
    "evaluated_on", "exit_price", "actual_return_pct", "r_multiple",
]


def _ensure_header():
    if not LOG_PATH.exists() or LOG_PATH.stat().st_size == 0:
        with LOG_PATH.open("w", newline="") as f:
            csv.DictWriter(f, fieldnames=FIELDS).writeheader()


def log_picks(picks: List[Dict], regime: Dict, cape: Dict = None) -> int:
    """Append today's picks to the log. Returns count saved."""
    _ensure_header()
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    timestr = now.strftime("%H:%M:%S")

    # Don't double-log if we already saved picks for today
    existing_today = set()
    if LOG_PATH.exists():
        with LOG_PATH.open() as f:
            for row in csv.DictReader(f):
                if row["pick_date"] == today:
                    existing_today.add(row["ticker"])

    saved = 0
    with LOG_PATH.open("a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        for p in picks:
            if p["ticker"] in existing_today:
                continue
            w.writerow({
                "pick_date": today,
                "pick_time": timestr,
                "ticker": p.get("ticker"),
                "company": p.get("company", ""),
                "tag": p.get("tag", ""),
                "trade_type": p.get("trade_type", "swing"),
                "score": round(p.get("score", 0), 3),
                "multiplier": p.get("multiplier", 1.0),
                "entry": p.get("entry"),
                "stop_loss": p.get("stop_loss"),
                "take_profit": p.get("take_profit"),
                "risk_reward": p.get("risk_reward", 2.0),
                "qty": p.get("qty", 0),
                "days_to_earnings": p.get("days_to_earnings", ""),
                "regime": (regime or {}).get("regime") or "unknown",
                "spy_close": regime.get("spy_close", ""),
                "cape": (cape or {}).get("cape", ""),
                "evaluation_status": "pending",
                "evaluated_on": "",
                "exit_price": "",
                "actual_return_pct": "",
                "r_multiple": "",
            })
            saved += 1
    skipped_dupes = len(picks) - saved
    if skipped_dupes > 0:
        print(f"[pick_logger] {saved} new, {skipped_dupes} skipped (already logged today)")
    return saved
