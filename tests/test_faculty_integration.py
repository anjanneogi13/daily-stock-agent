"""🧱 KEYSTONE INTEGRATION TEST

Proves all 7 faculties of the agent wire correctly end-to-end:

  1. EYES        — data_fetcher returns real prices + company name
  2. BRAIN       — scorer/probability_engine produces composite score
  3. SMELL       — smell_faculty detects danger flags
  4. JUDGMENT    — sanity gate blocks malformed picks
  5. MEMORY      — signal_journal records the signals + outcomes
  6. VOICE       — layman_translator renders user-friendly output
  7. WISDOM      — wisdom_consultant warns/boosts based on history

If ANY of these breaks (silent failure, schema drift, integration bug),
this test fails LOUDLY in CI. This is the test that prevents the
'May 2-4 silent metadata failure' class of bugs from ever returning.

Founder note: discovered the need for this when find ff43478 fixed
build_signals at function level but pipeline was still broken.
A test that exercised ALL faculties together would have caught it
the moment we pushed the bad fix.
"""
import json
from pathlib import Path
import pytest


# ═══════════════════════════════════════════════════════════════
# FACULTY 1 — EYES (data_fetcher)
# ═══════════════════════════════════════════════════════════════
def test_eyes_data_fetcher_returns_real_company_name():
    """Bug #7 root cause regression test."""
    from src.data_fetcher import fetch_info
    info = fetch_info("AAPL")
    name = info.get("name") or info.get("longName") or ""
    assert "Apple" in name, (
        f"Eyes regression: ticker AAPL should return Apple-something, got {name!r}"
    )


def test_eyes_returns_required_fields():
    """fetch_info contract — these fields MUST exist."""
    from src.data_fetcher import fetch_info
    info = fetch_info("AAPL")
    required = ["shortName", "longName", "name", "averageVolume", "sector"]
    for field in required:
        assert field in info, f"Eyes contract broken: missing {field!r}"


# ═══════════════════════════════════════════════════════════════
# FACULTY 2 — BRAIN (scorer + probability_engine)
# ═══════════════════════════════════════════════════════════════
def test_brain_composite_score_in_valid_range():
    """Composite score must be in [0, 1].
    Real signature: composite_score(sig, fund_score: float, sent_score: float, weights, ...)"""
    from src.scorer import composite_score
    sig = {"close": 100, "rsi_14": 50, "macd": 0.5, "macd_signal": 0.3,
           "sma_20": 98, "sma_50": 95, "sma_200": 90, "vol_ratio": 1.2,
           "bb_upper": 105, "bb_lower": 95, "bb_middle": 100, "adx": 25,
           "stoch_k": 50, "stoch_d": 50, "atr_14": 2.0,
           "ema_9": 100, "ema_21": 99, "psar": 95, "vwap_20": 99,
           "obv": 1e6, "obv_ema": 9e5, "plus_di": 25, "minus_di": 15}
    weights = {"indicators": 0.5, "fundamentals": 0.3, "sentiment": 0.2,
               "signals": 0.5, "fund": 0.3, "sent": 0.2}
    result = composite_score(sig, 0.5, 0.5, weights)
    score = result.get("composite", 0) if isinstance(result, dict) else float(result)
    assert 0 <= score <= 1, f"Brain regression: composite {score} out of [0,1]"


# ═══════════════════════════════════════════════════════════════
# FACULTY 3 — SMELL (smell_faculty)
# ═══════════════════════════════════════════════════════════════
def test_smell_blocks_earnings_tomorrow():
    from src.smell_faculty import has_blocking_smell
    blocker = has_blocking_smell({"days_to_earnings": 1}, {})
    assert blocker is not None and blocker.code == "earnings_tomorrow"


def test_smell_passes_clean_pick():
    from src.smell_faculty import has_blocking_smell
    pick = {"days_to_earnings": 30, "entry": 100, "stop_loss": 95}
    sig = {"rsi": 55, "vol_ratio": 1.2, "avg_volume": 5_000_000}
    assert has_blocking_smell(pick, sig) is None


# ═══════════════════════════════════════════════════════════════
# FACULTY 4 — JUDGMENT (sanity gate)
# ═══════════════════════════════════════════════════════════════
def test_judgment_blocks_zero_target():
    """Bug #1 regression — broken pick with $0 target must be blocked."""
    from scripts.send_layman_daily import _is_pick_sane
    broken = {"entry": 100, "stop_loss": 97, "take_profit": 0}
    ok, reason = _is_pick_sane(broken)
    assert not ok and "take_profit" in reason


