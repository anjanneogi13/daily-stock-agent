"""Phase 2B.4 — exit_metrics + end-to-end smoke tests."""
import sys, json, csv, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.exit_metrics import (
    tier_hit_breakdown, trail_stats, tp_raise_stats, capture_efficiency
)


# ═══ tier_hit_breakdown ═══

def test_tier_hit_breakdown_counts_correctly():
    picks = [
        {"tier_status": "tp1_hit"},
        {"tier_status": "tp1_hit"},
        {"tier_status": "tp2_hit"},
        {"tier_status": "trailing"},
        {"tier_status": "none"},
    ]
    result = tier_hit_breakdown(picks)
    assert result["tp1_hit"] == 2
    assert result["tp2_hit"] == 1
    assert result["trailing"] == 1
    assert result["none"] == 1


# ═══ trail_stats ═══

def test_trail_stats_calculates_locked_gains():
    picks = [
        {"trail_active": "true", "entry": "100", "current_sl": "104"},  # +4% locked
        {"trail_active": "true", "entry": "200", "current_sl": "212"},  # +6% locked
        {"trail_active": "false", "entry": "50", "current_sl": "47"},   # ignored
    ]
    s = trail_stats(picks)
    assert s["active_count"] == 2
    assert s["avg_locked_gain_pct"] == 5.0  # (4+6)/2
    assert s["max_locked_gain_pct"] == 6.0


# ═══ tp_raise_stats ═══

def test_tp_raise_stats_counts_raises_from_audit():
    picks = [
        {
            "take_profit": "100",
            "tp_raises": json.dumps([
                {"ts": "2026-05-01T14:00", "new_tp": 105, "reason": "x"},
                {"ts": "2026-05-01T15:00", "new_tp": 110, "reason": "y"},
            ]),
        },
        {"take_profit": "50", "tp_raises": "[]"},
        {"take_profit": "200", "tp_raises": ""},  # malformed → ignored
    ]
    s = tp_raise_stats(picks)
    assert s["raised_count"] == 1
    assert s["total_raises"] == 2
    # Avg bump: (105-100)/100=5% + (110-100)/100=10% → avg 7.5%
    assert s["avg_raise_pct"] == 7.5


# ═══ capture_efficiency ═══

def test_capture_efficiency_higher_is_better():
    """If we realized 5% but MFE was 10%, capture = 50%."""
    picks = [
        {"ticker": "AAA", "actual_return_pct": "5.0"},
        {"ticker": "BBB", "actual_return_pct": "3.0"},
    ]
    exec_report = {
        "picks": [
            {"ticker": "AAA", "mfe_pct": 10.0},
            {"ticker": "BBB", "mfe_pct": 6.0},
        ]
    }
    result = capture_efficiency(picks, exec_report)
    assert result["n_evaluated"] == 2
    assert result["avg_realized_pct"] == 4.0
    assert result["avg_mfe_pct"] == 8.0
    assert result["capture_pct"] == 50.0
    assert result["leakage_pct"] == 50.0


# ═══ End-to-end smoke test ═══

def test_phase_2b_full_lifecycle_smoke():
    """A pick goes through: scale-out plan → trail activates → TP raises.
    Verify all Phase 2B modules wire together without crashes.
    """
    from src.risk_manager import atr_trade_plan
    from src.trailing_stop import compute_trailing_sl
    from src.adaptive_tp import should_raise_tp, append_raise_audit

    # 1. Build trade plan with scale-out
    plan = atr_trade_plan(price=100, atr=2, capital=10000, trade_type="swing")
    assert plan["tp1"] == 103.0
    assert plan["tp2"] == 105.0
    assert plan["qty_t1"] + plan["qty_t2"] + plan["qty_t3"] == plan["quantity"]

    # 2. Simulate price rising — trail activates at +3%
    new_sl, raised = compute_trailing_sl(
        entry=100, peak_price=105, current_sl=plan["stop_loss"]
    )
    assert raised is True
    assert new_sl == 102.9

    # 3. Strong momentum at +7% → adaptive TP raise
    should, new_tp, reason = should_raise_tp(
        entry=100, current_price=107, current_tp=plan["tp2"],
        current_rsi=75, vol_ratio=2.3,
    )
    assert should is True
    assert new_tp > plan["tp2"]
    assert "RSI 75" in reason

    # 4. Audit appended cleanly
    audit = append_raise_audit("[]", new_tp, reason)
    history = json.loads(audit)
    assert len(history) == 1
    assert history[0]["new_tp"] == new_tp
