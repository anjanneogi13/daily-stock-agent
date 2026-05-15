"""PR-A7: 12 audit-confirmed bugs across 4 surgical files.

Audit refs (all from docs/audit/2026-05-12_FULL_REPO_AUDIT/):
- HB-22, HB-29, HB-12, HB-72: 14_parallel_scorer_and_hard_blocks.md
- DF-28, DF-45, DF-33:        19_data_fetcher_and_indicators.md
- PS-48, PS-49:               14_parallel_scorer_and_hard_blocks.md
- PRG-21:                     15_premarket_sanity_and_portfolio_risk_gates.md

Each test is a SOURCE-PATTERN GUARD so future refactors can't silently regress.
Functional tests added where cheap and safe.
"""
from pathlib import Path
import re


# ─── hard_blocks.py ───
def test_hb22_ai_tag_no_longer_maps_to_soxx():
    """HB-22: AI tag mapped to SOXX wrongly blocked META/MSFT/GOOGL."""
    src = Path("src/hard_blocks.py").read_text()
    # Find the TAG_ETF dict region
    import re as _re
    # Whitespace-insensitive: matches "AI": "QQQ" or "AI":    "QQQ"
    assert _re.search(r'"AI"\s*:\s*"QQQ"', src), (
        "HB-22 regression: AI tag must map to QQQ (broad tech), not SOXX"
    )
    assert not _re.search(r'"AI"\s*:\s*"SOXX"', src), (
        "HB-22 regression: 'AI' -> 'SOXX' must not be present anywhere"
    )


def test_hb12_csv_reader_handles_bom():
    """HB-12: utf-8 reader crashed on BOM → silently disabled cooldown."""
    src = Path("src/hard_blocks.py").read_text()
    assert "utf-8-sig" in src, (
        "HB-12 regression: csv reader must use utf-8-sig to handle BOM"
    )


def test_hb29_get_weak_sectors_has_real_cache():
    """HB-29: docstring promised cached but had none. Now has per-date cache."""
    src = Path("src/hard_blocks.py").read_text()
    assert "_WEAK_SECTORS_CACHE" in src, (
        "HB-29 regression: get_weak_sectors must have a real cache"
    )


def test_hb72_audit_log_retention_increased():
    """HB-72: keeping last 100 = 100 days of history. Increased to 1000."""
    src = Path("src/hard_blocks.py").read_text()
    assert "existing[-1000:]" in src, (
        "HB-72 regression: audit log retention must be 1000 entries"
    )
    assert "existing[-100:]" not in src, (
        "HB-72 regression: old 100-entry retention still present"
    )


# ─── data_fetcher.py ───
def test_df28_average_volume_default_not_1m():
    """DF-28: 1M default bypassed validation. Must now be None."""
    src = Path("src/data_fetcher.py").read_text()
    # The default in the info dict
    assert '"averageVolume": None' in src or "'averageVolume': None" in src, (
        "DF-28 regression: averageVolume default must be None"
    )
    # The `or 1_000_000` fallback must be gone
    assert "or 1_000_000" not in src, (
        "DF-28 regression: secondary `or 1_000_000` fallback still present"
    )


def test_df28_is_valid_market_data_rejects_none_volume():
    """DF-28: validation must explicitly reject None volume."""
    src = Path("src/data_fetcher.py").read_text()
    body = src[src.find("def is_valid_market_data"):]
    assert "averageVolume missing" in body or "vol is None" in body, (
        "DF-28 regression: is_valid_market_data must reject None volume"
    )


def test_df45_brk_a_threshold_raised():
    """DF-45: 100k threshold flagged BRK.A (~$700k) as suspicious."""
    src = Path("src/data_fetcher.py").read_text()
    assert "price > 1_000_000" in src, (
        "DF-45 regression: price threshold must be 1_000_000"
    )
    assert "price > 100_000" not in src, (
        "DF-45 regression: old 100_000 threshold still present"
    )


def test_df33_full_info_default_matches_docstring():
    """DF-33: docstring promised lightweight default; code defaulted to true."""
    src = Path("src/data_fetcher.py").read_text()
    assert 'os.getenv("DAILY_FETCH_YF_FULL_INFO", "false")' in src, (
        "DF-33 regression: DAILY_FETCH_YF_FULL_INFO default must be 'false'"
    )


# ─── parallel_scorer.py ───
def test_ps48_score_one_returns_signals():
    """PS-48: _score_one computed sig but dropped it. ONE-LINE fix."""
    src = Path("src/parallel_scorer.py").read_text()
    # Slice the source between `def _score_one` and the next top-level `def `
    start = src.find("def _score_one")
    assert start != -1, "_score_one not found"
    next_def = src.find("\ndef ", start + 1)
    body = src[start:next_def] if next_def != -1 else src[start:]
    assert '"signals": sig' in body or "'signals': sig" in body, (
        "PS-48 regression: _score_one return dict must include 'signals': sig"
    )


def test_ps49_composite_pre_snapshots_present():
    """PS-49: composite mutated 3x without snapshots → audit trail lost."""
    src = Path("src/parallel_scorer.py").read_text()
    snapshots = ["composite_pre_watchlist", "composite_pre_pattern", "composite_pre_wisdom"]
    found = [s for s in snapshots if s in src]
    assert len(found) >= 2, (
        f"PS-49 regression: expected >=2 composite_pre_* snapshots, found {found}"
    )


# ─── portfolio_risk_gate.py ───
def test_prg21_loud_warning_on_missing_picks_log():
    """PRG-21: silent fail-open on missing picks_log was hiding the gate
    operating on empty history. Now LOUDLY warns the operator."""
    src = Path("src/portfolio_risk_gate.py").read_text()
    body = src[src.find("def load_open_positions_from_picks_log"):]
    body_until_next_def = body[:body.find("\ndef ", 1)] if "\ndef " in body[1:] else body
    assert "WARN" in body_until_next_def or "warn" in body_until_next_def.lower(), (
        "PRG-21 regression: missing picks_log must produce a loud WARN"
    )
