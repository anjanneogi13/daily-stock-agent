from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from src.opening_range_scanner import (
    calculate_opening_range,
    detect_opening_range_breakout,
    latest_post_range_bar,
    opening_range_bounds,
)


ET = ZoneInfo("America/New_York")


def bar(ts, high, low, close, volume=1000, open_=None):
    return {
        "ts": ts,
        "open": close if open_ is None else open_,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
    }


def ts(h, m):
    return datetime(2026, 5, 6, h, m, tzinfo=ET)


def sample_bars(post_close=101.4, post_volume=3000):
    return [
        bar(ts(9, 30), 100.4, 99.7, 100.1, volume=1000),
        bar(ts(9, 35), 100.8, 99.9, 100.6, volume=1200),
        bar(ts(9, 40), 101.0, 100.2, 100.9, volume=1100),
        bar(ts(9, 45), post_close + 0.1, post_close - 0.5, post_close, volume=post_volume),
    ]


def test_opening_range_bounds_are_930_to_945_et():
    start, end = opening_range_bounds("2026-05-06", range_minutes=15)

    assert start.hour == 9
    assert start.minute == 30
    assert end.hour == 9
    assert end.minute == 45
    assert str(start.tzinfo) == "America/New_York"


def test_calculate_opening_range_from_first_15_minutes():
    result = calculate_opening_range(sample_bars(), session_date="2026-05-06")

    assert result["ready"] is True
    assert result["bar_count"] == 3
    assert result["high"] == 101.0
    assert result["low"] == 99.7
    assert result["volume"] == 3300
    assert result["blockers"] == []


def test_opening_range_rejects_incomplete_window():
    rows = [
        bar(ts(9, 30), 100.4, 99.7, 100.1),
        bar(ts(9, 45), 101.4, 100.9, 101.2),
    ]

    result = calculate_opening_range(rows, session_date="2026-05-06")

    assert result["ready"] is False
    assert any("opening_range_incomplete" in b for b in result["blockers"])


def test_latest_post_range_bar_uses_bar_after_range_end():
    latest = latest_post_range_bar(sample_bars(), session_date="2026-05-06")

    assert latest["ts"].hour == 9
    assert latest["ts"].minute == 45


def test_detects_watch_only_breakout_candidate():
    result = detect_opening_range_breakout(
        "NET",
        sample_bars(post_close=101.6, post_volume=3500),
        prev_close=100.0,
        session_date="2026-05-06",
    )

    assert result["candidate"] is True
    assert result["watch_only"] is True
    assert result["mode"] == "monitoring_only"
    assert result["entry"] == 101.6
    assert result["stop_loss"] == 99.7
    assert result["take_profit"] > result["entry"]
    assert "opening-range breakout" in result["reason"]


def test_blocks_when_price_has_not_broken_range_high():
    result = detect_opening_range_breakout(
        "NET",
        sample_bars(post_close=100.8, post_volume=3500),
        prev_close=100.0,
        session_date="2026-05-06",
    )

    assert result["candidate"] is False
    assert "price_not_above_opening_range_high" in result["blockers"]


def test_blocks_low_volume_breakout():
    result = detect_opening_range_breakout(
        "NET",
        sample_bars(post_close=101.6, post_volume=1000),
        prev_close=100.0,
        session_date="2026-05-06",
    )

    assert result["candidate"] is False
    assert any("volume_ratio" in b for b in result["blockers"])


def test_anti_chase_blocks_overextended_breakout():
    result = detect_opening_range_breakout(
        "NET",
        sample_bars(post_close=106.0, post_volume=5000),
        prev_close=100.0,
        session_date="2026-05-06",
        max_extension_pct=3.0,
    )

    assert result["candidate"] is False
    assert any("anti_chase_extension" in b for b in result["blockers"])


def test_blocks_large_gap_even_if_breaking_out():
    result = detect_opening_range_breakout(
        "NET",
        sample_bars(post_close=101.6, post_volume=3500),
        prev_close=90.0,
        session_date="2026-05-06",
        max_gap_pct=8.0,
    )

    assert result["candidate"] is False
    assert any("gap_pct" in b for b in result["blockers"])


def test_naive_timestamps_are_interpreted_as_et():
    rows = [
        bar(datetime(2026, 5, 6, 9, 30), 100.4, 99.7, 100.1),
        bar(datetime(2026, 5, 6, 9, 35), 100.8, 99.9, 100.6),
        bar(datetime(2026, 5, 6, 9, 40), 101.0, 100.2, 100.9),
        bar(datetime(2026, 5, 6, 9, 45), 101.8, 101.0, 101.6, volume=3500),
    ]

    result = detect_opening_range_breakout("NET", rows, session_date="2026-05-06")

    assert result["candidate"] is True
