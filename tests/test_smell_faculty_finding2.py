"""Finding #2: smells must fire when data is in pick['scores'][...] (real main.py shape).

Before fix: smells read sig.get('rsi') or pick.get('rsi'). In real picks, those
values live in pick['scores']['rsi']. All 4 sniff functions silently returned
None, so 4 of 7 smells effectively didn't exist. The 'proactive smell'
architecture claim was partial fiction.
"""
from src.smell_faculty import (
    smell_extreme_rsi,
    smell_volume_spike,
    smell_gap_up,
    smell_low_liquidity,
    sniff,
)


# ─── Each smell must work with the REAL pick shape (scores nested) ───

def test_extreme_rsi_fires_from_scores_nested():
    """PR-A2 F1-3: RSI blowoff is now HIGH warning, not blocking.
    Detection from pick['scores']['rsi'] still works (Finding #2 contract)."""
    pick = {"ticker": "AAA", "scores": {"rsi": 86}}
    smell = smell_extreme_rsi(pick, {})
    assert smell is not None, "RSI 86 must trigger blowoff smell from pick['scores']['rsi']"
    assert smell.code == "rsi_blowoff"
    assert smell.severity == "HIGH"
    assert smell.blocking is False


def test_extreme_rsi_overbought_from_scores():
    pick = {"ticker": "BBB", "scores": {"rsi": 78}}
    smell = smell_extreme_rsi(pick, {})
    assert smell is not None
    assert smell.code == "rsi_overbought"
    assert smell.severity == "HIGH"


def test_volume_spike_fires_from_scores_nested():
    pick = {"ticker": "CCC", "scores": {"vol_ratio": 4.5}}
    smell = smell_volume_spike(pick, {})
    assert smell is not None, "vol_ratio 4.5 must trigger from pick['scores']['vol_ratio']"
    assert smell.code == "volume_extreme"


def test_gap_up_fires_from_scores_nested():
    pick = {"ticker": "DDD", "scores": {"gap_pct": 6.0}}
    smell = smell_gap_up(pick, {})
    assert smell is not None
    assert smell.code == "gap_up_chasing"


def test_gap_up_modest_from_scores():
    pick = {"ticker": "EEE", "scores": {"gap_pct": 3.5}}
    smell = smell_gap_up(pick, {})
    assert smell is not None
    assert smell.code == "gap_up_modest"


def test_low_liquidity_fires_from_scores_nested():
    pick = {"ticker": "FFF", "scores": {"avg_volume": 80_000}}
    smell = smell_low_liquidity(pick, {})
    assert smell is not None
    assert smell.code == "liquidity_critical"


def test_low_liquidity_fires_from_avg_daily_volume_alias():
    """yfinance uses 'avg_daily_volume' field name in fetch_info."""
    pick = {"ticker": "GGG", "avg_daily_volume": 300_000}
    smell = smell_low_liquidity(pick, {})
    assert smell is not None
    assert smell.code == "liquidity_low"


# ─── Backward compat: flat-dict and sig-dict still work ───

def test_extreme_rsi_still_works_flat_dict():
    pick = {"ticker": "X", "rsi": 86}
    assert smell_extreme_rsi(pick, {}) is not None


def test_extreme_rsi_still_works_from_sig():
    smell = smell_extreme_rsi({"ticker": "X"}, {"rsi": 86})
    assert smell is not None


# ─── Integration: sniff() finds the warnings on a real-shape pick ───

def test_sniff_finds_multiple_smells_on_real_pick_shape():
    real_pick = {
        "ticker": "RISKY",
        "entry": 100.0,
        "stop_loss": 99.5,  # tight stop
        "scores": {
            "rsi": 87,           # blowoff
            "vol_ratio": 5.2,    # extreme volume
            "gap_pct": 7.0,      # gap chasing
            "avg_volume": 80_000 # critical liquidity
        },
    }
    warnings = sniff(real_pick)
    codes = [w.code for w in warnings]
    # Must catch at least: rsi_blowoff, volume_extreme, gap_up_chasing, liquidity_critical, stop_too_tight
    expected = {"rsi_blowoff", "volume_extreme", "gap_up_chasing", "liquidity_critical", "stop_too_tight"}
    found = set(codes)
    missing = expected - found
    assert not missing, f"sniff() missed: {missing}. Got: {codes}"
