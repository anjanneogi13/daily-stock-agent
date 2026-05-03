"""T46 / Pillar 6: week-over-week trend tests."""
from __future__ import annotations
from datetime import datetime, timedelta
import pytest

from src import wow_trend as wt


def _pick(days_ago, r, alpha=0.0):
    d = (datetime.now() - timedelta(days=days_ago)).date().isoformat()
    return {"pick_date": d, "evaluated_on": d,
            "r_multiple": r, "alpha_pct": alpha}


def test_compare_empty_returns_zeros():
    cmp = wt.compare([])
    assert cmp["this_week"]["n"] == 0
    assert cmp["last_week"]["n"] == 0


def test_compare_classifies_into_windows():
    picks = [
        _pick(2, 1.5),    # this week
        _pick(5, -1.0),   # this week
        _pick(10, 2.0),   # last week
        _pick(20, 0.5),   # outside both
    ]
    cmp = wt.compare(picks)
    assert cmp["this_week"]["n"] == 2
    assert cmp["last_week"]["n"] == 1


def test_compare_deltas_correct():
    picks = [
        _pick(2, 2.0),  # this week (1 win, mean R 2.0)
        _pick(10, -1.0),  # last week (0 wins, mean R -1.0)
    ]
    cmp = wt.compare(picks)
    assert cmp["deltas"]["mean_r"] == pytest.approx(3.0)
    assert cmp["deltas"]["win_rate"] == pytest.approx(1.0)


def test_format_footer_empty_no_prior():
    cmp = wt.compare([_pick(2, 1.0)])  # only this-week data
    assert wt.format_footer(cmp) == ""


def test_format_footer_renders():
    picks = [_pick(2, 2.0), _pick(10, -1.0)]
    out = wt.format_footer(wt.compare(picks))
    assert "Trades:" in out
    assert "WR:" in out
    assert "Mean R" in out
    assert "🟢" in out or "🔴" in out


def test_arrow_helper():
    assert "🟢" in wt._arrow(0.5, good_positive=True)
    assert "🔴" in wt._arrow(-0.5, good_positive=True)
    assert wt._arrow(0.0) == "→"
