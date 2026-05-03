"""Tests for Pillar 5 weekly self-assessment."""
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.weekly_review import (
    grade, what_worked, what_failed, recommended_actions,
    format_telegram, build_report,
)


def test_grade_no_picks():
    assert "N/A" in grade({"closed_picks": 0})


def test_grade_a():
    g = grade({"closed_picks": 5, "total_r": 5, "avg_alpha_spy": 2})
    assert "A " in g or "A (" in g


def test_grade_f_crisis():
    g = grade({"closed_picks": 5, "total_r": -8, "avg_alpha_spy": -5})
    assert "F " in g or "F (" in g


def test_what_worked_empty():
    out = what_worked([])
    assert out == ["(no closed picks this week)"]


def test_what_worked_finds_winning_type():
    """Make 3 day-trades all wins → should appear in 'worked'."""
    picks = [
        {"trade_type": "day", "tag": "AI", "evaluation_status": "tp_hit",
         "r_multiple": "1.5", "actual_return_pct": "5", "alpha_pct": "2",
         "sector_alpha_pct": "1"} for _ in range(3)
    ]
    out = what_worked(picks)
    assert any("DAY" in w for w in out)


def test_what_failed_finds_losing_tag():
    picks = [
        {"trade_type": "swing", "tag": "SEMI", "evaluation_status": "sl_hit",
         "r_multiple": "-1", "actual_return_pct": "-3", "alpha_pct": "-2",
         "sector_alpha_pct": "-1"} for _ in range(3)
    ]
    out = what_failed(picks)
    assert any("SEMI" in f or "SWING" in f for f in out)


def test_recommendations_for_crisis():
    actions = recommended_actions(
        {"avg_alpha_sec": -3, "win_rate": 0.1, "closed_picks": 5, "total_r": -10},
        ["SWING trades lost 5/5"],
        "🔴 F (crisis)",
    )
    assert any("FAILING" in a for a in actions)
    assert any("SWING" in a for a in actions)


def test_recommendations_no_picks_safe():
    actions = recommended_actions(
        {"closed_picks": 0, "win_rate": None, "total_r": None},
        [],
        "⚪ N/A",
    )
    assert len(actions) >= 1  # Always returns at least 1 action


def test_format_telegram_smoke():
    r = build_report(end_date=datetime.now())
    text = format_telegram(r)
    assert "Weekly Self-Assessment" in text
    assert "GRADE:" in text
    assert "Wisdom base" in text
    assert "Recommended action" in text


def test_build_report_returns_all_sections():
    r = build_report(end_date=datetime.now())
    assert "grade" in r
    assert "metrics" in r
    assert "worked" in r
    assert "failed" in r
    assert "wisdom" in r
    assert "actions" in r
