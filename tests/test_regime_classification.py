"""E3a — Regime classification tests.

Locks the 4-state regime boundaries so future tweaks don't silently
revert to binary bull/bear (which would re-empty chop/transition
buckets in pattern_stats and signal_journal).
"""
from unittest.mock import patch
import pandas as pd


def _mock_spy_df(close: float, sma: float, days: int = 250):
    """Build a synthetic SPY DataFrame whose last close is `close` and whose
    rolling 200d mean is `sma`."""
    # Construct a series where mean(last 200) = sma but last value = close
    other = (sma * 200 - close) / 199
    closes = [other] * (days - 1) + [close]
    return pd.DataFrame({"close": closes})


def _run_with_mocked_spy(close, sma):
    """Run market_regime() with a mocked SPY DataFrame."""
    from src import regime as regime_mod
    df = _mock_spy_df(close, sma)
    with patch.object(regime_mod, "_fetch_spy_with_retry", return_value=df), \
         patch.object(regime_mod, "_save_regime", return_value=None):
        return regime_mod.market_regime()


def test_strong_bull_above_5pct():
    r = _run_with_mocked_spy(close=525, sma=500)  # +5.0%
    assert r["regime"] == "bull"


def test_strong_bull_far_above():
    r = _run_with_mocked_spy(close=600, sma=500)  # +20%
    assert r["regime"] == "bull"


def test_transition_just_below_5pct():
    r = _run_with_mocked_spy(close=520, sma=500)  # +4%
    assert r["regime"] == "transition"


def test_transition_at_zero():
    r = _run_with_mocked_spy(close=500, sma=500)  # 0%
    assert r["regime"] == "transition"


def test_transition_just_above_minus_2pct():
    r = _run_with_mocked_spy(close=491, sma=500)  # -1.8%
    assert r["regime"] == "transition"


def test_chop_at_minus_2pct_boundary():
    r = _run_with_mocked_spy(close=490, sma=500)  # -2.0% → chop
    assert r["regime"] == "chop"


def test_chop_minus_3pct():
    r = _run_with_mocked_spy(close=485, sma=500)  # -3%
    assert r["regime"] == "chop"


def test_chop_just_above_minus_5pct():
    r = _run_with_mocked_spy(close=476, sma=500)  # -4.8% → chop (avoids float boundary)
    assert r["regime"] == "chop"


def test_bear_below_minus_5pct():
    r = _run_with_mocked_spy(close=470, sma=500)  # -6%
    assert r["regime"] == "bear"


def test_bear_deep():
    r = _run_with_mocked_spy(close=400, sma=500)  # -20%
    assert r["regime"] == "bear"


def test_distance_pct_calculated_correctly():
    r = _run_with_mocked_spy(close=510, sma=500)
    assert abs(r["distance_pct"] - 2.0) < 0.1


def test_bullish_boolean_preserved_for_legacy_callers():
    """Old code reads result['bullish']. Don't break it."""
    r_bull   = _run_with_mocked_spy(close=525, sma=500)
    r_bear   = _run_with_mocked_spy(close=470, sma=500)
    r_chop   = _run_with_mocked_spy(close=485, sma=500)
    assert r_bull["bullish"] is True
    assert r_bear["bullish"] is False
    assert r_chop["bullish"] is False  # below SMA = not bullish
