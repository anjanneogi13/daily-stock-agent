"""Schema contract for data/picks_log.csv vs src.pick_logger.FIELDS.

Bug #15 (2026-05-05):
  Bug #9 backfilled spy_close_at_exit / spy_return_pct / alpha_pct into
  data/picks_log.csv, but pick_logger.FIELDS did not include those columns.

Danger:
  pick_logger._migrate_header_if_needed() rewrites the CSV using FIELDS.
  If FIELDS is missing live CSV columns, future daily runs can silently
  drop valuable historical learning columns.

Contract:
  - FIELDS must contain every existing live CSV header column.
  - FIELDS must contain every SPY alpha field written by pick_evaluator.
  - FIELDS must contain every sector alpha field written by pick_evaluator.
"""
import csv
from pathlib import Path

from src.pick_logger import FIELDS


CSV_PATH = Path("data/picks_log.csv")

SPY_ALPHA_FIELDS = {
    "spy_close_at_exit",
    "spy_return_pct",
    "alpha_pct",
}

SECTOR_ALPHA_FIELDS = {
    "sector_etf",
    "sector_close",
    "sector_close_at_exit",
    "sector_return_pct",
    "sector_alpha_pct",
}


def test_pick_logger_fields_preserve_existing_csv_header_columns():
    """No existing picks_log.csv column may be missing from pick_logger.FIELDS."""
    with CSV_PATH.open() as f:
        header = next(csv.reader(f))

    missing = [c for c in header if c not in FIELDS]
    assert missing == [], (
        "pick_logger.FIELDS is missing live CSV columns. "
        "A future header migration would drop these columns: "
        f"{missing}"
    )


def test_pick_logger_fields_include_spy_alpha_contract():
    """SPY alpha fields are written by pick_evaluator and must be durable."""
    missing = sorted(SPY_ALPHA_FIELDS - set(FIELDS))
    assert missing == [], f"Missing SPY alpha fields from pick_logger.FIELDS: {missing}"


def test_pick_logger_fields_include_sector_alpha_contract():
    """Sector alpha fields are written by pick_evaluator and must be durable."""
    missing = sorted(SECTOR_ALPHA_FIELDS - set(FIELDS))
    assert missing == [], f"Missing sector alpha fields from pick_logger.FIELDS: {missing}"
