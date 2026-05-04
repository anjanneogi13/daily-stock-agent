"""Finding #4: Total fetch failure + no cache must NOT default to bullish full-size trades."""
from unittest.mock import patch
import pandas as pd
import src.regime as regime_mod
from src.regime import market_regime


def test_total_failure_no_cache_returns_defensive():
    """When SPY fetch returns empty AND no cache exists, must NOT be bullish."""
    empty_df = pd.DataFrame()

    with patch.object(regime_mod, "_fetch_spy_with_retry", return_value=empty_df), \
         patch.object(regime_mod, "_load_cached_regime", return_value=None):
        result = market_regime()

    assert result["fetch_failed"] is True
    assert result["regime"] != "bull", \
        f"Fallback regime is '{result['regime']}' — must NOT be 'bull' (would trade full size on data blackout)"
    assert result["bullish"] is False, \
        "bullish must be False on total failure — defensive default"


def test_total_failure_falls_back_to_transition():
    """Specific check: fallback should be 'transition' (0.8x sizing in atr_trade_plan)."""
    empty_df = pd.DataFrame()

    with patch.object(regime_mod, "_fetch_spy_with_retry", return_value=empty_df), \
         patch.object(regime_mod, "_load_cached_regime", return_value=None):
        result = market_regime()

    assert result["regime"] == "transition", \
        f"Expected 'transition' fallback (defensive but allows trading), got '{result['regime']}'"
    assert result["fallback"] == "no_data_no_cache"


def test_cached_regime_still_used_when_available():
    """If cache exists, prefer it over the new defensive fallback."""
    empty_df = pd.DataFrame()
    cached = {"regime": "bear", "spy_close": 400.0, "spy_sma200": 420.0,
              "bullish": False, "sma_window": 200, "distance_pct": -4.76}

    with patch.object(regime_mod, "_fetch_spy_with_retry", return_value=empty_df), \
         patch.object(regime_mod, "_load_cached_regime", return_value=cached):
        result = market_regime()

    # Cache hit: regime preserved, fetch_failed flag set
    assert result["regime"] == "bear"
    assert result["fetch_failed"] is True
