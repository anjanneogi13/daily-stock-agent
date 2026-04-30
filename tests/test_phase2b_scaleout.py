"""Phase 2B.1 — scale-out exit tier tests."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.exit_manager import compute_exit_tiers
from src.risk_manager import atr_trade_plan


# ═══ compute_exit_tiers tests ═══

def test_swing_tier_prices_correct():
    """Swing: tp1=1.5×ATR, tp2=2.5×ATR above entry."""
    t = compute_exit_tiers(entry=100.0, atr=2.0, qty=9, trade_type="swing")
    assert t["tp1"] == 103.0  # 100 + 1.5*2
    assert t["tp2"] == 105.0  # 100 + 2.5*2


def test_day_tier_prices_tighter():
    """Day: tp1=0.75×ATR, tp2=1.5×ATR (tighter for intraday)."""
    t = compute_exit_tiers(entry=100.0, atr=2.0, qty=9, trade_type="day")
    assert t["tp1"] == 101.5  # 100 + 0.75*2
    assert t["tp2"] == 103.0  # 100 + 1.5*2


def test_qty_split_divisible_by_three():
    t = compute_exit_tiers(100.0, 2.0, qty=9)
    assert t["qty_t1"] == 3
    assert t["qty_t2"] == 3
    assert t["qty_t3"] == 3
    assert t["qty_t1"] + t["qty_t2"] + t["qty_t3"] == 9


def test_qty_split_remainder_goes_to_t3():
    """qty=10 → 3/3/4 (last tier gets the extra)."""
    t = compute_exit_tiers(100.0, 2.0, qty=10)
    assert t["qty_t1"] == 3
    assert t["qty_t2"] == 3
    assert t["qty_t3"] == 4
    assert sum([t["qty_t1"], t["qty_t2"], t["qty_t3"]]) == 10


def test_qty_too_small_collapses_to_single_exit():
    """qty<3: can't split, all goes to tp2 (bulk target)."""
    t = compute_exit_tiers(100.0, 2.0, qty=2)
    assert t["qty_t1"] == 0
    assert t["qty_t2"] == 2
    assert t["qty_t3"] == 0


def test_zero_atr_falls_back_to_2pct():
    """Zero ATR → use price × 0.02 as fallback."""
    t = compute_exit_tiers(100.0, 0, qty=9, trade_type="swing")
    # atr=2 (2% of 100), tp1=100+1.5*2=103, tp2=100+2.5*2=105
    assert t["tp1"] == 103.0
    assert t["tp2"] == 105.0


def test_tp3_mode_is_trail():
    """Third tier is always trailing (set in 2B.2 PR)."""
    t = compute_exit_tiers(100.0, 2.0, qty=9)
    assert t["tp3_mode"] == "trail"


# ═══ atr_trade_plan integration ═══

def test_atr_trade_plan_includes_tier_fields():
    """atr_trade_plan should now return tp1/tp2/qty_t1/t2/t3 fields."""
    plan = atr_trade_plan(price=100.0, atr=2.0, capital=10000.0, trade_type="swing")
    assert "tp1" in plan
    assert "tp2" in plan
    assert "qty_t1" in plan
    assert "qty_t2" in plan
    assert "qty_t3" in plan
    assert "tp3_mode" in plan
    # take_profit (legacy) should still equal the bulk tier (tp2 = 2.5×ATR)
    assert plan["take_profit"] == plan["tp2"]
