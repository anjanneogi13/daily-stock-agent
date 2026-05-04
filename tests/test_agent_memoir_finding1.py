"""Finding #1 (May 4 2026): Soul faculty must count real outcome statuses."""
import csv
from pathlib import Path
from src.agent_memoir import _load_closed_picks


def test_memoir_counts_tp_hit_sl_hit_expired(tmp_path, monkeypatch):
    """Memoir should count picks with evaluation_status in (tp_hit, sl_hit, expired)."""
    fake_csv = tmp_path / "picks_log.csv"
    rows = [
        {"ticker": "AAA", "evaluation_status": "tp_hit",   "r_multiple": "1.5"},
        {"ticker": "BBB", "evaluation_status": "sl_hit",   "r_multiple": "-1.0"},
        {"ticker": "CCC", "evaluation_status": "expired",  "r_multiple": "0.2"},
        {"ticker": "DDD", "evaluation_status": "pending",  "r_multiple": ""},
        {"ticker": "EEE", "evaluation_status": "unreachable_entry", "r_multiple": ""},
    ]
    with fake_csv.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)

    # Patch the module's PICKS_LOG path
    import src.agent_memoir as memoir
    monkeypatch.setattr(memoir, "PICKS_LOG", fake_csv)

    closed = _load_closed_picks()
    tickers = sorted(r["ticker"] for r in closed)
    assert tickers == ["AAA", "BBB", "CCC"], \
        f"Expected AAA/BBB/CCC, got {tickers}. Pending and unreachable_entry must be excluded."
    assert len(closed) == 3


def test_memoir_does_not_count_pending():
    """Sanity: 'closed' (the OLD broken value) should NOT match anything."""
    # Real picks_log.csv values per pick_evaluator.py: tp_hit, sl_hit, expired,
    # pending, unreachable_entry. Never 'closed'. This test would have failed
    # before the fix because no rows matched, returning 0 always.
    pass  # captured by test above
