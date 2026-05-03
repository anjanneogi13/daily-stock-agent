"""Backfill signal_journal.jsonl from picks_log.csv.

For each closed pick (evaluation_status in sl_hit/tp_hit/max_hold/expired),
construct a signal record so hypothesis_engine has data to analyze.

Idempotent: skips picks already journaled (keyed by ticker+pick_date).

Usage:
    python scripts/backfill_signal_journal.py [--dry-run]
"""
from __future__ import annotations
import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src import signal_journal as sj

PICKS_LOG = Path("data/picks_log.csv")
CLOSED_STATUSES = {"sl_hit", "tp_hit", "max_hold", "expired",
                   "sl_gap", "tp_gap", "closed"}


def _existing_keys() -> set[tuple[str, str]]:
    """(ticker, pick_date) tuples already in journal."""
    if not sj.JOURNAL.exists():
        return set()
    keys = set()
    with sj.JOURNAL.open() as f:
        for line in f:
            try:
                rec = json.loads(line)
                keys.add((rec.get("ticker"), rec.get("pick_date")))
            except json.JSONDecodeError:
                continue
    return keys


def _row_to_pick_dict(row: dict) -> dict:
    """Map CSV row → dict shape that build_signals() expects."""
    def _f(k):
        v = row.get(k, "").strip()
        try:
            return float(v) if v else None
        except ValueError:
            return None
    def _i(k):
        v = row.get(k, "").strip()
        try:
            return int(float(v)) if v else None
        except ValueError:
            return None
    return {
        "ticker":            row.get("ticker"),
        "pick_date":         row.get("pick_date"),
        "tag":               row.get("tag"),
        "trade_type":        row.get("trade_type"),
        "composite_score":   _f("score"),
        "days_to_earnings":  _i("days_to_earnings"),
        "vol_ratio":         None,    # not in picks_log — bucketed as "unknown"
        "monster_score":     None,
        "p_win":             None,
    }


def _outcome_status(eval_status: str) -> str:
    s = (eval_status or "").lower()
    if s in ("tp_hit", "tp_gap"):  return "win"
    if s in ("sl_hit", "sl_gap"):  return "loss"
    if s == "max_hold":            return "neutral"
    return "neutral"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    if not PICKS_LOG.exists():
        print(f"❌ {PICKS_LOG} not found"); return 1

    existing = _existing_keys()
    print(f"📂 journal already has {len(existing)} records")

    new_records = []
    skipped_open = 0
    skipped_dupe = 0

    with PICKS_LOG.open() as f:
        reader = csv.DictReader(f)
        for row in reader:
            status = (row.get("evaluation_status") or "").lower()
            if status not in CLOSED_STATUSES:
                skipped_open += 1
                continue
            key = (row.get("ticker"), row.get("pick_date"))
            if key in existing:
                skipped_dupe += 1
                continue

            pick = _row_to_pick_dict(row)
            signals = sj.build_signals(pick)
            r_mult = None
            try:
                rm = row.get("r_multiple", "").strip()
                r_mult = float(rm) if rm else None
            except ValueError:
                pass
            ret_pct = None
            try:
                rp = row.get("actual_return_pct", "").strip()
                ret_pct = float(rp) if rp else None
            except ValueError:
                pass

            rec = {
                "pick_date":         row.get("pick_date"),
                "ticker":            row.get("ticker"),
                "signals":           signals,
                "outcome":           _outcome_status(status),
                "r_multiple":        r_mult,
                "actual_return_pct": ret_pct,
                "evaluated_on":      row.get("evaluated_on") or row.get("pick_date"),
            }
            new_records.append(rec)

    print(f"📊 {len(new_records)} new closed picks to backfill")
    print(f"   (skipped {skipped_open} still-open, {skipped_dupe} already-journaled)")

    if not new_records:
        print("✅ nothing to do — journal up-to-date"); return 0

    if args.dry_run:
        print(f"\n[DRY-RUN] sample (first 2):")
        for r in new_records[:2]:
            print(json.dumps(r, indent=2))
        return 0

    with sj.JOURNAL.open("a") as f:
        for r in new_records:
            f.write(json.dumps(r) + "\n")
    print(f"✅ appended {len(new_records)} records → {sj.JOURNAL}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
