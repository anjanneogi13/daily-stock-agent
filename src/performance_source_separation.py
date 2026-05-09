"""Performance source separation helpers.

Official performance reporting must not blend watch-only/research-only evidence
with closed official/legacy monitored picks.
"""

from __future__ import annotations

WATCH_ONLY_TRUE_VALUES = {"1", "true", "yes", "y", "watch", "watch_only"}


PERFORMANCE_SOURCE_NOTE = (
    "Source: closed non-watch-only rows from data/picks_log.csv. "
    "Excludes watch-only late ideas, opening-range observations, research-only outcomes, "
    "and paper-like simulations."
)

LAYMAN_PERFORMANCE_SOURCE_NOTE = (
    "_Source: closed non-watch-only rows from data/picks_log.csv._\n"
    "_Excludes watch-only late ideas, opening-range observations, research-only outcomes, "
    "and paper-like simulations._"
)


def is_watch_only_row(row: dict) -> bool:
    """Return True if a picks_log-style row is explicitly watch-only."""
    value = row.get("watch_only")
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in WATCH_ONLY_TRUE_VALUES


def filter_official_performance_rows(rows: list[dict]) -> list[dict]:
    """Return rows eligible for official/legacy performance stats."""
    return [row for row in rows if not is_watch_only_row(row)]


def count_watch_only_rows(rows: list[dict]) -> int:
    return sum(1 for row in rows if is_watch_only_row(row))
