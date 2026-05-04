"""F4: lock the picks_log <-> signal_journal consistency invariant.

Discovered May 4 2026: stores are in perfect sync (39/39). This test
locks that invariant. Future drift = silent journaling bug = test
breaks CI = forced investigation.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from scripts.audit_journal_consistency import audit, _load_picks_keys, _load_journal_keys


pytestmark = pytest.mark.skipif(
    not Path("data/picks_log.csv").exists(),
    reason="data/picks_log.csv not present in this environment"
)


def test_audit_returns_expected_shape():
    r = audit()
    assert "picks_count" in r
    assert "journal_count" in r
    assert "in_picks_only" in r
    assert "in_journal_only" in r
    assert "in_both" in r


def test_no_picks_missing_from_journal():
    """Every pick MUST be journaled. Missing entries = silent log_pick failure."""
    r = audit()
    if r["picks_count"] == 0:
        pytest.skip("empty picks_log")
    missing = r["in_picks_only"]
    assert not missing, (
        f"{len(missing)} picks missing from signal_journal — "
        f"main.py log_pick() may have failed silently:\n"
        + "\n".join(f"    {d}  {t}" for t, d in missing[:5])
    )


def test_no_orphan_journal_entries():
    """Every journal entry MUST have a backing pick row."""
    r = audit()
    if r["journal_count"] == 0:
        pytest.skip("empty journal")
    orphans = r["in_journal_only"]
    assert not orphans, (
        f"{len(orphans)} journal entries have no backing pick row — "
        f"someone deleted picks_log rows or journaled before logging:\n"
        + "\n".join(f"    {d}  {t}" for t, d in orphans[:5])
    )


def test_counts_match_when_both_present():
    """If both stores have data, sizes must match exactly."""
    r = audit()
    if r["picks_count"] == 0 or r["journal_count"] == 0:
        pytest.skip("one store empty")
    assert r["picks_count"] == r["journal_count"], (
        f"size mismatch: picks={r['picks_count']} journal={r['journal_count']}"
    )
