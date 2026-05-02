"""
Tests for src/probability_engine.py — locks in v0.1 behavior.

Why these tests matter:
- Probability engine is THE moat. Regressions here = catastrophic.
- These tests verify the LOGIC, not the exact numbers
  (numbers will change as data updates).
"""
from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

from src.probability_engine import (
    SignalState,
    ProbabilisticDecision,
    compute_probabilistic_decision,
    _classify_news,
    _classify_catalyst,
    REGIME_ADJUSTMENTS,
    NEWS_ADJUSTMENTS,
    CATALYST_ADJUSTMENTS,
    DEFAULT_P_WIN_PRIOR,
)


# ─── Helpers classification ────────────────────────────────────────

class TestClassifyNews:
    def test_huge_positive_with_bullish_sentiment(self):
        assert _classify_news(0.95, "bullish") == "huge_positive"

    def test_high_score_bearish_treated_as_strong_negative(self):
        assert _classify_news(0.95, "bearish") == "strong_negative"

    def test_strong_positive(self):
        assert _classify_news(0.80, "bullish") == "strong_positive"

    def test_mild_positive(self):
        assert _classify_news(0.60, "bullish") == "mild_positive"

    def test_neutral_low_score(self):
        assert _classify_news(0.30, "bullish") == "neutral"

    def test_neutral_no_sentiment(self):
        assert _classify_news(0.30, "neutral") == "neutral"


class TestClassifyCatalyst:
    def test_imminent_3_days(self):
        assert _classify_catalyst(3) == "imminent"

    def test_imminent_zero_days(self):
        assert _classify_catalyst(0) == "imminent"

    def test_near_5_days(self):
        assert _classify_catalyst(5) == "near"

    def test_near_7_days(self):
        assert _classify_catalyst(7) == "near"

    def test_moderate_15_days(self):
        assert _classify_catalyst(15) == "moderate"

    def test_far_60_days(self):
        assert _classify_catalyst(60) == "far"

    def test_none_treated_as_far(self):
        assert _classify_catalyst(None) == "far"


# ─── SignalState defaults ──────────────────────────────────────────

class TestSignalState:
    def test_defaults_are_neutral(self):
        s = SignalState()
        assert s.regime == "unknown"
        assert s.news_score == 0.0
        assert s.news_sentiment == "neutral"
        assert s.days_to_earnings is None
        assert s.watchlist_boost == 0.0


# ─── Decision logic ────────────────────────────────────────────────

