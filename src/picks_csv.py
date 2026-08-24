"""Helpers for reading/updating mutable fields in picks_log.csv.

Used by intraday_monitor to update peak_price, current_sl, trail_active,
and tier_status as positions move through the day.
"""
import csv
from pathlib import Path
from typing import Dict, List

LOG_PATH = Path("data/picks_log.csv")


def read_open_picks(today: str) -> List[Dict]:
    """Return all rows for `today` that are still pending/open."""
    if not LOG_PATH.exists():
        return []
    out = []
    with LOG_PATH.open() as f:
        for row in csv.DictReader(f):
            if row.get("pick_date") == today and row.get("evaluation_status", "pending") == "pending":
                out.append(row)
    return out


def update_pick_row(pick_date: str, ticker: str, updates: Dict) -> bool:
    """Update specific fields for a pick. Returns True if row was found and updated.

    Write-once terminal guard (§7): once a row has reached a terminal
    evaluation_status (tp_hit/sl_hit/day_close/expired/unreachable_entry) its
    outcome is immutable — attempts to change evaluation_status again are
    dropped, so a position can never be re-closed or double-counted.
    """
    if not LOG_PATH.exists():
        return False
    from src.trade_state import TERMINAL_STATUSES
    rows = []
    found = False
    with LOG_PATH.open() as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            if row.get("pick_date") == pick_date and row.get("ticker") == ticker:
                existing = (row.get("evaluation_status") or "").strip().lower()
                if existing in TERMINAL_STATUSES and "evaluation_status" in updates:
                    print(f"[picks_csv] {ticker} {pick_date} already terminal "
                          f"({existing}) — refusing re-close (write-once)")
                    return False
                for k, v in updates.items():
                    if k in fieldnames:
                        row[k] = str(v)
                found = True
            rows.append(row)
    if found:
        # P1 (COFOUNDER_AUDIT_2026-06-24 #3 / audit PV-X2): write atomically.
        # Previously this opened LOG_PATH in "w" (truncate) and rewrote in
        # place, so a kill mid-write left the durable pick history truncated
        # or empty. Mirror pick_evaluator._save_picks: write a sibling .tmp
        # then atomically rename onto the real path (atomic on POSIX). On any
        # exception the original picks_log.csv is left intact.
        tmp = LOG_PATH.with_suffix(LOG_PATH.suffix + ".tmp")
        try:
            with tmp.open("w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
                w.writeheader()
                w.writerows(rows)
            tmp.replace(LOG_PATH)
        finally:
            # Clean up a leftover tmp if the write failed before replace().
            if tmp.exists():
                try:
                    tmp.unlink()
                except OSError:
                    pass
    return found
