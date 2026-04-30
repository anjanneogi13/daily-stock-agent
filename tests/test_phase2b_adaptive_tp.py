"""Phase 2B.3 — adaptive TP raise tests."""
import sys, json
from datetime import datetime, timedelta
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.adaptive_tp import should_raise_tp, append_raise_audit, last_raise_ts


# ═══ should_raise_tp: positive cases ═══

def test_all_conditions_met_raises_tp():
    """+7% gain, RSI 75, vol 2.3× → raise approved."""
    should, new_tp, reason = should_raise_tp(
        entry=100, current_price=107, current_tp=105,
        current_rsi=75, vol_ratio=2.3, last_raise_iso=None,
    )
    assert should is True
    assert new_tp == 112.35  # 107 × 1.05
    assert "RSI 75" in reason
    assert "vol 2.3" in reason


def test_new_tp_must_be_above_current():
    """If candidate TP ≤ current TP, no raise (avoids regression)."""
    # Current TP $200, price $107 → candidate $112.35 < $200 → no raise
    should, new_tp, reason = should_raise_tp(
        entry=100, current_price=107, current_tp=200,
        current_rsi=75, vol_ratio=2.3,
    )
    assert should is False
    assert new_tp == 200
    assert "not above" in reason


# ═══ should_raise_tp: negative cases (one per condition) ═══

def test_no_raise_when_gain_below_5pct():
    """Only +3% gain → fails gain threshold."""
    should, _, reason = should_raise_tp(
        entry=100, current_price=103, current_tp=105,
        current_rsi=75, vol_ratio=2.3,
    )
    assert should is False
    assert "gain only" in reason


def test_no_raise_when_rsi_below_70():
    should, _, reason = should_raise_tp(
        entry=100, current_price=107, current_tp=105,
        current_rsi=65, vol_ratio=2.3,
    )
    assert should is False
    assert "RSI 65" in reason


def test_no_raise_when_vol_below_1_8():
    should, _, reason = should_raise_tp(
        entry=100, current_price=107, current_tp=105,
        current_rsi=75, vol_ratio=1.5,
    )
    assert should is False
    assert "vol 1.5" in reason


def test_no_raise_when_rsi_is_none():
    should, _, _ = should_raise_tp(
        entry=100, current_price=107, current_tp=105,
        current_rsi=None, vol_ratio=2.3,
    )
    assert should is False


def test_no_raise_when_vol_is_none():
    should, _, _ = should_raise_tp(
        entry=100, current_price=107, current_tp=105,
        current_rsi=75, vol_ratio=None,
    )
    assert should is False


# ═══ Cooldown logic ═══

def test_cooldown_blocks_recent_raise():
    """Raised 30min ago → cooldown blocks (default 60min)."""
    now = datetime(2026, 5, 1, 14, 30)
    last = (now - timedelta(minutes=30)).isoformat()
    should, _, reason = should_raise_tp(
        entry=100, current_price=107, current_tp=105,
        current_rsi=75, vol_ratio=2.3,
        last_raise_iso=last, now=now,
    )
    assert should is False
    assert "cooldown" in reason


def test_cooldown_passes_after_60min():
    """Raised 90min ago → cooldown passed."""
    now = datetime(2026, 5, 1, 14, 30)
    last = (now - timedelta(minutes=90)).isoformat()
    should, _, _ = should_raise_tp(
        entry=100, current_price=107, current_tp=105,
        current_rsi=75, vol_ratio=2.3,
        last_raise_iso=last, now=now,
    )
    assert should is True


# ═══ Audit JSON helpers ═══

def test_append_raise_audit_to_empty():
    """Append to empty/null JSON → creates first entry."""
    now = datetime(2026, 5, 1, 14, 30)
    result = append_raise_audit("", new_tp=112.35, reason="test", now=now)
    history = json.loads(result)
    assert len(history) == 1
    assert history[0]["new_tp"] == 112.35
    assert history[0]["reason"] == "test"


def test_append_multiple_raises_preserved():
    """Sequential raises accumulate in order."""
    s1 = append_raise_audit("[]", 110.0, "first", now=datetime(2026, 5, 1, 14, 0))
    s2 = append_raise_audit(s1, 115.0, "second", now=datetime(2026, 5, 1, 15, 0))
    h = json.loads(s2)
    assert len(h) == 2
    assert h[0]["new_tp"] == 110.0
    assert h[1]["new_tp"] == 115.0


def test_last_raise_ts_returns_most_recent():
    s = append_raise_audit("[]", 110.0, "x", now=datetime(2026, 5, 1, 14, 0))
    s = append_raise_audit(s, 115.0, "y", now=datetime(2026, 5, 1, 15, 0))
    ts = last_raise_ts(s)
    assert ts == "2026-05-01T15:00:00"
