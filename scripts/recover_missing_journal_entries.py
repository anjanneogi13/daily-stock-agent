"""PR-A4: Recover signal_journal entries for picks that exist in picks_log
but never made it into signal_journal.jsonl.

Real-world cause: 2026-05-15 AMAT was logged to picks_log.csv but never
appeared in signal_journal.jsonl because the daily-picks workflow's
'git add' step silently omitted signal_journal.jsonl from staging.

This script uses the SAME code path main.py uses (signal_journal.log_pick
via build_signals) so the recovered entry is schema-identical to a
normally-journaled pick. Idempotent: existing (ticker,pick_date) pairs are
skipped. Safe to run repeatedly.
"""
from __future__ import annotations
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src import signal_journal as sj
from scripts.audit_journal_consistency import _load_picks_keys, _load_journal_keys

PICKS = Path("data/picks_log.csv")


def _csv_row_to_pick_dict(row: dict) -> dict:
    """Reshape a picks_log.csv row into the dict shape build_signals() expects.

    Mirrors the structure main.py passes to _journal_log_pick (see main.py
    lines 1769-1779), so recovered rows produce identical bucket assignments.
    """
    def _to_float(v):
        try:
            return float(v) if v not in (None, "") else None
        except (TypeError, ValueError):
            return None

    def _to_int(v):
        try:
            return int(float(v)) if v not in (None, "") else None
        except (TypeError, ValueError):
            return None

    scores = {
        "composite": _to_float(row.get("score")),
        "sector_tag": row.get("tag") or "",
        "vol_ratio": _to_float(row.get("vol_ratio")),
        "monster_score": _to_float(row.get("monster_score")),
    }
    brain = {
        "p_win": _to_float(row.get("brain_p_win")),
    }
    return {
        "ticker": row.get("ticker"),
        "pick_date": row.get("pick_date"),
        "scores": scores,
        "brain": brain,
        "regime": row.get("regime") or "unknown",
        "trade_type": row.get("trade_type") or "swing",
        "days_to_earnings": _to_int(row.get("days_to_earnings")),
        "vol_ratio": _to_float(row.get("vol_ratio")),
        "tag": row.get("tag") or "",
    }


def main(argv=None) -> int:
    argv = argv or sys.argv[1:]
    dry_run = "--dry-run" in argv

    if not PICKS.exists():
        print(f"❌ {PICKS} not found")
        return 1

    pick_keys = _load_picks_keys()
    journal_keys = _load_journal_keys()
    missing_keys = pick_keys - journal_keys

    if not missing_keys:
        print(f"✅ No drift. picks={len(pick_keys)} journal={len(journal_keys)}")
        return 0

    print(f"📊 picks={len(pick_keys)} journal={len(journal_keys)}")
    print(f"🔧 {len(missing_keys)} pick(s) missing from journal:")
    for ticker, pick_date in sorted(missing_keys):
        print(f"   {pick_date}  {ticker}")

    if dry_run:
        print("(dry-run — no writes)")
        return 0

    recovered = 0
    with PICKS.open() as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = (row.get("ticker"), row.get("pick_date"))
            if key not in missing_keys:
                continue
            pick = _csv_row_to_pick_dict(row)
            try:
                sj.log_pick(pick, regime=pick["regime"])
                recovered += 1
                print(f"   ✅ recovered {key[1]} {key[0]}")
            except Exception as e:
                print(f"   ❌ FAILED {key[1]} {key[0]}: {e}")

    print(f"📝 recovered {recovered}/{len(missing_keys)} entries")
    return 0 if recovered == len(missing_keys) else 1


if __name__ == "__main__":
    sys.exit(main())
