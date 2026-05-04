"""Data quality floor — fence off pre-gate picks from analysis.

Background (May 4 2026):
  • Apr 28 - May 1 picks: pre-sector-cap, pre-hard-blocks, pre-calibration era
  • These picks include known structural failures (16-SEMI concentration,
    SLNH @ $1.66 penny stock) caused by missing safety gates that have
    SINCE been added.
  • Including them in win-rate / hypothesis analysis pollutes the signal
    with bugs that can no longer occur.

DATA_QUALITY_FLOOR = the earliest pick_date for which all current safety
gates were active. Analysis MUST filter to pick_date >= floor or risk
drawing false conclusions from fossil losses.
"""
from datetime import date

# Floor anchors (each gate's go-live date):
#   c756dde — apply_sector_cap + apply_tag_cap         2026-04-30
#   9d85915 — apply_hard_blocks (penny + SL buffer)    2026-05-02
#   39c8f05 — BUG-5 tiered SL minimums                 2026-05-02
#   E1-E4 series — calibration + smell + regime sizing 2026-05-04
DATA_QUALITY_FLOOR = date(2026, 5, 2)


def is_above_floor(pick_date_str: str) -> bool:
    """Return True if pick_date is on/after DATA_QUALITY_FLOOR.

    Defaults to False on parse error (conservative: exclude unknown dates
    rather than risk polluting analysis with them).
    """
    if not pick_date_str:
        return False
    try:
        return date.fromisoformat(pick_date_str) >= DATA_QUALITY_FLOOR
    except (ValueError, TypeError):
        return False


def filter_to_quality(rows, date_field="pick_date"):
    """Filter out rows below the data quality floor."""
    return [r for r in rows if is_above_floor(r.get(date_field, ""))]