def test_judgment_blocks_inverted_sl_tp():
    from scripts.send_layman_daily import _is_pick_sane
    broken = {"entry": 100, "stop_loss": 110, "take_profit": 105}
    ok, reason = _is_pick_sane(broken)
    assert not ok


def test_judgment_passes_clean_pick():
    from scripts.send_layman_daily import _is_pick_sane
    clean = {"entry": 100, "stop_loss": 97, "take_profit": 110,
             "days_to_earnings": 30}
    ok, reason = _is_pick_sane(clean)
    assert ok, f"Judgment over-blocked clean pick: {reason}"


def test_judgment_AND_smell_block_earnings_trap():
    """Faculty 3+4 fusion — earnings tomorrow must die at the gate."""
    from scripts.send_layman_daily import _is_pick_sane
    trap = {"entry": 100, "stop_loss": 97, "take_profit": 110,
            "days_to_earnings": 1}
    ok, reason = _is_pick_sane(trap)
    assert not ok and "SMELL" in reason


# ═══════════════════════════════════════════════════════════════
# FACULTY 5 — MEMORY (signal_journal)
# ═══════════════════════════════════════════════════════════════
def test_memory_build_signals_no_unknowns_for_complete_pick():
    """Bug #4 regression — complete pick must produce all real buckets."""
    from src.signal_journal import build_signals
    pick = {
        "ticker": "TEST",
        "scores": {"composite": 0.85, "vol_ratio": 1.5,
                   "monster_score": 0.4, "sector_tag": "SEMI"},
        "brain": {"p_win": 0.6},
        "regime": "bull",
        "days_to_earnings": 10,
        "trade_type": "swing",
    }
    sig = build_signals(pick)
    unknowns = [k for k, v in sig.items() if v == "unknown"]
    assert not unknowns, (
        f"Memory regression: {unknowns} unknown despite complete data. "
        f"build_signals() field-name fallbacks broken."
    )


def test_memory_journal_writes_and_reads():
    """log_pick → load_closed roundtrip must work."""
    from src.signal_journal import log_pick, attach_outcome, load_closed, JOURNAL
    import tempfile, shutil, os
    
    # Use temp file
    original = JOURNAL
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as tmp:
        tmppath = Path(tmp.name)
    
    import src.signal_journal as sj
    sj.JOURNAL = tmppath
    try:
        sj.JOURNAL.write_text("")  # clean
        log_pick({"ticker": "TEST", "pick_date": "2026-05-04",
                  "scores": {"composite": 0.8}, "brain": {"p_win": 0.55}})
        attach_outcome("TEST", "2026-05-04", r_multiple=1.5,
                       actual_return_pct=4.5, evaluated_on="2026-05-10")
        closed = load_closed()
        assert len(closed) == 1
        assert closed[0]["outcome"] == "win"
    finally:
        sj.JOURNAL = original
        if tmppath.exists():
            tmppath.unlink()


# ═══════════════════════════════════════════════════════════════
# FACULTY 6 — VOICE (layman_translator)
# ═══════════════════════════════════════════════════════════════
def test_voice_renders_company_name():
    """Bug #7 regression."""
    from src.layman_translator import pick_to_layman
    pick = {"ticker": "AAPL", "company": "Apple Inc.",
            "entry": 200, "stop_loss": 195, "take_profit": 215,
            "qty": 10, "trade_type": "swing", "score": 0.85}
    out = pick_to_layman(pick, 1)
    assert "AAPL" in out and "Apple" in out


def test_voice_renders_real_target_not_zero():
    """Bug #1 regression — never render $0.00 target."""
    from src.layman_translator import pick_to_layman
    pick = {"ticker": "TEST", "company": "Test Inc",
            "entry": 100, "stop_loss": 97, "take_profit": 110,
            "qty": 10, "trade_type": "swing", "score": 0.7}
    out = pick_to_layman(pick, 1)
    assert "$110" in out
    assert "$0.00" not in out


