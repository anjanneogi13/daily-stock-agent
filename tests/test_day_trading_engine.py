"""Tests for day trading engine (PR #67)."""
import pytest
from src.day_trading_scorer import (
    day_trading_score, is_day_tradeable,
    _score_rvol, _score_atr_ratio, _score_intraday_momentum,
    _score_trend_alignment, _score_liquidity,
)
from src.market_guard import classify_trade_type, classify_with_day_score
from src.risk_manager import atr_trade_plan


# ═══════════════════════════════════════════════════════════════
# day_trading_scorer tests
# ═══════════════════════════════════════════════════════════════

def test_rvol_scoring():
    assert _score_rvol(2.5) == 1.00
    assert _score_rvol(1.5) == 0.85
    assert _score_rvol(1.0) == 0.50
    assert _score_rvol(0.5) == 0.15


def test_atr_ratio_sweet_spot():
    # 2% ATR/price ratio = ideal day trade
    assert _score_atr_ratio(2.0, 100.0) == 1.00
    # 0.5% = too quiet
    assert _score_atr_ratio(0.5, 100.0) == 0.30
    # 8% = too volatile
    assert _score_atr_ratio(8.0, 100.0) == 0.40


def test_atr_ratio_zero_handling():
    assert _score_atr_ratio(0, 100) == 0.30
    assert _score_atr_ratio(2, 0) == 0.30


def test_momentum_sweet_spot():
    # RSI 60 + positive MACD = ideal
    assert _score_intraday_momentum(60, 1.0) == 1.0
    # RSI 85 = exhausted (0.20 RSI score × 0.6 + 1.0 MACD × 0.4 = 0.52)
    assert _score_intraday_momentum(85, 1.0) < 0.55
    # RSI 30 = weak
    assert _score_intraday_momentum(30, -1.0) < 0.4


def test_trend_alignment_full_bullish():
    sig = {"close": 100, "ema_20": 95, "ema_50": 90, "vwap": 98}
    assert _score_trend_alignment(sig) == 1.0


def test_trend_alignment_bearish():
    sig = {"close": 90, "ema_20": 95, "ema_50": 100, "vwap": 92}
    assert _score_trend_alignment(sig) == 0.30


def test_liquidity_scoring():
    # $200M daily = max liquidity
    assert _score_liquidity(2_000_000, 100) == 1.00
    # $1M daily = too thin
    assert _score_liquidity(10_000, 100) == 0.15


def test_day_score_ideal_setup():
    """High RVOL + good ATR + bullish momentum + trend = high day score."""
    sig = {
        "close": 100, "atr_14": 2.0,  # 2% ATR
        "vol_ratio": 2.0,              # 2x volume
        "rsi_14": 62, "macd_hist": 0.8,
        "ema_20": 98, "ema_50": 95, "vwap": 99,
        "volume": 1_000_000,           # $100M daily
    }
    result = day_trading_score(sig)
    assert result["day_score"] >= 0.85
    assert "RVOL" in result["day_reason"] or "ATR" in result["day_reason"]


def test_day_score_weak_setup():
    """Low volume + flat momentum = low day score."""
    sig = {
        "close": 100, "atr_14": 0.5,
        "vol_ratio": 0.5, "rsi_14": 45, "macd_hist": -0.5,
        "ema_20": 102, "ema_50": 105, "vwap": 101,
        "volume": 50_000,
    }
    result = day_trading_score(sig)
    assert result["day_score"] < 0.5


def test_day_score_with_news_boost():
    """News catalyst should bump score."""
    sig = {
        "close": 100, "atr_14": 2.0, "vol_ratio": 1.5,
        "rsi_14": 60, "macd_hist": 0.5,
        "ema_20": 98, "ema_50": 95, "vwap": 99,
        "volume": 500_000,
    }
    no_news = day_trading_score(sig, news_boost=0)
    with_news = day_trading_score(sig, news_boost=0.10)
    assert with_news["day_score"] > no_news["day_score"]


def test_is_day_tradeable_threshold():
    assert is_day_tradeable(0.70) is True
    assert is_day_tradeable(0.65) is True
    assert is_day_tradeable(0.64) is False


