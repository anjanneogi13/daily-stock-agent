"""Audit consistency between data/picks_log.csv and data/signal_journal.jsonl.

INVARIANT (locked May 4 2026, F4):
  Every pick in picks_log.csv must have a matching entry in signal_journal.jsonl
  keyed by (ticker, pick_date). Drift between the two stores would mean
  hypothesis_engine and the layman channel see different worlds.

Counter-rule: signal_journal MAY have entries with outcome=null (open picks
not yet evaluated). picks_log MAY have entries with evaluation_status=pending.
That is fine — they\'re both just "in flight".

Usage:
    python scripts/audit_journal_consistency.py            # report
    python scripts/audit_journal_consistency.py --strict   # exit 1 on drift
"""
from __future__ import annotations
import csv
import json
import sys
from pathlib import Path

PICKS = Path("data/picks_log.csv")
JOURNAL = Path("data/signal_journal.jsonl")


def _load_picks_keys() -> set[tuple[str, str]]:
    if not PICKS.exists():
        return set()
    keys = set()
    for r in csv.DictReader(PICKS.open()):
        t = (r.get("ticker") or "").strip()
        d = (r.get("pick_date") or "").strip()
        if t and d:
            keys.add((t, d))
    return keys


def _load_journal_keys() -> set[tuple[str, str]]:
    if not JOURNAL.exists():
        return set()
    keys = set()
    with JOURNAL.open() as f:
        for line in f:
            try:
                j = json.loads(line)
            except json.JSONDecodeError:
                continue
            t = (j.get("ticker") or "").strip()
            d = (j.get("pick_date") or "").strip()
            if t and d:
                keys.add((t, d))
    return keys


def audit() -> dict:
    pk = _load_picks_keys()
    jk = _load_journal_keys()
    return {
        "picks_count": len(pk),
        "journal_count": len(jk),
        "in_picks_only": sorted(pk - jk),
        "in_journal_only": sorted(jk - pk),
        "in_both": len(pk & jk),
    }


def main(argv=None):
    argv = argv or sys.argv[1:]
    strict = "--strict" in argv
    r = audit()

    print(f"  picks_log entries:    {r['picks_count']}")
    print(f"  signal_journal lines: {r['journal_count']}")
    print(f"  Matched (both):       {r['in_both']}")
    print(f"  In picks ONLY:        {len(r['in_picks_only'])}")
    print(f"  In journal ONLY:      {len(r['in_journal_only'])}")

    drift = r["in_picks_only"] or r["in_journal_only"]
    if not drift:
        print("  ✅ Stores are in sync.")
        return 0

    print()
    print("─── DRIFT DETAILS ───")
    if r["in_picks_only"]:
        print(f"  ❌ {len(r['in_picks_only'])} picks NOT in journal:")
        for t, d in r["in_picks_only"][:10]:
            print(f"      {d}  {t}")
        print("    → main.py log_pick() may have failed silently. Check pipeline log.")
    if r["in_journal_only"]:
        print(f"  ⚠ {len(r['in_journal_only'])} journal entries NOT in picks:")
        for t, d in r["in_journal_only"][:10]:
            print(f"      {d}  {t}")
        print("    → likely a pick was deleted from picks_log. Investigate.")

    return 1 if strict else 0


if __name__ == "__main__":
    sys.exit(main())
