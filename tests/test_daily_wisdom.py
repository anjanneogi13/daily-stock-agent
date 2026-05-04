"""E5-C: daily wisdom hint must respect quality floor + small-n honesty."""
import csv
from pathlib import Path
from src.daily_wisdom import (
    generate_daily_wisdom, _confidence_label, _row_to_journal_format,
    N_ANECDOTAL, N_DIRECTIONAL, N_CONFIDENT,
)


def test_confidence_labels():
    assert "ANECDOTAL" in _confidence_label(5)
    assert "ANECDOTAL" in _confidence_label(N_ANECDOTAL - 1)
    assert "DIRECTIONAL" in _confidence_label(N_ANECDOTAL)
    assert "DIRECTIONAL" in _confidence_label(N_DIRECTIONAL - 1)
    assert "USEFUL" in _confidence_label(N_DIRECTIONAL)
    assert "CONFIDENT" in _confidence_label(N_CONFIDENT)
    assert "CONFIDENT" in _confidence_label(500)


def test_row_to_journal_format_win():
    row = {"ticker": "AAPL", "r_multiple": "1.66", "score": "0.80",
           "regime": "bull", "trade_type": "day", "tag": "MEGA / FAANG"}
    j = _row_to_journal_format(row)
    assert j["outcome"] == "win"
    assert j["r_multiple"] == 1.66
    assert j["signals"]["regime"] == "bull"
    assert j["signals"]["score_bucket"] == "very_high"
    assert j["signals"]["tag"] == "MEGA"


def test_row_to_journal_format_loss():
    row = {"ticker": "X", "r_multiple": "-1.0", "score": "0.65",
           "regime": "bear", "trade_type": "swing", "tag": ""}
    j = _row_to_journal_format(row)
    assert j["outcome"] == "loss"
    assert j["signals"]["score_bucket"] == "low"


def test_row_to_journal_skips_unrecorded():
    """Pending picks (no r_multiple) must be skipped, not crash."""
    assert _row_to_journal_format({"ticker": "X", "r_multiple": ""}) is None
    assert _row_to_journal_format({"ticker": "X"}) is None
    assert _row_to_journal_format({"ticker": "X", "r_multiple": "garbage"}) is None


def test_generate_wisdom_runs_without_crash():
    """Smoke test on real picks_log — must produce SOME report."""
    out = generate_daily_wisdom()
    assert isinstance(out, str)
    assert "DAILY WISDOM" in out
    assert "Floor:" in out


def test_wisdom_contains_sample_warning_when_small():
    """If post-floor n < N_ANECDOTAL, output must say so."""
    out = generate_daily_wisdom()
    # Today: post-floor n = 0 or very small. Must show ANECDOTAL or "No closed".
    assert ("ANECDOTAL" in out) or ("No closed picks" in out) or ("Sample" in out)


def test_wisdom_uses_quality_floor():
    """Output must reference the floor date."""
    from src.data_quality import DATA_QUALITY_FLOOR
    out = generate_daily_wisdom()
    assert DATA_QUALITY_FLOOR.isoformat() in out
