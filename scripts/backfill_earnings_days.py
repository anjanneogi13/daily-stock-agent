"""Backfill missing days_to_earnings in data/picks_log.csv.

Bug #11 (2026-05-05):
  Earnings proximity is a core risk/smell input. Historical rows can have blank
  days_to_earnings when the live provider later has enough data.

Usage:
    python scripts/backfill_earnings_days.py
    python scripts/backfill_earnings_days.py --apply

Dry-run by default. Writes atomically when --apply is provided.
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
import tempfile
from pathlib import Path

# Make src/ importable when running from repo root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.earnings import UNKNOWN_EARNINGS_DAYS, days_to_earnings  # noqa: E402


PICKS_LOG = Path("data/picks_log.csv")
DATA_QUALITY_FLOOR = "2026-05-02"


def _has_days_to_earnings(row: dict) -> bool:
    value = row.get("days_to_earnings")
    if value in (None, "", "None"):
        return False
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False


def backfill(path: Path = PICKS_LOG, floor: str = DATA_QUALITY_FLOOR, apply: bool = False) -> int:
    if not path.exists():
        print(f"[backfill_earnings_days] {path} not found — nothing to do.")
        return 0

    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    if "days_to_earnings" not in fieldnames:
        fieldnames.append("days_to_earnings")
    for row in rows:
        row.setdefault("days_to_earnings", "")

    candidates = [
        row for row in rows
        if (row.get("pick_date") or "") >= floor
        and not _has_days_to_earnings(row)
        and (row.get("ticker") or "").strip()
        and (row.get("pick_date") or "").strip()
    ]

    print(
        f"[backfill_earnings_days] {len(candidates)} candidate(s) "
        f"for floor >= {floor} (out of {len(rows)} total rows)"
    )

    changed = 0
    for row in candidates:
        ticker = (row.get("ticker") or "").strip()
        pick_date = (row.get("pick_date") or "").strip()

        d2e = days_to_earnings(ticker, as_of=pick_date)
        if d2e == UNKNOWN_EARNINGS_DAYS:
            print(f"  ⚠ {ticker:6} {pick_date}: earnings unknown — skip")
            continue

        row["days_to_earnings"] = str(int(d2e))
        changed += 1
        print(f"  ✓ {ticker:6} {pick_date}: days_to_earnings={row['days_to_earnings']}")

    if not apply:
        print(
            f"\n[backfill_earnings_days] DRY RUN — would update {changed} row(s). "
            "Re-run with --apply to write."
        )
        return changed

    if not changed:
        print("[backfill_earnings_days] Nothing changed. Exit.")
        return 0

    tmp_fd, tmp_path = tempfile.mkstemp(
        prefix="picks_log.", suffix=".tmp", dir=str(path.parent)
    )
    try:
        with os.fdopen(tmp_fd, "w", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=fieldnames,
                extrasaction="ignore",
                lineterminator="\n",
            )
            writer.writeheader()
            writer.writerows(rows)
        os.replace(tmp_path, path)
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise

    print(f"\n[backfill_earnings_days] ✅ APPLIED — updated {changed} row(s) in {path}")
    return changed


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Write changes to data/picks_log.csv")
    parser.add_argument("--floor", default=DATA_QUALITY_FLOOR, help="Minimum pick_date to include")
    args = parser.parse_args(argv)

    backfill(apply=args.apply, floor=args.floor)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
