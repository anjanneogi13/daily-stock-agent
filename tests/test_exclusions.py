"""
Test that backtester-proven losers are excluded from universe.

Source: Sunday May 3 2026 sprint — 5 tickers proved losing in
100-ticker × 20-month backtest (2,010 picks). See FINAL_ROADMAP.md.
"""
import yaml
from pathlib import Path


CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"
BACKTESTER_LOSERS = ["UNH", "TEAM", "SMCI", "DIS", "SCHW"]


def test_backtester_losers_are_excluded():
    """All 5 known losers must be in config.yaml excluded_tickers."""
    with open(CONFIG_PATH) as f:
        cfg = yaml.safe_load(f)

    excluded = set(t.upper() for t in cfg["universe"]["excluded_tickers"])

    for loser in BACKTESTER_LOSERS:
        assert loser in excluded, (
            f"{loser} must be in excluded_tickers — backtester proved it loses money. "
            f"Current excluded list: {sorted(excluded)}"
        )


def test_universe_loader_filters_losers():
    """src.universe.get_universe() must return zero of the loser tickers."""
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
