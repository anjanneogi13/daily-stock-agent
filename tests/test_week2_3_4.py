"""Smoke tests for Week 2/3/4 features. Run via: pytest tests/"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.market_guard import classify_trade_type, vix_level, spy_trend, sector_strength
from src.risk_manager import atr_trade_plan
from src.scorer import apply_sector_cap
from src.premarket_filter import gap_check
from src.performance_tracker import (
    compute_metrics, _r_multiple, _safe_float, _sharpe, _max_drawdown
)


# ═══ Week 2: Trade type classifier ═══════════════════════════════
def test_classify_high_momentum_volume_is_day():
    assert classify_trade_type({"momentum": 0.85, "volume": 0.8, "trend": 0.6}) == "day"

def test_classify_trend_only_is_swing():
    assert classify_trade_type({"momentum": 0.5, "volume": 0.5, "trend": 0.85}) == "swing"

def test_classify_handles_missing_keys():
    assert classify_trade_type({}) == "swing"  # safe default

def test_classify_high_momentum_with_gap_is_swing():
    """If gap is too large, even high momentum should NOT be day-trade."""
    assert classify_trade_type({"momentum": 0.85, "volume": 0.8, "trend": 0.6}, gap_pct=0.05) == "swing"


# ═══ Week 2: ATR trade plan ══════════════════════════════════════
def test_atr_swing_trade_2x_stop():
    plan = atr_trade_plan(100, 2, 10000, trade_type="swing", regime="bull")
    assert plan["stop_loss"] == 96.0  # 100 - (2*ATR=2)
    assert plan["take_profit"] == 105.0  # Tier 1: 100 + (2.5*ATR=2)
    assert plan["risk_reward"] == 1.25  # Tier 1: 2.5/2.0 ATR

def test_atr_day_trade_tighter_stop():
    """PR #67: Day trade stops tightened from 1.0×ATR to 0.6×ATR
    (was 2% stop, now ~1.2% stop — matches user 3-4% daily target)."""
    plan = atr_trade_plan(100, 2, 10000, trade_type="day", regime="bull")
    assert plan["stop_loss"] == 98.8   # 100 - (0.6*ATR=1.2) → tighter
    assert plan["take_profit"] == 102.0  # PR #67: 100 + (1.0*ATR=2.0)
    assert plan["risk_reward"] == 1.67  # PR #67: TP(2.0) / SL(1.2) = 1.67

def test_atr_zero_atr_uses_fallback():
    plan = atr_trade_plan(100, 0, 10000, trade_type="swing", regime="bull")
    # Falls back to 2% (atr = price * 0.02 = 2)
    assert plan["stop_loss"] < 100
    assert plan["take_profit"] > 100
    assert plan["quantity"] >= 1

def test_atr_position_sizing_respects_risk():
    # 1% risk on $10k = $100. Stop at $96 = $4 risk/share. Should be 25 shares.
    plan = atr_trade_plan(100, 2, 10000, risk_pct=0.01, trade_type="swing", regime="bull")
    assert plan["quantity"] == 25


# ═══ Week 3: Sector cap ══════════════════════════════════════════
def test_sector_cap_basic():
    picks = [
        {"ticker": f"T{i}", "scores": {"composite": 1.0 - i*0.01},
         "info_short": {"sector": "Technology"}}
        for i in range(10)
    ]
    result = apply_sector_cap(picks, max_per_sector=4)
    assert len(result) == 4
    assert all(p["info_short"]["sector"] == "Technology" for p in result)

def test_sector_cap_with_weak_sector():
    picks = [
        {"ticker": f"T{i}", "scores": {"composite": 0.9},
         "info_short": {"sector": "Technology"}} for i in range(5)
    ] + [
        {"ticker": f"F{i}", "scores": {"composite": 0.7},
         "info_short": {"sector": "Financials"}} for i in range(5)
    ]
    result = apply_sector_cap(picks, max_per_sector=4, reduced_sectors={"Technology": 2})
    tech = sum(1 for p in result if p["info_short"]["sector"] == "Technology")
    fin = sum(1 for p in result if p["info_short"]["sector"] == "Financials")
    assert tech == 2  # capped to 2 (weak sector)
    assert fin == 4   # full cap

def test_sector_cap_keeps_highest_score_first():
    picks = [
        {"ticker": "LOW",  "scores": {"composite": 0.5}, "info_short": {"sector": "Tech"}},
        {"ticker": "HIGH", "scores": {"composite": 0.9}, "info_short": {"sector": "Tech"}},
    ]
    result = apply_sector_cap(picks, max_per_sector=1)
    assert result[0]["ticker"] == "HIGH"


# ═══ Week 4: Performance metrics ═════════════════════════════════
def test_safe_float_handles_empty_string():
    assert _safe_float("") == 0.0
    assert _safe_float(None) == 0.0
    assert _safe_float("3.14") == 3.14
    assert _safe_float("not a number") == 0.0

def test_r_multiple_winning_trade():
    row = {"entry": "100", "stop_loss": "95", "exit_price": "110"}
    assert _r_multiple(row) == 2.0  # (110-100)/(100-95) = 10/5 = 2

def test_r_multiple_losing_trade():
    row = {"entry": "100", "stop_loss": "95", "exit_price": "94"}
    assert _r_multiple(row) == -1.2  # (94-100)/(100-95) = -6/5 = -1.2

def test_compute_metrics_empty_returns_zeros():
    m = compute_metrics([], "test")
    assert m["n_trades"] == 0
    assert m["win_rate"] == 0.0

def test_compute_metrics_basic():
    picks = [
        {"ticker": "WIN1", "entry": "100", "stop_loss": "95", "exit_price": "110",
         "actual_return_pct": "10"},
        {"ticker": "WIN2", "entry": "100", "stop_loss": "95", "exit_price": "105",
         "actual_return_pct": "5"},
        {"ticker": "LOSS", "entry": "100", "stop_loss": "95", "exit_price": "94",
         "actual_return_pct": "-6"},
    ]
    m = compute_metrics(picks, "test")
    assert m["n_trades"] == 3
    assert m["wins"] == 2
    assert m["losses"] == 1
    assert m["win_rate"] == 66.7
    assert m["best_ticker"] == "WIN1"
    assert m["worst_ticker"] == "LOSS"

def test_max_drawdown_calculation():
    # Returns: +10%, -20%, +5% → equity 100 → 110 → 88 → 92.4. Max DD from 110 → 88 = 20%
    dd = _max_drawdown([10, -20, 5])
    assert 19 < dd < 21


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))


# ═══ Regression: ATR key compatibility with indicators.py ════════
def test_atr_key_matches_indicators():
    """Make sure parallel_scorer reads the same ATR key indicators.py writes."""
    from src.indicators import latest_signals
    import inspect, src.parallel_scorer as ps
    src_code = inspect.getsource(ps._score_one)
    # indicators writes "atr_14" — scorer must read it
    assert 'atr_14' in src_code, "parallel_scorer must read 'atr_14' (key from indicators.py)"


# ═══ Regression: ATR key compatibility with indicators.py ════════
def test_atr_key_matches_indicators():
    """Make sure parallel_scorer reads the same ATR key indicators.py writes."""
    from src.indicators import latest_signals
    import inspect, src.parallel_scorer as ps
    src_code = inspect.getsource(ps._score_one)
    # indicators writes "atr_14" — scorer must read it
    assert 'atr_14' in src_code, "parallel_scorer must read 'atr_14' (key from indicators.py)"


# ═══ Tier 1 Bug Fixes ═══════════════════════════════════════
def test_apply_tag_cap_caps_semi_to_two():
    """Hard cap on tag — even if yfinance sector mismatches, only 2 SEMIs survive."""
    from src.scorer import apply_tag_cap
    picks = [
        {"ticker": f"X{i}", "tag": "SEMI / AI", "scores": {"composite": 0.9 - i*0.01}}
        for i in range(10)
    ]
    capped = apply_tag_cap(picks, max_per_tag=2)
    semi_count = sum(1 for p in capped if p["tag"].startswith("SEMI"))
    assert semi_count == 2, f"Expected 2 SEMIs, got {semi_count}"


def test_apply_tag_cap_keeps_highest_score_first():
    """Tag cap must keep the 2 highest-scored stocks per tag."""
    from src.scorer import apply_tag_cap
    picks = [
        {"ticker": "LOW",  "tag": "SEMI", "scores": {"composite": 0.50}},
        {"ticker": "HIGH", "tag": "SEMI", "scores": {"composite": 0.95}},
        {"ticker": "MID",  "tag": "SEMI", "scores": {"composite": 0.75}},
    ]
    capped = apply_tag_cap(picks, max_per_tag=2)
    tickers = [p["ticker"] for p in capped]
    assert "HIGH" in tickers and "MID" in tickers
    assert "LOW" not in tickers


def test_apply_tag_cap_keeps_picks_without_tag():
    """Picks without a tag pass through untouched."""
    from src.scorer import apply_tag_cap
    picks = [
        {"ticker": "A", "tag": "", "scores": {"composite": 0.8}},
        {"ticker": "B", "scores": {"composite": 0.7}},  # no tag at all
    ]
    capped = apply_tag_cap(picks, max_per_tag=2)
    assert len(capped) == 2


def test_atr_swing_tp_mult_is_2_5_not_4():
    """Tier 1: TP multiplier for swing trades lowered from 4.0 to 2.5 (hittable)."""
    from src.risk_manager import atr_trade_plan
    plan = atr_trade_plan(price=100.0, atr=2.0, capital=10000.0, trade_type="swing", regime="bull")
    # Risk = 2*ATR=4 below entry → SL=$96. TP at 2.5*ATR=$5 above → TP=$105
    assert plan["take_profit"] == 105.0  # Tier 1: 100 + (2.5*ATR=2)
    assert plan["stop_loss"] == 96.0
    # R:R = 5/4 = 1.25
    assert 1.20 <= plan["risk_reward"] <= 1.30


def test_atr_day_tp_mult_is_1_5_not_2():
    """PR #67: Day trade TP further tightened from 1.5×ATR to 1.0×ATR
    for quicker intraday wins. SL=0.6×ATR=1.2, TP=1.0×ATR=2.0."""
    from src.risk_manager import atr_trade_plan
    plan = atr_trade_plan(price=100.0, atr=2.0, capital=10000.0, trade_type="day", regime="bull")
    assert plan["stop_loss"] == 98.8       # 100 - 0.6*2.0 = 98.8
    assert plan["take_profit"] == 102.0    # 100 + 1.0*2.0 = 102.0
