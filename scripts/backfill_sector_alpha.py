"""Backfill sector benchmark fields in data/picks_log.csv.

Bug #8/#10 (2026-05-05):
  Sector-relative learning depends on:
    - sector_etf and sector_close at pick time
    - sector_close_at_exit, sector_return_pct, sector_alpha_pct after close

Usage:
    python scripts/backfill_sector_alpha.py
    python scripts/backfill_sector_alpha.py --apply

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

from src.pick_evaluator import (  # noqa: E402
    _add_sector_alpha,
    _ensure_sector_benchmark_anchor,
)


PICKS_LOG = Path("data/picks_log.csv")
DATA_QUALITY_FLOOR = "2026-05-02"
CLOSED_STATUSES = {"tp_hit", "sl_hit", "expired", "day_close"}
SECTOR_FIELDS = [
    "sector_etf",
    "sector_close",
    "sector_close_at_exit",
    "sector_return_pct",
    "sector_alpha_pct",
]


def _has_value(value) -> bool:
    if value is None:
        return False
    text = str(value).strip()
    return bool(text) and text.lower() not in {"none", "nan", "null"}


def _is_closed(row: dict) -> bool:
    return (row.get("evaluation_status") or "").strip().lower() in CLOSED_STATUSES


def _changed(before: dict, after: dict) -> bool:
    return any(str(before.get(k, "")) != str(after.get(k, "")) for k in SECTOR_FIELDS)


def backfill(path: Path = PICKS_LOG, floor: str = DATA_QUALITY_FLOOR, apply: bool = False) -> int:
    if not path.exists():
        print(f"[backfill_sector_alpha] {path} not found — nothing to do.")
        return 0

    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    for field in SECTOR_FIELDS:
        if field not in fieldnames:
            fieldnames.append(field)
        for row in rows:
            row.setdefault(field, "")

    candidates = [
        row for row in rows
        if (row.get("pick_date") or "") >= floor
        and (
            not _has_value(row.get("sector_etf"))
            or not _has_value(row.get("sector_close"))
            or (
                _is_closed(row)
                and (
                    not _has_value(row.get("sector_close_at_exit"))
                    or not _has_value(row.get("sector_return_pct"))
                    or not _has_value(row.get("sector_alpha_pct"))
                )
            )
        )
    ]

    print(
        f"[backfill_sector_alpha] {len(candidates)} candidate(s) "
        f"for floor >= {floor} (out of {len(rows)} total rows)"
    )

    changed = 0
    for row in candidates:
        before = {k: row.get(k, "") for k in SECTOR_FIELDS}

        etf, pick_close = _ensure_sector_benchmark_anchor(row)

        if _is_closed(row) and row.get("evaluated_on") and row.get("actual_return_pct"):
            try:
                pick_return = float(row["actual_return_pct"])
            except (TypeError, ValueError):
                pick_return = None

            if pick_return is not None:
                exit_close = _add_sector_alpha(row, row["evaluated_on"], pick_return)
                if exit_close:
                    row["sector_close_at_exit"] = exit_close

        if _changed(before, row):
            changed += 1
            print(
                f"  ✓ {row.get('ticker','?'):6} {row.get('pick_date','?')} "
                f"status={row.get('evaluation_status','?')} "
                f"etf={row.get('sector_etf','')} "
                f"pick_close={row.get('sector_close','')} "
                f"exit_close={row.get('sector_close_at_exit','')} "
                f"sector_return={row.get('sector_return_pct','')} "
                f"sector_alpha={row.get('sector_alpha_pct','')}"
            )
        else:
            print(
                f"  ⚠ {row.get('ticker','?'):6} {row.get('pick_date','?')}: "
                f"no change (etf={etf!r}, pick_close={pick_close!r})"
            )

    if not apply:
        print(
            f"\n[backfill_sector_alpha] DRY RUN — would update {changed} row(s). "
            "Re-run with --apply to write."
        )
        return changed

    if not changed:
        print("[backfill_sector_alpha] Nothing changed. Exit.")
        return 0

    tmp_fd, tmp_path = tempfile.mkstemp(
        prefix="picks_log.", suffix=".tmp", dir=str(path.parent)
    )
    try:
        with os.fdopen(tmp_fd, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        os.replace(tmp_path, path)
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise

    print(f"\n[backfill_sector_alpha] ✅ APPLIED — updated {changed} row(s) in {path}")
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
