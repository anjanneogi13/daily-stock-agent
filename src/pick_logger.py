"""Logs every generated pick to a CSV for later evaluation.

Phase 2B.1: added scale-out tier columns (tp1, tp2, qty_t1/t2/t3, tier_status).
Header migration: detects old schema and rewrites with new header (old rows get blanks).
"""
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
    "evaluation_status",
    "evaluated_on", "exit_price", "actual_return_pct", "r_multiple",
    # Phase 2B.1 scale-out fields:
    "tp1", "tp2", "qty_t1", "qty_t2", "qty_t3", "tier_status",
    # Phase 2B.2 trailing-stop fields:
    "original_sl", "current_sl", "peak_price", "trail_active",
    # Phase 2B.3 adaptive-TP fields:
    "current_tp", "tp_raises",
    # Phase 2B.5: adaptive SL tighten audit
    "peak_rsi", "sl_tightens",
    # Monster Hunt Mode (May 3 2026)
    "monster_score", "is_monster",
    # Sector benchmark (May 3 2026 T3) — sector-relative alpha
    "sector_etf", "sector_close", "sector_close_at_exit",
    "sector_return_pct", "sector_alpha_pct",
]


def _migrate_header_if_needed():
    """If existing CSV has old header, rewrite the file with new header.
    Old rows get empty values for new columns (CSV-safe)."""
    if not LOG_PATH.exists() or LOG_PATH.stat().st_size == 0:
        return
    with LOG_PATH.open() as f:
        reader = csv.reader(f)
        try:
            existing_header = next(reader)
        except StopIteration:
            return
        if existing_header == FIELDS:
            return  # already migrated
        # Read all existing rows as dicts using OLD header
        f.seek(0)
        old_rows = list(csv.DictReader(f))

    # Rewrite with NEW header (extrasaction='ignore' guards future drift)
    with LOG_PATH.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        for row in old_rows:
            # Fill new fields with empty strings for old rows
            for new_field in FIELDS:
                if new_field not in row:
                    row[new_field] = ""
            w.writerow(row)
    print(f"[pick_logger] migrated CSV header: +{len(FIELDS) - len(existing_header)} new columns")


def _ensure_header():
    if not LOG_PATH.exists() or LOG_PATH.stat().st_size == 0:
        with LOG_PATH.open("w", newline="") as f:
            csv.DictWriter(f, fieldnames=FIELDS).writeheader()
    else:
        _migrate_header_if_needed()


def log_picks(picks: List[Dict], regime: Dict, cape: Dict = None) -> int:
    """Append today's picks to the log. Returns count saved."""
    _ensure_header()
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    timestr = now.strftime("%H:%M:%S")

    existing_today = set()
    if LOG_PATH.exists():
        with LOG_PATH.open() as f:
            for row in csv.DictReader(f):
                if row["pick_date"] == today:
                    existing_today.add(row["ticker"])

    saved = 0
    with LOG_PATH.open("a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
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
                "spy_close": (regime or {}).get("spy_close", ""),
                "cape": (cape or {}).get("cape", ""),
                "evaluation_status": "pending",
                "evaluated_on": "",
                "exit_price": "",
                "actual_return_pct": "",
                "r_multiple": "",
                # Phase 2B.1 scale-out fields:
                "tp1": p.get("tp1", ""),
                "tp2": p.get("tp2", ""),
                "qty_t1": p.get("qty_t1", ""),
                "qty_t2": p.get("qty_t2", ""),
                "qty_t3": p.get("qty_t3", ""),
                "tier_status": "none",  # none | tp1_hit | tp2_hit | trailing | closed
                # Phase 2B.2: trailing-stop state (mutable, updated by intraday monitor)
                "original_sl": p.get("stop_loss"),
                "current_sl": p.get("stop_loss"),
                "peak_price": p.get("entry"),
                "trail_active": "false",
                # Phase 2B.3: adaptive TP state
                "current_tp": p.get("take_profit"),
                "tp_raises": "[]",  # JSON audit trail
                "peak_rsi": "",  # Phase 2B.5: highest RSI seen
                "sl_tightens": "[]",  # Phase 2B.5: tighten audit
                # Monster Hunt Mode
                "monster_score": p.get("monster_score", ""),
                "is_monster": "true" if p.get("is_monster") else "false",
                # Sector benchmark (T3 May 3 2026)
                "sector_etf": p.get("sector_etf", ""),
                "sector_close": p.get("sector_close", ""),
                "sector_close_at_exit": "",
                "sector_return_pct": "",
                "sector_alpha_pct": "",
            })
            saved += 1
    skipped_dupes = len(picks) - saved
    if skipped_dupes > 0:
        print(f"[pick_logger] {saved} new, {skipped_dupes} skipped (already logged today)")
    return saved
