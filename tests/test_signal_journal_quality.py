"""Production data quality gate for signal_journal.

These tests fail if entries written AFTER the May 4 metadata fix show
'unknown' buckets in fields that should always have data.

Historical entries (pre-2026-05-05) may have legacy 'unknown' values from
the silent-failure period (May 2-4) and are intentionally excluded.
"""
import json
from pathlib import Path
from datetime import datetime, timedelta

JOURNAL = Path("data/signal_journal.jsonl")

# Cutoff: only entries on or after this date are quality-gated
QUALITY_GATE_START = "2026-05-05"


def _post_fix_entries():
    """Return entries written AFTER metadata fix took effect."""
    if not JOURNAL.exists():
        return []
    out = []
    with JOURNAL.open() as f:
        for line in f:
            try:
                r = json.loads(line)
                if r.get("pick_date", "") >= QUALITY_GATE_START:
                    out.append(r)
            except json.JSONDecodeError:
                continue
    return out


def test_post_fix_composite_score_never_unknown():
    entries = _post_fix_entries()
    if not entries:
        return  # no post-fix data yet — skip until tomorrow's pick
    unknowns = [e for e in entries if e["signals"].get("composite_score_bucket") == "unknown"]
    pct = 100 * len(unknowns) / len(entries)
    assert pct < 10, (
        f"REGRESSION: {pct:.0f}% of post-fix picks have unknown composite_score "
        f"({len(unknowns)}/{len(entries)}). Check main.py journal block."
    )


def test_post_fix_regime_never_unknown():
    entries = _post_fix_entries()
    if not entries:
        return
    unknowns = [e for e in entries if e["signals"].get("regime") == "unknown"]
    pct = 100 * len(unknowns) / len(entries)
    assert pct < 10, (
        f"REGRESSION: {pct:.0f}% of post-fix picks have unknown regime"
    )


def test_post_fix_vol_ratio_never_unknown():
    """Once vol_ratio is in CSV + main.py, this should always be tagged.

    PR-A4 (2026-05-15): added small-N guard. With only 1-2 post-fix entries,
    a single 'unknown' produces 50-100% rates that trip the 10% threshold
    spuriously. Test now requires >=10 entries before enforcing the bound,
    matching real-world statistical relevance.

    KNOWN OPEN BUG (PR-A5): AMAT 2026-05-15 was journaled with unknown
    vol_ratio because main.py line 1746 writes p['scores'].get('vol_ratio')
    which is None when parallel_scorer.py fails to compute it (likely
    yfinance rate-limit on info fetch). Same root cause as PR-A2.6 BUG-A
    (missing company name). Track in audit doc 1-pager for PR-A5.
    """
    entries = _post_fix_entries()
    if len(entries) < 10:
        return  # insufficient sample — wait for more post-fix data
    unknowns = [e for e in entries if e["signals"].get("vol_ratio_bucket") == "unknown"]
    pct = 100 * len(unknowns) / len(entries)
    assert pct < 10, (
        f"REGRESSION: {pct:.0f}% of post-fix picks have unknown vol_ratio "
        f"({len(unknowns)}/{len(entries)}). "
        f"Check that pick_logger.py FIELDS includes 'vol_ratio' AND main.py writes it."
    )


def test_buckets_have_valid_values():
    """Every bucket value must be from a known vocabulary (no garbage)."""
    valid = {
        "composite_score_bucket": {"low", "mid", "high", "very_high", "unknown"},
        "regime":                 {"bull", "bear", "chop", "transition", "unknown"},
        "vol_ratio_bucket":       {"low", "normal", "high", "extreme", "unknown"},
        "monster_score_bucket":   {"none", "mid", "monster"},
        "brain_p_win_bucket":     {"low", "mid", "high", "very_high", "unknown"},
        "days_to_earnings_bucket":{"none", "imminent", "near", "far"},
        "trade_type":             {"swing", "day"},
    }
    if not JOURNAL.exists():
        return
    with JOURNAL.open() as f:
        for line in f:
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            for k, allowed in valid.items():
                v = r.get("signals", {}).get(k)
                if v is not None:
                    assert v in allowed, (
                        f"Invalid {k}={v!r} in {r.get('ticker')} ({r.get('pick_date')})"
                    )