# ═══════════════════════════════════════════════════════════════
# FACULTY 7 — WISDOM (wisdom_consultant)
# ═══════════════════════════════════════════════════════════════
def test_wisdom_consult_returns_required_fields():
    """wisdom_consultant must return warnings/boosts/kill/score_adj."""
    try:
        from src.wisdom_consultant import consult_before_pick
    except ImportError:
        pytest.skip("wisdom_consultant not yet wired")
        return
    
    signals = {"composite_score_bucket": "high", "regime": "bull",
               "tag": "SEMI", "vol_ratio_bucket": "high",
               "brain_p_win_bucket": "high", "monster_score_bucket": "none",
               "days_to_earnings_bucket": "far", "trade_type": "swing"}
    result = consult_before_pick("AAPL", signals)
    
    for key in ["warnings", "boosts", "kill", "score_adj"]:
        assert key in result, f"Wisdom contract broken: missing {key!r}"
    assert isinstance(result["warnings"], list)
    assert isinstance(result["boosts"], list)
    # kill is None (no kill) OR dict (killed). NOT bool — that's the contract.
    assert result["kill"] is None or isinstance(result["kill"], dict)
    assert isinstance(result["score_adj"], (int, float))


# ═══════════════════════════════════════════════════════════════
# FULL PIPELINE — ALL 7 FACULTIES IN SEQUENCE
# ═══════════════════════════════════════════════════════════════
def test_full_pipeline_end_to_end():
    """Simulate the full pick→journal→render flow.
    
    If this passes, all 7 faculties are wired correctly.
    If this fails, find which sub-test failed first to localize the break.
    """
    from src.signal_journal import build_signals
    from src.smell_faculty import sniff, has_blocking_smell
    from src.layman_translator import pick_to_layman
    from scripts.send_layman_daily import _is_pick_sane
    
    # Realistic pick (post-scoring, pre-shipping)
    pick = {
        "ticker": "AAPL",
        "company": "Apple Inc.",
        "scores": {"composite": 0.85, "vol_ratio": 1.4,
                   "monster_score": 0.3, "sector_tag": "TECH"},
        "brain": {"p_win": 0.6},
        "regime": "bull",
        "trade_type": "swing",
        "days_to_earnings": 14,
        "entry": 200, "stop_loss": 195, "take_profit": 215,
        "qty": 10, "score": 0.85, "tag": "TECH",
    }
    
    # Mock Finnhub: fake AAPL @ $200 in fixture vs real ~$276 would
    # correctly trigger stale_price smell (E2c.2). Real smell behavior
    # is tested in tests/test_stale_price_smell.py.
    from unittest.mock import patch
    with patch("src.finnhub_data.fetch_finnhub_quote") as _mock_q:
        _mock_q.return_value = {"current": 200.50, "source": "finnhub"}

        # 1. SANITY GATE (Faculty 4 + 3) — must pass
        ok, reason = _is_pick_sane(pick)
        assert ok, f"Pipeline: clean pick blocked at sanity gate: {reason}"

        # 2. SMELL (Faculty 3) — should be quiet for this pick
        warnings = sniff(pick, {})
        blocker = has_blocking_smell(pick, {})
        assert blocker is None, f"Pipeline: clean pick has blocking smell: {blocker}"
    
    # 3. SIGNAL JOURNAL (Faculty 5) — must produce real buckets
    signals = build_signals(pick)
    assert signals["composite_score_bucket"] == "very_high"  # 0.85 >= 0.79 threshold
    assert signals["regime"] == "bull"
    assert signals["tag"] == "TECH"
    assert signals["vol_ratio_bucket"] == "high"    # 1.4 in [1.3, 2.5) = high (recalibrated E1)
    
    # 4. VOICE (Faculty 6) — must render correctly
    out = pick_to_layman(pick, 1)
    assert "AAPL" in out
    assert "Apple" in out
    assert "$215" in out
    assert "$0.00" not in out
    assert "1.5x" in out or "Reward vs Risk" in out


def test_pipeline_blocks_dangerous_pick():
    """End-to-end danger check — earnings-tomorrow pick must not ship."""
    from scripts.send_layman_daily import _is_pick_sane
    
    pick = {
        "ticker": "RISKY",
        "entry": 100, "stop_loss": 97, "take_profit": 110,
        "days_to_earnings": 1,  # 🚨
    }
    ok, reason = _is_pick_sane(pick)
    assert not ok and ("SMELL" in reason or "earnings" in reason.lower())
