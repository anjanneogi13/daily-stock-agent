"""Tests for Pillar 4 prep — auto_pause observe-mode."""
import sys
from pathlib import Path
from datetime import datetime, timedelta
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.auto_pause import (
    consecutive_losses, rolling_r, rolling_win_rate,
    compute_score, classify, format_summary,
)


def _row(status, r_mult, days_ago=0):
    d = datetime.now() - timedelta(days=days_ago)
    return {
        "evaluation_status": status,
        "r_multiple": str(r_mult),
        "evaluated_on": d.strftime("%Y-%m-%d"),
        "_evaluated_dt": d,
    }


def test_consecutive_losses_zero():
    assert consecutive_losses([]) == 0


def test_consecutive_losses_streak():
    rows = [_row("tp_hit", 1.5, 10), _row("sl_hit", -1, 5),
            _row("sl_hit", -1, 3), _row("sl_hit", -1, 1)]
    assert consecutive_losses(rows) == 3


def test_consecutive_loss_broken_by_win():
    rows = [_row("sl_hit", -1, 5), _row("sl_hit", -1, 3), _row("tp_hit", 1.5, 1)]
    assert consecutive_losses(rows) == 0


def test_rolling_r_sums_window():
    rows = [_row("tp_hit", 1.5, 5),
            _row("sl_hit", -1.0, 3),
            _row("sl_hit", -1.0, 100)]  # outside window
    assert rolling_r(rows, days=14) == 0.5


def test_rolling_win_rate():
    rows = [_row("tp_hit", 1.5, 5), _row("sl_hit", -1, 3)]
    assert rolling_win_rate(rows, days=14) == 0.5


def test_classify_thresholds():
    assert "GREEN" in classify(0)
    assert "ELEVATED" in classify(4)
    assert "AMBER" in classify(6)
    assert "RED" in classify(9)


def test_compute_score_clean():
    """1 win, no streak — should be GREEN."""
    rows = [_row("tp_hit", 1.5, 5)]
    r = compute_score(rows)
    assert r["score"] <= 2
    assert "GREEN" in r["level"]
    assert r["would_pause"] is False


def test_compute_score_crisis_red():
    """Build a real crisis: 6 consecutive losses, big drawdown."""
    rows = [_row("sl_hit", -1.5, days) for days in [12, 10, 8, 6, 4, 2]]
    r = compute_score(rows)
    assert r["score"] >= 7  # streak(4) + dd(4) capped at 10
    assert r["would_pause"] is True


def test_format_summary_shows_reasons():
    rows = [_row("sl_hit", -1, days) for days in [6, 4, 2]]
    r = compute_score(rows)
    text = format_summary(r)
    assert "PAUSE SIGNAL" in text
    assert any("loss" in line.lower() for line in text.split("\n"))


def test_observe_mode_never_enforces():
    """v0.1 must always have enforced=False."""
    rows = [_row("sl_hit", -2, days) for days in range(1, 8)]
    r = compute_score(rows)
    assert r["enforced"] is False
