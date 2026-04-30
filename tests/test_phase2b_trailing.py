"""Phase 2B.2 — trailing stop engine tests."""
import sys, csv, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.trailing_stop import compute_trailing_sl, trail_status


# ═══ compute_trailing_sl: activation logic ═══

def test_no_activation_below_threshold():
    """Peak gain <3% → no trailing, SL stays at original."""
    new_sl, raised = compute_trailing_sl(entry=100, peak_price=102, current_sl=95)
    assert new_sl == 95
    assert raised is False


def test_activation_at_exactly_3pct():
    """Peak exactly 3% above entry → trail activates."""
    # peak=103, trail 2% below = 100.94
    new_sl, raised = compute_trailing_sl(entry=100, peak_price=103, current_sl=95)
    assert new_sl == 100.94
    assert raised is True


def test_sl_only_moves_up_never_down():
    """If candidate SL < current SL, no change."""
    # peak=110, candidate = 110*0.98 = 107.8
    # current_sl = 108 (already higher) → should stay at 108
    new_sl, raised = compute_trailing_sl(entry=100, peak_price=110, current_sl=108)
    assert new_sl == 108
    assert raised is False


def test_trail_follows_new_highs():
    """As peak rises, SL rises proportionally."""
    # peak=105 → SL = 102.9
    sl1, _ = compute_trailing_sl(entry=100, peak_price=105, current_sl=95)
    assert sl1 == 102.9
    # peak=110 → SL = 107.8 (raised)
    sl2, raised = compute_trailing_sl(entry=100, peak_price=110, current_sl=sl1)
    assert sl2 == 107.8
    assert raised is True


def test_custom_activation_and_trail_pct():
    """5% activation, 3% trail."""
    # peak=104 (4% gain) → no activation (<5%)
    sl, raised = compute_trailing_sl(100, 104, 95, activation_pct=5.0, trail_pct=3.0)
    assert sl == 95 and raised is False
    # peak=106 (6%) → SL = 106*0.97 = 102.82
    sl, raised = compute_trailing_sl(100, 106, 95, activation_pct=5.0, trail_pct=3.0)
    assert sl == 102.82 and raised is True


# ═══ Edge cases ═══

def test_peak_equals_entry():
    """Peak == entry → no gain, no trail."""
    sl, raised = compute_trailing_sl(entry=100, peak_price=100, current_sl=95)
    assert sl == 95 and raised is False


def test_peak_below_entry():
    """Peak below entry (losing) → no trail."""
    sl, raised = compute_trailing_sl(entry=100, peak_price=95, current_sl=90)
    assert sl == 90 and raised is False


def test_invalid_entry_returns_unchanged():
    """entry=0 → safe, returns current_sl unchanged."""
    sl, raised = compute_trailing_sl(entry=0, peak_price=100, current_sl=95)
    assert sl == 95 and raised is False


# ═══ trail_status ═══

def test_trail_status_active_flag():
    """current_sl > original_sl → active=True."""
    s = trail_status(entry=100, peak_price=108, current_sl=105, original_sl=95)
    assert s["active"] is True
    assert s["peak_gain_pct"] == 8.0
    assert s["locked_gain_pct"] == 5.0


def test_trail_status_inactive_when_sl_unchanged():
    """current_sl == original_sl → active=False."""
    s = trail_status(entry=100, peak_price=102, current_sl=95, original_sl=95)
    assert s["active"] is False
    assert s["peak_gain_pct"] == 2.0