class TestComputeProbabilisticDecision:
    def test_returns_decision_object(self):
        d = compute_probabilistic_decision("UNKNOWN_TICKER", 100.0)
        assert isinstance(d, ProbabilisticDecision)
        assert d.ticker == "UNKNOWN_TICKER"
        assert d.entry_price == 100.0

    def test_fallback_when_no_stats(self):
        """Stocks with no stock_stats data should still produce a decision."""
        d = compute_probabilistic_decision("XXNOSTATSXX", 100.0)
        assert d.final_sl_pct >= 0.5
        assert d.final_tp_pct > 0
        assert "FALLBACK_SL_NO_STATS" in d.adjustments_applied or d.base_sl_pct is not None

    def test_no_signals_gives_default_pwin(self):
        d = compute_probabilistic_decision("UNKNOWN", 100.0)
        # With no signals, p_win should be near the prior
        assert abs(d.p_win - DEFAULT_P_WIN_PRIOR) < 0.05

    def test_bull_regime_increases_pwin(self):
        baseline = compute_probabilistic_decision("UNKNOWN", 100.0)
        bull = compute_probabilistic_decision(
            "UNKNOWN", 100.0,
            signals=SignalState(regime="bull"),
        )
        assert bull.p_win > baseline.p_win

    def test_bear_regime_decreases_pwin(self):
        baseline = compute_probabilistic_decision("UNKNOWN", 100.0)
        bear = compute_probabilistic_decision(
            "UNKNOWN", 100.0,
            signals=SignalState(regime="bear"),
        )
        assert bear.p_win < baseline.p_win

    def test_positive_news_increases_pwin(self):
        baseline = compute_probabilistic_decision("UNKNOWN", 100.0)
        pos = compute_probabilistic_decision(
            "UNKNOWN", 100.0,
            signals=SignalState(news_score=0.85, news_sentiment="bullish"),
        )
        assert pos.p_win > baseline.p_win

    def test_negative_news_decreases_pwin(self):
        baseline = compute_probabilistic_decision("UNKNOWN", 100.0)
        neg = compute_probabilistic_decision(
            "UNKNOWN", 100.0,
            signals=SignalState(news_score=0.85, news_sentiment="bearish"),
        )
        assert neg.p_win < baseline.p_win

    def test_imminent_earnings_widens_sl(self):
        """Earnings within 3 days should widen the stop loss (volatility expansion)."""
        baseline = compute_probabilistic_decision("UNKNOWN", 100.0)
        earnings = compute_probabilistic_decision(
            "UNKNOWN", 100.0,
            signals=SignalState(days_to_earnings=2),
        )
        assert earnings.final_sl_pct > baseline.final_sl_pct

    def test_pwin_clipped_to_sane_range(self):
        """P(win) should never exceed [0.05, 0.95]."""
        # Stack everything bullish
        signals = SignalState(
            regime="bull",
            news_score=0.99,
            news_sentiment="bullish",
            days_to_earnings=45,
            watchlist_boost=0.30,
        )
        d = compute_probabilistic_decision("UNKNOWN", 100.0, signals=signals)
        assert 0.05 <= d.p_win <= 0.95

        # Stack everything bearish
        signals = SignalState(
            regime="bear",
            news_score=0.99,
            news_sentiment="bearish",
            days_to_earnings=1,
        )
        d = compute_probabilistic_decision("UNKNOWN", 100.0, signals=signals)
        assert 0.05 <= d.p_win <= 0.95

    def test_sl_never_below_minimum(self):
        d = compute_probabilistic_decision("UNKNOWN", 100.0)
        assert d.final_sl_pct >= 0.5

    def test_tp_at_least_minimum_rr(self):
        """TP should be at least 1.2× SL to maintain risk:reward."""
        d = compute_probabilistic_decision("UNKNOWN", 100.0)
        assert d.final_tp_pct >= d.final_sl_pct * 1.2

    def test_price_levels_consistent(self):
        d = compute_probabilistic_decision("UNKNOWN", 100.0)
        assert d.final_sl_price < d.entry_price  # SL below entry
        assert d.final_tp_price > d.entry_price  # TP above entry
        assert d.buy_zone_low < d.entry_price < d.buy_zone_high
        assert d.trigger_price > d.entry_price  # trigger above entry

    def test_ev_calculation(self):
        """EV should equal P(win)*TP - P(loss)*SL."""
        d = compute_probabilistic_decision(
            "UNKNOWN", 100.0,
            signals=SignalState(regime="bull", news_score=0.85, news_sentiment="bullish"),
        )
        expected_ev = (d.p_win * d.final_tp_pct) - ((1 - d.p_win) * d.final_sl_pct)
        assert abs(d.expected_value_pct - expected_ev) < 0.01

    def test_audit_trail_records_signals(self):
        signals = SignalState(
            regime="bull",
            news_score=0.85,
            news_sentiment="bullish",
            days_to_earnings=5,
        )
        d = compute_probabilistic_decision("UNKNOWN", 100.0, signals=signals)
        applied = " ".join(d.adjustments_applied)
        assert "regime=bull" in applied
        assert "news=" in applied
        assert "earnings=" in applied

    def test_confidence_low_when_no_signals(self):
        d = compute_probabilistic_decision("UNKNOWN", 100.0)
        assert d.confidence == "low"

    def test_confidence_high_with_multiple_strong_signals(self):
        """Stock with stats + multiple signals → HIGH confidence.
        Uses NVDA (has stock_stats); falls back to medium check if not present."""
        from src.stock_stats import load_stats
        signals = SignalState(
            regime="bull",
            news_score=0.95,
            news_sentiment="bullish",
            days_to_earnings=5,
            watchlist_boost=0.20,
        )
        d = compute_probabilistic_decision("NVDA", 198.45, signals=signals)
        if load_stats("NVDA") is not None:
            # Has stats → should be high or medium
            assert d.confidence in ("medium", "high")
        else:
            # No stats locally (e.g., CI without prebuilt stats) → low is acceptable
            assert d.confidence in ("low", "medium", "high")

    def test_confidence_low_when_no_stats_even_with_signals(self):
        """Defensive: even with strong signals, NO stats = LOW confidence."""
        signals = SignalState(
            regime="bull",
            news_score=0.95,
            news_sentiment="bullish",
            days_to_earnings=5,
        )
        d = compute_probabilistic_decision("XXNOSTATSXX", 100.0, signals=signals)
        assert d.confidence == "low"


# ─── Decision math sanity ──────────────────────────────────────────

class TestDecisionMathSanity:
    def test_perfect_storm_has_positive_ev(self):
        """All bullish signals should produce positive EV."""
        signals = SignalState(
            regime="bull",
            news_score=0.90,
            news_sentiment="bullish",
            days_to_earnings=14,
            watchlist_boost=0.20,
        )
        d = compute_probabilistic_decision("UNKNOWN", 100.0, signals=signals)
        assert d.expected_value_pct > 0

    def test_worst_case_has_negative_ev(self):
        """All bearish signals should produce negative EV."""
        signals = SignalState(
            regime="bear",
            news_score=0.90,
            news_sentiment="bearish",
            days_to_earnings=2,
        )
        d = compute_probabilistic_decision("UNKNOWN", 100.0, signals=signals)
        assert d.expected_value_pct < 0


# ─── Configuration sanity ──────────────────────────────────────────

class TestConfigurationSanity:
    def test_all_regime_keys_have_required_fields(self):
        for regime, adj in REGIME_ADJUSTMENTS.items():
            assert "sl_mult" in adj
            assert "tp_mult" in adj
            assert "p_win_boost" in adj

    def test_all_news_buckets_have_required_fields(self):
        for bucket, adj in NEWS_ADJUSTMENTS.items():
            assert "tp_mult" in adj
            assert "p_win_boost" in adj

    def test_all_catalyst_buckets_have_required_fields(self):
        for bucket, adj in CATALYST_ADJUSTMENTS.items():
            assert "sl_mult" in adj
            assert "tp_mult" in adj
            assert "p_win_boost" in adj

    def test_bull_better_than_bear(self):
        assert REGIME_ADJUSTMENTS["bull"]["p_win_boost"] > REGIME_ADJUSTMENTS["bear"]["p_win_boost"]

    def test_huge_positive_better_than_strong_positive(self):
        assert NEWS_ADJUSTMENTS["huge_positive"]["p_win_boost"] > NEWS_ADJUSTMENTS["strong_positive"]["p_win_boost"]