"""Finding #5: chop regime must produce defensive adjustments, not no-op."""
from src.probability_engine import (
    compute_probabilistic_decision,
    SignalState,
    REGIME_ADJUSTMENTS,
)


def test_chop_regime_key_exists():
    """REGIME_ADJUSTMENTS must include 'chop' (returned by regime.py since E3a)."""
    assert "chop" in REGIME_ADJUSTMENTS, \
        "regime.py returns chop but probability_engine had no entry → silently downgraded to 'unknown'"


def test_chop_is_more_defensive_than_unknown():
    """chop must reduce p_win and tp vs unknown, since chop = below SMA but not collapsed."""
    chop = REGIME_ADJUSTMENTS["chop"]
    unknown = REGIME_ADJUSTMENTS["unknown"]
    assert chop["p_win_boost"] < unknown["p_win_boost"], "chop must hurt p_win vs unknown"
    assert chop["tp_mult"] < unknown["tp_mult"], "chop must shrink TP vs unknown"


def test_chop_decision_differs_from_unknown_decision():
    """End-to-end: same pick under chop vs unknown must produce different EV."""
    sig_chop = SignalState(regime="chop", news_score=0.0, news_sentiment="neutral")
    sig_unknown = SignalState(regime="unknown", news_score=0.0, news_sentiment="neutral")

    d_chop = compute_probabilistic_decision("FAKE", entry_price=100.0, signals=sig_chop)
    d_unknown = compute_probabilistic_decision("FAKE", entry_price=100.0, signals=sig_unknown)

    # chop must be more pessimistic
    assert d_chop.p_win < d_unknown.p_win, \
        f"chop p_win ({d_chop.p_win}) should be less than unknown ({d_unknown.p_win})"
    assert d_chop.expected_value_pct < d_unknown.expected_value_pct, \
        "chop EV must be lower than unknown EV"
