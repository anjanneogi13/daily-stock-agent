"""Tests for Pillar 1 Layer 4 — hypothesis engine + signal journal."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.signal_journal import (
    bucket_composite, bucket_d2e, bucket_vol, bucket_monster,
    bucket_p_win, primary_tag, build_signals,
)
from src.hypothesis_engine import (
    analyze, two_sided_p_value, format_report, MIN_SAMPLE_SIZE,
)


# ═══════════════════════════════════════════════════════════════
# Bucketing
# ═══════════════════════════════════════════════════════════════
def test_bucket_composite():
    assert bucket_composite(None) == "unknown"
    assert bucket_composite(0.5) == "low"
    assert bucket_composite(0.7) == "mid"
    assert bucket_composite(0.84) == "mid"
    assert bucket_composite(0.85) == "high"
    assert bucket_composite(0.99) == "high"


def test_bucket_d2e():
    assert bucket_d2e(None) == "none"
    assert bucket_d2e("") == "none"
    assert bucket_d2e(2) == "imminent"
    assert bucket_d2e(7) == "near"
    assert bucket_d2e(30) == "far"


def test_bucket_monster():
    assert bucket_monster(None) == "none"
    assert bucket_monster(0.0) == "none"
    assert bucket_monster(0.45) == "mid"
    assert bucket_monster(0.7) == "monster"


def test_primary_tag_compound():
    assert primary_tag("SEMI / AI") == "SEMI"
    assert primary_tag("ai") == "AI"
    assert primary_tag(None) == "none"


def test_build_signals_smoke():
    pick = {
        "ticker": "NVDA", "regime": "bull", "trade_type": "swing",
        "days_to_earnings": 5, "vol_ratio": 2.1,
        "scores": {"composite": 0.88, "monster_score": 0.7, "sector_tag": "SEMI"},
        "brain": {"p_win": 0.62},
    }
    s = build_signals(pick)
    assert s["composite_score_bucket"] == "high"
    assert s["regime"] == "bull"
    assert s["tag"] == "SEMI"
    assert s["days_to_earnings_bucket"] == "near"
    assert s["vol_ratio_bucket"] == "high"
    assert s["monster_score_bucket"] == "monster"
    assert s["brain_p_win_bucket"] == "high"
    assert s["trade_type"] == "swing"


# ═══════════════════════════════════════════════════════════════
# Binomial p-value
# ═══════════════════════════════════════════════════════════════
def test_pvalue_at_base_rate_is_high():
    """If observed exactly equals expectation, p-value should be ~1.0."""
    p = two_sided_p_value(wins=5, n=10, base_rate=0.5)
    assert p > 0.5


def test_pvalue_huge_deviation_is_low():
    """20/20 wins with 50% base rate → very significant."""
    p = two_sided_p_value(wins=20, n=20, base_rate=0.5)
    assert p < 0.001


def test_pvalue_zero_n_safe():
    assert two_sided_p_value(0, 0, 0.5) == 1.0


# ═══════════════════════════════════════════════════════════════
# analyze() integration
# ═══════════════════════════════════════════════════════════════
def test_analyze_empty():
    r = analyze([])
    assert r["total_n"] == 0
    assert r["edges"] == []


def test_analyze_finds_edge():
    """Build 30 closed rows where regime=bull wins 100% of 15 picks."""
    rows = []
    # 15 winners, all regime=bull, tag=SEMI
    for i in range(15):
        rows.append({
            "outcome": "win",
            "r_multiple": 1.5,
            "signals": {"regime": "bull", "tag": "SEMI"},
        })
    # 15 losers, all regime=bear
    for i in range(15):
        rows.append({
            "outcome": "loss",
            "r_multiple": -1.0,
            "signals": {"regime": "bear", "tag": "OTHER"},
        })
    r = analyze(rows, min_n=10, alpha=0.05)
    assert r["total_n"] == 30
    assert r["base_rate"] == 0.5
    edge_signals = {(e["signal"], e["bucket"]) for e in r["edges"]}
    drag_signals = {(d["signal"], d["bucket"]) for d in r["drags"]}
    assert ("regime", "bull") in edge_signals
    assert ("regime", "bear") in drag_signals


def test_analyze_low_sample_skipped():
    """Buckets with n < min_n go to low_sample, not edges/drags."""
    rows = [{"outcome": "win", "r_multiple": 1.0,
             "signals": {"regime": "bull"}} for _ in range(5)]
    r = analyze(rows, min_n=10)
    assert r["edges"] == []
    assert any(ls["signal"] == "regime" for ls in r["low_sample"])


def test_format_report_runs():
    r = analyze([
        {"outcome": "win", "r_multiple": 1.0, "signals": {"regime": "bull"}},
    ])
    text = format_report(r)
    assert "HYPOTHESIS REVIEW" in text
    assert "OBSERVE-MODE" in text
