"""Tests for the Smell faculty — proactive danger detection."""
from src.smell_faculty import (
    sniff, has_blocking_smell, format_for_telegram,
    smell_earnings_imminent, smell_extreme_rsi, smell_volume_spike,
    smell_gap_up, smell_low_liquidity, smell_tight_stop,
)


# ── earnings ──
def test_earnings_tomorrow_warns_critical_but_does_not_block():
    """PR-A2 F1-2: suggestion-only — show CRITICAL warning, user decides."""
    s = smell_earnings_imminent({"days_to_earnings": 1}, {})
    assert s and s.severity == "CRITICAL" and not s.blocking


def test_earnings_in_5_days_warns_med():
    s = smell_earnings_imminent({"days_to_earnings": 5}, {})
    assert s and s.severity == "MED" and not s.blocking


def test_earnings_far_away_no_smell():
    assert smell_earnings_imminent({"days_to_earnings": 30}, {}) is None


def test_earnings_none_no_smell():
    assert smell_earnings_imminent({"days_to_earnings": None}, {}) is None
    assert smell_earnings_imminent({}, {}) is None


# ── RSI ──
def test_rsi_blowoff_warns_high_but_does_not_block():
    """PR-A2 F1-3: NVDA/AVGO routinely run RSI 85-95. Warn, don't block."""
    s = smell_extreme_rsi({}, {"rsi": 88})
    assert s and s.severity == "HIGH" and not s.blocking


def test_rsi_overbought_warns():
    s = smell_extreme_rsi({}, {"rsi": 78})
    assert s and not s.blocking


def test_rsi_normal_no_smell():
    assert smell_extreme_rsi({}, {"rsi": 55}) is None


# ── volume ──
def test_volume_spike_warns():
    s = smell_volume_spike({}, {"vol_ratio": 5.0})
    assert s and s.severity == "HIGH"


def test_volume_normal_no_smell():
    assert smell_volume_spike({}, {"vol_ratio": 1.2}) is None


# ── gap ──
def test_gap_up_warns():
    s = smell_gap_up({}, {"gap_pct": 6.0})
    assert s and s.severity == "HIGH"


# ── liquidity ──
def test_liquidity_critical_blocks():
    s = smell_low_liquidity({}, {"avg_volume": 50_000})
    assert s and s.blocking


def test_liquidity_normal_no_smell():
    assert smell_low_liquidity({}, {"avg_volume": 5_000_000}) is None


# ── tight stop ──
def test_tight_stop_warns():
    s = smell_tight_stop({"entry": 100, "stop_loss": 99.5}, {})
    assert s and s.severity == "HIGH"


def test_normal_stop_no_smell():
    assert smell_tight_stop({"entry": 100, "stop_loss": 97}, {}) is None


# ── registry ──
def test_sniff_returns_sorted_by_severity():
    pick = {"days_to_earnings": 1, "entry": 100, "stop_loss": 99.5}
    sig = {"rsi": 88, "vol_ratio": 5.0}
    warnings = sniff(pick, sig)
    assert len(warnings) >= 3
    severities = [w.severity for w in warnings]
    # CRITICAL must come before HIGH
    assert severities.index("CRITICAL") < severities.index("HIGH")


def test_has_blocking_smell_finds_blocker():
    """PR-A2: earnings/rsi no longer block. Liquidity_critical still does."""
    pick = {"days_to_earnings": 1}
    sig = {"avg_volume": 50_000}  # liquidity_critical IS still blocking (F1-4 KEEP)
    blocker = has_blocking_smell(pick, sig)
    assert blocker is not None
    assert blocker.code == "liquidity_critical"


def test_has_blocking_smell_returns_none_for_clean_pick():
    pick = {"days_to_earnings": 30, "entry": 100, "stop_loss": 95}
    sig = {"rsi": 55, "vol_ratio": 1.2, "avg_volume": 5_000_000}
    assert has_blocking_smell(pick, sig) is None


def test_clean_pick_no_smells():
    pick = {"days_to_earnings": 30, "entry": 100, "stop_loss": 95}
    sig = {"rsi": 55, "vol_ratio": 1.2, "avg_volume": 5_000_000, "gap_pct": 0.3}
    assert sniff(pick, sig) == []


def test_format_for_telegram_empty_returns_empty():
    assert format_for_telegram([]) == ""


def test_format_for_telegram_renders_warnings():
    pick = {"days_to_earnings": 1}
    out = format_for_telegram(sniff(pick, {}))
    assert "Smell-test warnings" in out
    assert "Earnings in 1 day" in out


def test_broken_smell_doesnt_crash_sniff():
    """If a smell function raises, sniff should skip it gracefully."""
    pick = {"entry": "garbage", "days_to_earnings": "broken"}
    # Should not raise
    sniff(pick, {})