# ═══════════════════════════════════════════════════════════════
# classify_trade_type tests (PR #67 fix)
# ═══════════════════════════════════════════════════════════════

def test_classify_returns_day_for_strong_intraday():
    """PR #67 FIX: realistic thresholds should return 'day'."""
    scores = {"momentum": 0.70, "volume": 0.60, "trend": 0.55}
    sig = {"close": 100, "atr_14": 2.0}  # 2% ATR
    assert classify_trade_type(scores, sig=sig, gap_pct=0.01) == "day"


def test_classify_returns_swing_for_low_momentum():
    scores = {"momentum": 0.40, "volume": 0.60, "trend": 0.65}
    assert classify_trade_type(scores) == "swing"


def test_classify_swing_for_huge_gap():
    """Big gap → not safe for day trade (gap-and-fade risk)."""
    scores = {"momentum": 0.80, "volume": 0.75, "trend": 0.65}
    sig = {"close": 100, "atr_14": 2.0}
    assert classify_trade_type(scores, sig=sig, gap_pct=0.06) == "swing"


def test_classify_swing_for_too_volatile():
    """ATR > 3.5% → too risky for day trade."""
    scores = {"momentum": 0.75, "volume": 0.70, "trend": 0.65}
    sig = {"close": 100, "atr_14": 5.0}  # 5% ATR
    assert classify_trade_type(scores, sig=sig) == "swing"


def test_classify_with_day_score_overrides():
    """High day_score should force 'day' classification."""
    scores = {"momentum": 0.50, "volume": 0.50, "trend": 0.55}  # marginal
    assert classify_with_day_score(scores, day_score=0.80) == "day"


def test_classify_with_day_score_low_falls_back():
    """Low day_score falls back to swing classifier."""
    scores = {"momentum": 0.50, "volume": 0.50, "trend": 0.55}
    assert classify_with_day_score(scores, day_score=0.40) == "swing"


# ═══════════════════════════════════════════════════════════════
# atr_trade_plan day-mode tightening (PR #67)
# ═══════════════════════════════════════════════════════════════

def test_day_trade_has_tight_stop():
    """PR #67: Day trades should have ~1% stop, not 3%+."""
    plan = atr_trade_plan(price=100.0, atr=2.0, capital=10000,
                          trade_type="day")
    sl_pct = (100.0 - plan["stop_loss"]) / 100.0 * 100
    # 0.6 × ATR(2.0) = 1.2 → stop at 98.8 → -1.2%
    assert sl_pct <= 1.5, f"Day trade stop too wide: {sl_pct:.2f}%"
    assert sl_pct >= 0.8, f"Day trade stop too tight: {sl_pct:.2f}%"


def test_day_trade_has_max_hold_minutes():
    """PR #67: Day trades must have force-close time."""
    plan = atr_trade_plan(price=100.0, atr=2.0, capital=10000,
                          trade_type="day")
    assert plan.get("max_hold_minutes") == 240


def test_swing_trade_no_max_hold():
    """Swing trades have no force-close."""
    plan = atr_trade_plan(price=100.0, atr=2.0, capital=10000,
                          trade_type="swing")
    assert plan.get("max_hold_minutes") is None


def test_day_trade_better_rr_than_old():
    """PR #67: New day-trade R:R should be 1.0+ (tp 1.0×ATR / sl 0.6×ATR)."""
    plan = atr_trade_plan(price=100.0, atr=2.0, capital=10000,
                          trade_type="day")
    assert plan["risk_reward"] >= 1.5, f"Day R:R too low: {plan['risk_reward']}"


def test_swing_trade_unchanged():
    """Swing trades should still use 2.0×ATR SL (backward compat)."""
    plan = atr_trade_plan(price=100.0, atr=2.0, capital=10000,
                          trade_type="swing")
    sl_pct = (100.0 - plan["stop_loss"]) / 100.0 * 100
    # 2.0 × ATR(2.0) = 4.0 → stop at 96.0 → -4.0%
    assert 3.5 <= sl_pct <= 4.5, f"Swing stop wrong: {sl_pct:.2f}%"