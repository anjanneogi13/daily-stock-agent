"""Tests for Monster Hunt Mode v0.1."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.monster_hunt import score_monster, apply_monster_treatment


# ═══════════════════════════════════════════════════════════════
# Scoring tests
# ═══════════════════════════════════════════════════════════════
def test_zero_signals_returns_zero():
    r = score_monster(composite=0.5, days_to_earnings=None,
                      short_pct_of_float=None, float_shares=None,
                      vol_ratio=None, has_bullish_news=False)
    assert r["monster_score"] == 0.0
    assert r["is_monster"] is False


def test_full_monster_caps_at_one():
    r = score_monster(composite=0.95, days_to_earnings=3,
                      short_pct_of_float=0.20, float_shares=30_000_000,
                      vol_ratio=2.5, has_bullish_news=True)
    assert r["monster_score"] >= 0.60
    assert r["is_monster"] is True
    assert r["monster_score"] <= 1.0


def test_threshold_boundary():
    """earnings(0.20) + rvol(0.15) + short(0.20) + combo(0.05) = 0.60 → monster."""
    r = score_monster(composite=0.7, days_to_earnings=5,
                      short_pct_of_float=0.18, float_shares=None,
                      vol_ratio=2.0, has_bullish_news=False)
    assert r["monster_score"] == 0.60
    assert r["is_monster"] is True


def test_just_below_threshold():
    """Only earnings + RVOL + combo = 0.40 → NOT monster."""
    r = score_monster(composite=0.7, days_to_earnings=5,
                      short_pct_of_float=None, float_shares=None,
                      vol_ratio=2.0, has_bullish_news=False)
    assert r["monster_score"] == 0.40
    assert r["is_monster"] is False


def test_reasons_human_readable():
    r = score_monster(composite=0.9, days_to_earnings=2,
                      short_pct_of_float=0.18, float_shares=40_000_000,
                      vol_ratio=2.0, has_bullish_news=True)
    text = " ".join(r["monster_reasons"])
    assert "earnings" in text
    assert "short" in text


# ═══════════════════════════════════════════════════════════════
# Treatment tests
# ═══════════════════════════════════════════════════════════════
def test_non_monster_unchanged():
    pick = {"ticker": "X", "entry": 100.0, "stop_loss": 97.0,
            "take_profit": 106.0, "qty": 50}
    out = apply_monster_treatment(pick.copy(), monster_score=0.4)
    assert out["stop_loss"] == 97.0
    assert out["take_profit"] == 106.0
    assert out["qty"] == 50
    assert out["is_monster"] is False


def test_monster_widens_sl_and_tp():
    pick = {"ticker": "X", "entry": 100.0, "stop_loss": 97.0,
            "take_profit": 106.0, "qty": 50}
    out = apply_monster_treatment(pick.copy(), monster_score=0.75,
                                   account_size=10000.0)
    assert out["stop_loss"] == 95.0      # 5% wider
    assert out["take_profit"] == 125.0   # 25% target
    assert out["is_monster"] is True
    # Lottery sizing: $150 risk / $5 stop = 30 qty (vs original 50)
    assert out["qty"] == 30
    # Originals preserved for audit
    assert out["original_sl_pre_monster"] == 97.0
    assert out["original_tp_pre_monster"] == 106.0
