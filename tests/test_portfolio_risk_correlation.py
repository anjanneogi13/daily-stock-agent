"""Task 8 (COFOUNDER_AUDIT_2026-06-24 #28): 60-day return correlation guard.

Vision item #28 has two halves: sector/tag caps (already enforced) AND
"reject co-issued pairs whose 60-day return correlation > 0.7". This tests
the second half: among the day's finalists, if a candidate's daily-return
correlation with an ALREADY-ACCEPTED (higher-scored) finalist exceeds the
threshold, the lower-scored one is rejected.

Design decisions under test:
- POSITIVE-only: anti-correlated pairs (corr ~ -0.9) are diversifying, so they
  are NOT rejected. Only correlation > +threshold rejects.
- Greedy + score-ordered: the higher composite score is always the keeper.
- FAIL-OPEN on data: thin overlap or missing history => no rejection (this is
  an additive diversity filter; it must never zero-out a day on bad data).
- Config-gated: threshold >= 1.0 (or absent history) disables the guard.
- Backward compatible: price_history defaults to None => behaves exactly as the
  pre-Task-8 gate (no correlation rejections).
"""
import numpy as np
import pandas as pd
import pytest

from src.portfolio_risk_gate import apply_portfolio_risk_gate


def _cfg(max_corr=0.7, lookback=60):
    risk = {
        "account_size": 100000.0,
        "risk_per_trade_pct": 2.0,        # generous so per-trade risk never blocks
        "max_new_picks_per_day": 10,
        "max_per_sector": 10,             # disable sector cap for these tests
        "max_per_tag": 10,                # disable tag cap for these tests
        "min_risk_reward": 1.0,
    }
    if max_corr is not None:
        risk["max_pairwise_correlation"] = max_corr
    if lookback is not None:
        risk["corr_lookback_days"] = lookback
    return {"risk": risk}


def _candidate(ticker, score, *, sector="Tech", tag="AI",
               entry=100.0, sl=98.0, tp=106.0, qty=10):
    return {
        "ticker": ticker,
        "scores": {"composite": score, "sector_tag": tag},
        "info_short": {"sector": sector},
        "plan": {
            "entry": entry, "stop_loss": sl, "take_profit": tp,
            "quantity": qty, "risk_reward": (tp - entry) / (entry - sl),
        },
    }


def _series(closes):
    idx = pd.date_range("2026-01-01", periods=len(closes), freq="D")
    return pd.DataFrame({"Close": np.asarray(closes, dtype=float)}, index=idx)


def _price_history(**ticker_to_closes):
    return {tk: _series(c) for tk, c in ticker_to_closes.items()}


def _rng(seed):
    return np.random.default_rng(seed)


def _walk(n, seed, scale=1.0):
    """A random-walk close series of length n."""
    steps = _rng(seed).normal(0, 1, n) * scale
    return 100.0 + np.cumsum(steps)


def _tickers(blocked):
    return {b.get("ticker") for b in blocked}


def _corr_blocks(blocked):
    return [b for b in blocked if b.get("block_type") == "correlation"]


N = 80  # > 60 lookback, > 30 min-overlap


def test_highly_correlated_pair_rejects_lower_scored():
    base = _walk(N, seed=1)
    # AAA and BBB nearly identical => corr ~ 0.99
    aaa = base
    bbb = base + _rng(2).normal(0, 0.01, N)
    hist = _price_history(AAA=aaa, BBB=bbb)
    cands = [_candidate("AAA", 0.90), _candidate("BBB", 0.80)]

    allowed, blocked, summary = apply_portfolio_risk_gate(
        cands, _cfg(), price_history=hist
    )
    allowed_tk = {c["ticker"] for c in allowed}
    assert "AAA" in allowed_tk, "higher-scored AAA must be kept"
    assert "BBB" not in allowed_tk, "correlated lower-scored BBB must be rejected"
    cb = _corr_blocks(blocked)
    assert cb and cb[0]["ticker"] == "BBB"
    assert cb[0]["rejection_stage"] == "portfolio_risk"


def test_uncorrelated_pair_keeps_both():
    aaa = _walk(N, seed=10)
    bbb = _walk(N, seed=999)  # independent walk => corr ~ 0
    hist = _price_history(AAA=aaa, BBB=bbb)
    cands = [_candidate("AAA", 0.90), _candidate("BBB", 0.80)]
    allowed, blocked, _ = apply_portfolio_risk_gate(cands, _cfg(), price_history=hist)
    allowed_tk = {c["ticker"] for c in allowed}
    assert {"AAA", "BBB"} <= allowed_tk, "uncorrelated picks must both be kept"
    assert _corr_blocks(blocked) == []


def test_anti_correlated_pair_keeps_both():
    base = _walk(N, seed=20)
    aaa = base
    bbb = 200.0 - base  # mirror => returns corr ~ -1.0 (diversifying)
    hist = _price_history(AAA=aaa, BBB=bbb)
    cands = [_candidate("AAA", 0.90), _candidate("BBB", 0.80)]
    allowed, blocked, _ = apply_portfolio_risk_gate(cands, _cfg(), price_history=hist)
    allowed_tk = {c["ticker"] for c in allowed}
    assert {"AAA", "BBB"} <= allowed_tk, "anti-correlated picks must both be kept (positive-only guard)"
    assert _corr_blocks(blocked) == []


def test_thin_overlap_does_not_reject():
    # Only 10 common observations -> below min-overlap -> fail-open (keep both).
    base = _walk(10, seed=30)
    hist = _price_history(AAA=base, BBB=base.copy())  # identical but too short
    cands = [_candidate("AAA", 0.90), _candidate("BBB", 0.80)]
    allowed, blocked, _ = apply_portfolio_risk_gate(cands, _cfg(), price_history=hist)
    allowed_tk = {c["ticker"] for c in allowed}
    assert {"AAA", "BBB"} <= allowed_tk, "thin data must NOT trigger a correlation rejection"
    assert _corr_blocks(blocked) == []


def test_history_none_behaves_as_before():
    # No price_history -> guard disabled -> identical-by-construction picks both kept.
    cands = [_candidate("AAA", 0.90), _candidate("BBB", 0.80)]
    allowed, blocked, _ = apply_portfolio_risk_gate(cands, _cfg())  # no price_history
    allowed_tk = {c["ticker"] for c in allowed}
    assert {"AAA", "BBB"} <= allowed_tk
    assert _corr_blocks(blocked) == []


def test_threshold_disabled_keeps_identical_series():
    base = _walk(N, seed=40)
    hist = _price_history(AAA=base, BBB=base.copy())  # corr ~ 1.0
    cands = [_candidate("AAA", 0.90), _candidate("BBB", 0.80)]
    # threshold >= 1.0 disables the guard
    allowed, blocked, _ = apply_portfolio_risk_gate(
        cands, _cfg(max_corr=1.0), price_history=hist
    )
    allowed_tk = {c["ticker"] for c in allowed}
    assert {"AAA", "BBB"} <= allowed_tk, "threshold>=1.0 must disable the guard"
    assert _corr_blocks(blocked) == []
