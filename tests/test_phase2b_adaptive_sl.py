"""Phase 2B.5 — adaptive SL tighten tests."""
import sys, json
from pathlib import Path
from datetime import datetime, timedelta
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.adaptive_sl import should_tighten_sl, append_tighten_audit, last_tighten_ts


# ═══ should_tighten_sl ═══

def test_tighten_fires_when_all_conditions_met():
    """+5% profit, RSI faded 75→52, vol died → tighten."""
    should, new_sl, reason = should_tighten_sl(
        entry=100, current_price=105, current_sl=98,
        current_rsi=52, peak_rsi=75, vol_ratio=0.5,
    )
    assert should is True
    assert new_sl == 103.95  # 105 × 0.99
    assert "fading" in reason


def test_no_tighten_if_not_profitable_enough():
    """Only +1% gain → below 2% threshold."""
    should, new_sl, _ = should_tighten_sl(
        entry=100, current_price=101, current_sl=98,
        current_rsi=50, peak_rsi=75, vol_ratio=0.4,
    )
    assert should is False
    assert new_sl == 98


def test_no_tighten_if_rsi_never_peaked_high():
    """Peak RSI was only 60 → never showed strong momentum to fade from."""
    should, _, reason = should_tighten_sl(
        entry=100, current_price=105, current_sl=98,
        current_rsi=50, peak_rsi=60, vol_ratio=0.4,
    )
    assert should is False
    assert "peak RSI" in reason


def test_no_tighten_if_rsi_still_strong():
    """Current RSI 60 → not faded yet (threshold 55)."""
    should, _, reason = should_tighten_sl(
        entry=100, current_price=105, current_sl=98,
        current_rsi=60, peak_rsi=75, vol_ratio=0.4,
    )
    assert should is False
    assert "not yet faded" in reason


def test_no_tighten_if_vol_still_high():
    """Vol still 1.2× → not dying."""
    should, _, reason = should_tighten_sl(
        entry=100, current_price=105, current_sl=98,
        current_rsi=52, peak_rsi=75, vol_ratio=1.2,
    )
    assert should is False
    assert "vol" in reason


def test_no_tighten_if_proposed_below_current_sl():
    """Trail already raised SL to $104. Price $105 × 0.99 = $103.95 < $104."""
    should, new_sl, reason = should_tighten_sl(
        entry=100, current_price=105, current_sl=104,
        current_rsi=52, peak_rsi=75, vol_ratio=0.4,
    )
    assert should is False
    assert new_sl == 104  # unchanged


def test_no_tighten_during_cooldown():
    """Last tighten 10min ago (cooldown 30min) → blocked."""
    recent = (datetime.now() - timedelta(minutes=10)).isoformat()
    should, _, reason = should_tighten_sl(
        entry=100, current_price=105, current_sl=98,
        current_rsi=52, peak_rsi=75, vol_ratio=0.4,
        last_tighten_iso=recent,
    )
    assert should is False
    assert "cooldown" in reason


def test_tighten_after_cooldown_expires():
    """Last tighten 45min ago → cooldown cleared."""
    old = (datetime.now() - timedelta(minutes=45)).isoformat()
    should, _, _ = should_tighten_sl(
        entry=100, current_price=105, current_sl=98,
        current_rsi=52, peak_rsi=75, vol_ratio=0.4,
        last_tighten_iso=old,
    )
    assert should is True


def test_no_tighten_if_missing_rsi():
    """No RSI data → cannot evaluate fade."""
    should, _, reason = should_tighten_sl(
        entry=100, current_price=105, current_sl=98,
        current_rsi=None, peak_rsi=75, vol_ratio=0.4,
    )
    assert should is False
    assert "rsi" in reason.lower()


# ═══ audit helpers ═══

def test_append_tighten_audit_round_trip():
    """Audit appends correctly and can extract last ts."""
    audit = append_tighten_audit("[]", 103.95, "fade reason", ts="2026-05-01T14:00:00")
    history = json.loads(audit)
    assert len(history) == 1
    assert history[0]["new_sl"] == 103.95
    assert last_tighten_ts(audit) == "2026-05-01T14:00:00"

    # Append another
    audit2 = append_tighten_audit(audit, 104.50, "another", ts="2026-05-01T15:00:00")
    assert len(json.loads(audit2)) == 2
    assert last_tighten_ts(audit2) == "2026-05-01T15:00:00"
