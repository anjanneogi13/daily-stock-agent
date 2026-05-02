"""Tests for Backtester v2 — focus on look-ahead bias prevention."""
import pandas as pd
import numpy as np
from datetime import date

from src.backtester.pit_data import slice_pit, get_forward_window
from src.backtester.outcome_simulator import simulate_outcome
from src.backtester.metrics import compute_metrics


def _make_df(n_days=200, start="2024-01-01"):
    idx = pd.date_range(start=start, periods=n_days, freq="B")
    rng = np.random.default_rng(42)
    closes = 100 + np.cumsum(rng.normal(0.1, 1, n_days))
    return pd.DataFrame({
        "Open": closes - 0.3, "High": closes + 0.5,
        "Low": closes - 0.5, "Close": closes,
        "Volume": rng.integers(1e6, 5e6, n_days),
    }, index=idx)


def test_pit_slice_excludes_as_of_date():
    """Algo on day D must NOT see day D's data."""
    df = _make_df(200)
    cutoff = df.index[100].date()
    sliced = slice_pit(df, as_of=cutoff, min_history_days=10)
    assert sliced is not None
    assert sliced.index.max().date() < cutoff, "LOOK-AHEAD BIAS DETECTED"


def test_pit_returns_none_if_insufficient_history():
    df = _make_df(30)
    sliced = slice_pit(df, as_of=df.index[10].date(), min_history_days=60)
    assert sliced is None


def test_forward_window_starts_at_or_after_as_of():
    df = _make_df(200)
    cutoff = df.index[100].date()
    fwd = get_forward_window(df, as_of=cutoff, n_days=10)
    assert fwd is not None
    assert len(fwd) == 10
    assert fwd.index[0].date() >= cutoff


def test_outcome_sl_hit_when_low_breaches():
    bars = pd.DataFrame({
        "Open": [100], "High": [102], "Low": [94], "Close": [98],
    }, index=pd.date_range("2024-06-01", periods=1, freq="B"))
    out = simulate_outcome(bars, entry=100, stop_loss=95,
                           take_profit=110, max_hold_days=5)
    assert out["exit_status"] == "sl_hit"
    assert out["exit_price"] == 95
    assert out["r_multiple"] == -1.0


def test_outcome_tp_hit_when_high_reaches():
    bars = pd.DataFrame({
        "Open": [100], "High": [115], "Low": [99], "Close": [113],
    }, index=pd.date_range("2024-06-01", periods=1, freq="B"))
    out = simulate_outcome(bars, entry=100, stop_loss=95,
                           take_profit=110, max_hold_days=5)
    assert out["exit_status"] == "tp_hit"
    assert out["r_multiple"] == 2.0


def test_outcome_conservative_sl_first_when_both_hit():
    """If SL and TP both touched same day → SL wins (pessimistic)."""
    bars = pd.DataFrame({
        "Open": [100], "High": [115], "Low": [94], "Close": [105],
    }, index=pd.date_range("2024-06-01", periods=1, freq="B"))
    out = simulate_outcome(bars, entry=100, stop_loss=95,
                           take_profit=110, max_hold_days=5)
    assert out["exit_status"] == "sl_hit", "must be conservative"


def test_outcome_max_hold_exits_at_close():
    bars = pd.DataFrame({
        "Open": [100, 101, 102], "High": [101, 102, 103],
        "Low": [99, 100, 101], "Close": [100.5, 101.5, 102.5],
    }, index=pd.date_range("2024-06-01", periods=3, freq="B"))
    out = simulate_outcome(bars, entry=100, stop_loss=90,
                           take_profit=120, max_hold_days=3)
    assert out["exit_status"] == "max_hold"
    assert out["exit_price"] == 102.5


def test_metrics_basic():
    picks = [
        {"r_multiple": 2.0, "return_pct": 6.0, "exit_status": "tp_hit"},
        {"r_multiple": -1.0, "return_pct": -3.0, "exit_status": "sl_hit"},
        {"r_multiple": 2.0, "return_pct": 5.5, "exit_status": "tp_hit"},
        {"r_multiple": -1.0, "return_pct": -2.8, "exit_status": "sl_hit"},
        {"r_multiple": 0.5, "return_pct": 1.5, "exit_status": "max_hold"},
    ]
    m = compute_metrics(picks)
    assert m["n_picks"] == 5
    assert m["wins"] == 3
    assert m["losses"] == 2
    assert m["win_rate_pct"] == 60.0
    assert m["statistical_warning"] is not None  # N<30


def test_metrics_warns_on_small_sample():
    picks = [{"r_multiple": 1.0, "return_pct": 3.0, "exit_status": "tp_hit"}] * 10
    m = compute_metrics(picks)
    assert m["statistical_warning"] is not None


def test_metrics_no_warning_when_n_30():
    picks = [{"r_multiple": 1.0, "return_pct": 3.0, "exit_status": "tp_hit"}] * 30
    m = compute_metrics(picks)
    assert m["statistical_warning"] is None


"""v1.1 tests — gap fills + cooldown + RSI cap."""
import pandas as pd
from src.backtester.outcome_simulator import simulate_outcome


def test_gap_down_fills_at_open_below_stop():
    """If next day opens below SL, fill at open (worse than stop)."""
    bars = pd.DataFrame({
        "Open": [88.0],   # gap down: opens BELOW stop of 95
        "High": [90.0],
        "Low": [85.0],
        "Close": [87.0],
    }, index=pd.date_range("2024-06-01", periods=1, freq="B"))
    out = simulate_outcome(bars, entry=100, stop_loss=95,
                           take_profit=110, max_hold_days=5)
    assert out["exit_status"] == "sl_gap"
    assert out["exit_price"] == 88.0
    assert out["r_multiple"] < -1.0, "must be worse than -1R on gap-down"


def test_gap_up_fills_at_open_above_tp():
    """If next day opens above TP, fill at open (better than TP)."""
    bars = pd.DataFrame({
        "Open": [115.0],  # gap up above TP of 110
        "High": [118.0],
        "Low": [114.0],
        "Close": [116.0],
    }, index=pd.date_range("2024-06-01", periods=1, freq="B"))
    out = simulate_outcome(bars, entry=100, stop_loss=95,
                           take_profit=110, max_hold_days=5)
    assert out["exit_status"] == "tp_gap"
    assert out["exit_price"] == 115.0
    assert out["r_multiple"] > 2.0, "must be better than 2R on gap-up"


def test_normal_sl_still_works_after_v1_1():
    """Regression: intraday SL still detected when not a gap."""
    bars = pd.DataFrame({
        "Open": [99.0], "High": [102.0], "Low": [94.0], "Close": [98.0],
    }, index=pd.date_range("2024-06-01", periods=1, freq="B"))
    out = simulate_outcome(bars, entry=100, stop_loss=95,
                           take_profit=110, max_hold_days=5)
    assert out["exit_status"] == "sl_hit"
    assert out["exit_price"] == 95
