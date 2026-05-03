"""T45 / Pillar 5: rolling 30d CIs + monthly calibration."""
from __future__ import annotations
import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from src import self_awareness as sa
from src import signal_journal as sj


# ── Wilson CI ──
def test_wilson_ci_zero_sample():
    lo, hi = sa.wilson_ci(0, 0)
    assert (lo, hi) == (0.0, 0.0)

def test_wilson_ci_full_wins():
    lo, hi = sa.wilson_ci(10, 10)
    assert lo > 0.7   # not 1.0 — Wilson is conservative
    assert hi == 1.0

def test_wilson_ci_half_wins():
    lo, hi = sa.wilson_ci(50, 100)
    assert lo < 0.5 < hi
    assert hi - lo < 0.25  # n=100 → fairly tight


# ── mean R CI ──
def test_mean_r_ci_empty():
    assert sa.mean_r_ci([]) == (0.0, 0.0, 0.0)

def test_mean_r_ci_single_value():
    assert sa.mean_r_ci([1.5]) == (1.5, 1.5, 1.5)

def test_mean_r_ci_brackets_mean():
    mean, lo, hi = sa.mean_r_ci([1.0, 2.0, 3.0, 4.0, 5.0])
    assert lo < mean < hi
    assert mean == pytest.approx(3.0)


# ── rolling_window ──
@pytest.fixture
def journal(tmp_path, monkeypatch):
    p = tmp_path / "j.jsonl"
    monkeypatch.setattr(sj, "JOURNAL", p)
    return p

def _rec(ticker, outcome, r, days_ago):
    d = (datetime.now() - timedelta(days=days_ago)).date().isoformat()
    return {"ticker": ticker, "pick_date": d, "evaluated_on": d,
            "outcome": outcome, "r_multiple": r,
            "signals": {"trade_type":"swing"}}

def _seed(p, recs):
    with p.open("w") as f:
        for r in recs:
            f.write(json.dumps(r) + "\n")


def test_rolling_window_filters_by_days(journal):
    _seed(journal, [
        _rec("A","win", 2.0, days_ago=5),
        _rec("B","loss",-1.0, days_ago=10),
        _rec("OLD","win",2.0, days_ago=60),  # outside 30d
    ])
    s = sa.rolling_window(30)
    assert s["n"] == 2
    assert s["wins"] == 1
    assert s["win_rate"] == 0.5

def test_rolling_window_empty(journal):
    s = sa.rolling_window(30)
    assert s["n"] == 0
    assert s["verdict"] == "INCONCLUSIVE"

def test_rolling_window_verdict_inconclusive_low_n(journal):
    _seed(journal, [_rec(f"X{i}","win",2.0,days_ago=1) for i in range(10)])
    s = sa.rolling_window(30)
    assert s["verdict"] == "INCONCLUSIVE"  # n<20 always inconclusive

def test_rolling_window_verdict_edge_confirmed(journal):
    # 25 picks, 18 wins, mean R ≈ +1.0 → edge confirmed
    recs = ([_rec(f"W{i}","win", 2.0, days_ago=i+1) for i in range(18)] +
            [_rec(f"L{i}","loss",-1.0,days_ago=i+1) for i in range(7)])
    _seed(journal, recs)
    s = sa.rolling_window(30)
    assert s["verdict"] == "EDGE_CONFIRMED"

def test_rolling_window_verdict_edge_broken(journal):
    # 30 picks, 2 wins (WR 7%) — wr_hi << 0.35 → edge broken
    recs = ([_rec(f"W{i}","win", 1.0, days_ago=i+1) for i in range(2)] +
            [_rec(f"L{i}","loss",-1.0,days_ago=i+3) for i in range(28)])
    _seed(journal, recs)
    s = sa.rolling_window(30)
    assert s["verdict"] == "EDGE_BROKEN"


# ── format_footer ──
def test_format_footer_empty():
    assert sa.format_footer({"n":0}) == ""

def test_format_footer_nonempty():
    s = {"n":18,"wins":7,"win_rate":0.389,"wr_ci_lo":0.2,"wr_ci_hi":0.61,
         "mean_r":-0.12,"r_ci_lo":-0.55,"r_ci_hi":0.31,
         "verdict":"INCONCLUSIVE","days":30}
    out = sa.format_footer(s)
    assert "30d edge: INCONCLUSIVE" in out
    assert "WR 39%" in out
    assert "95% CI" in out


# ── monthly_calibration ──
def test_monthly_calibration_returns_3_windows(journal):
    _seed(journal, [_rec(f"X{i}","win",2.0,days_ago=i+1) for i in range(10)])
    cal = sa.monthly_calibration()
    assert "30d" in cal and "60d" in cal and "90d" in cal
    assert cal["trend"] in ("improving","stable","decaying")
