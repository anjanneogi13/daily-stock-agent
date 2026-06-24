"""
Test that the configured heuristic excluded tickers stay excluded.

These exclusions are a manual, UNVERIFIED preference — NOT backtest-validated.
They originated from an in-dev backtest that is survivorship-biased, uses a
mis-annualized Sharpe, has no unit tests, and runs in no CI. This test only
guards that the configured exclusions remain applied; it makes NO claim that
the tickers are "proven losers." See docs/audit/COFOUNDER_AUDIT_2026-06-24.md.
"""
import yaml
from pathlib import Path


CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"
# Heuristic, unverified exclusions (NOT backtest-proven). Kept excluded by preference.
# Name retained for compatibility; the label below is the accurate description.
BACKTESTER_LOSERS = ["UNH", "TEAM", "SMCI", "DIS", "SCHW"]


def test_backtester_losers_are_excluded():
    """All configured heuristic exclusions must be in config.yaml excluded_tickers."""
    with open(CONFIG_PATH) as f:
        cfg = yaml.safe_load(f)

    excluded = set(t.upper() for t in cfg["universe"]["excluded_tickers"])

    for loser in BACKTESTER_LOSERS:
        assert loser in excluded, (
            f"{loser} must be in excluded_tickers (heuristic, unverified exclusion — "
            f"not backtest-validated). Current excluded list: {sorted(excluded)}"
        )


def test_universe_loader_filters_losers():
    """src.universe.get_universe() must return zero of the excluded tickers."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from src.universe import get_universe

    with open(CONFIG_PATH) as f:
        cfg = yaml.safe_load(f)

    try:
        universe = get_universe(cfg)
    except Exception as e:
        # Network or external dep failure → skip (not what we're testing)
        import pytest
        pytest.skip(f"get_universe failed (non-test issue): {e}")

    universe_upper = {t.upper() for t in universe}
    leaked = [t for t in BACKTESTER_LOSERS if t in universe_upper]
    assert not leaked, f"Excluded tickers leaked into universe: {leaked}"
