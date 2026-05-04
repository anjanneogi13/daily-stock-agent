"""E3b — Regime-aware position sizing tests.

Locks behavior: same pick should produce smaller qty in chop/bear than bull.
"""
from src.risk_manager import (
    atr_trade_plan, regime_risk_multiplier, REGIME_RISK_MULT
)


# ── regime_risk_multiplier ───────────────────────────────────────
def test_bull_full_risk():
    assert regime_risk_multiplier("bull") == 1.0


def test_transition_cuts_20pct():
    assert regime_risk_multiplier("transition") == 0.8


def test_chop_cuts_40pct():
    assert regime_risk_multiplier("chop") == 0.6


def test_bear_cuts_60pct():
    assert regime_risk_multiplier("bear") == 0.4


def test_unknown_defaults_to_defensive():
    """Defensive default — never accidentally size up in murky conditions."""
    assert regime_risk_multiplier("unknown") == 0.7
    assert regime_risk_multiplier(None) == 0.7
    assert regime_risk_multiplier("") == 0.7
    assert regime_risk_multiplier("garbage_value") == 0.7


def test_multiplier_dict_complete():
    """All 4 regimes + unknown must be in the dict."""
    for k in ("bull", "transition", "chop", "bear", "unknown"):
        assert k in REGIME_RISK_MULT


# ── atr_trade_plan with regime ───────────────────────────────────
def _plan(regime):
    """Same pick, just different regime."""
    return atr_trade_plan(price=100.0, atr=2.0, capital=10_000,
                          risk_pct=0.01, regime=regime)


def test_bull_qty_largest():
    bull_qty = _plan("bull")["quantity"]
    chop_qty = _plan("chop")["quantity"]
    bear_qty = _plan("bear")["quantity"]
    assert bull_qty > chop_qty > bear_qty


def test_chop_qty_60pct_of_bull():
    """Chop should size 0.6x bull — give or take int rounding."""
    bull = _plan("bull")["quantity"]
    chop = _plan("chop")["quantity"]
    ratio = chop / bull
    assert 0.55 <= ratio <= 0.65


def test_bear_qty_40pct_of_bull():
    bull = _plan("bull")["quantity"]
    bear = _plan("bear")["quantity"]
    ratio = bear / bull
    assert 0.35 <= ratio <= 0.45


def test_plan_includes_regime_audit_fields():
    p = _plan("chop")
    assert p["regime"] == "chop"
    assert p["regime_risk_mult"] == 0.6


def test_plan_unknown_regime_defaults_safely():
    p = atr_trade_plan(price=100, atr=2, capital=10_000, regime=None)
    assert p["regime_risk_mult"] == 0.7  # defensive default


def test_backward_compat_no_regime_arg():
    """Existing callers that don't pass regime still work."""
    p = atr_trade_plan(price=100, atr=2, capital=10_000)
    assert p["quantity"] > 0  # didn't crash
    assert p["regime_risk_mult"] == 0.7  # unknown default applied
    assert p["regime"] is None
