"""E5-B: data quality floor — exclude pre-gate fossil picks from analysis."""
from datetime import date
from src.data_quality import (
    DATA_QUALITY_FLOOR, is_above_floor, filter_to_quality
)


def test_floor_is_may_2_2026():
    """Floor is locked to May 2 2026 — bump only with documented reason."""
    assert DATA_QUALITY_FLOOR == date(2026, 5, 2)


def test_above_floor_after_may_2():
    assert is_above_floor("2026-05-02") is True
    assert is_above_floor("2026-05-04") is True
    assert is_above_floor("2030-01-01") is True


def test_below_floor_before_may_2():
    assert is_above_floor("2026-05-01") is False
    assert is_above_floor("2026-04-28") is False
    assert is_above_floor("2020-01-01") is False


def test_garbage_date_excluded_conservatively():
    """Conservative: unknown dates -> excluded, not included."""
    assert is_above_floor("") is False
    assert is_above_floor(None) is False
    assert is_above_floor("not-a-date") is False
    assert is_above_floor("2026-13-99") is False


def test_filter_to_quality_drops_fossils():
    rows = [
        {"pick_date": "2026-04-28", "ticker": "OLD"},
        {"pick_date": "2026-05-01", "ticker": "OLD2"},
        {"pick_date": "2026-05-02", "ticker": "NEW"},
        {"pick_date": "2026-05-04", "ticker": "NEW2"},
        {"pick_date": "",           "ticker": "BAD"},
    ]
    clean = filter_to_quality(rows)
    tickers = {r["ticker"] for r in clean}
    assert tickers == {"NEW", "NEW2"}


def test_filter_real_picks_log_excludes_fossils():
    """Lock the empirical fact: today's picks_log has fossils to exclude."""
    import csv, os
    if not os.path.exists("data/picks_log.csv"):
        return  # skip in CI without data
    rows = list(csv.DictReader(open("data/picks_log.csv")))
    if not rows:
        return
    clean = filter_to_quality(rows)
    # Some fossils should be filtered
    has_fossils = any(r.get("pick_date","") < "2026-05-02" for r in rows)
    if has_fossils:
        assert len(clean) < len(rows), "filter must drop fossil picks"
