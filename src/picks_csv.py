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
    """Update specific fields for a pick. Returns True if row was found and updated."""
    if not LOG_PATH.exists():
        return False
    rows = []
    found = False
    with LOG_PATH.open() as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            if row.get("pick_date") == pick_date and row.get("ticker") == ticker:
                for k, v in updates.items():
                    if k in fieldnames:
                        row[k] = str(v)
                found = True
            rows.append(row)
    if found:
        with LOG_PATH.open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            w.writeheader()
            w.writerows(rows)
    return found
