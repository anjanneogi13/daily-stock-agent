"""Sync closed outcomes from picks_log.csv into data/signal_journal.jsonl.

Audit 2026-10-29: 45 of 110 closed official picks (17 from October alone)
had a signal_journal row whose ``outcome`` was still ``None`` even though
picks_log.csv carried the verified result. The journal is what
``self_awareness`` (rolling 30/60/90d confidence intervals), the hypothesis
engine and the weekly footer read — so the agent's "how am I doing?" view
saw 13 closed trades in the last 30 days when there were 30.

Cause: the evaluator attaches outcomes in the same CI run that evaluates,
but for weeks its pushes were lost (rebase failures), and later catch-up
runs re-evaluated rows from a journal checkout that was then overwritten by
competing workflow commits.

This script is the idempotent repair: for every closed+verified official
picks_log row, call ``signal_journal.attach_outcome`` (the SAME code path the
evaluator uses, so win/loss/flat semantics are identical). attach_outcome
only fills rows whose outcome is None — verified journal rows are never
rewritten.

Usage:
    python scripts/sync_journal_outcomes.py            # dry run
    python scripts/sync_journal_outcomes.py --apply
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import signal_journal as sj  # noqa: E402
from src.outcome_window import load_rows, is_closed_verified, is_official, _to_float  # noqa: E402


def _journal_open_keys() -> set:
    """(ticker, pick_date) of journal rows that still have no outcome."""
    if not sj.JOURNAL.exists():
        return set()
    keys = set()
    with sj.JOURNAL.open() as f:
        for line in f:
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if r.get("outcome") is None:
                keys.add((r.get("ticker"), r.get("pick_date")))
    return keys


def find_unsynced(rows=None) -> list:
    rows = load_rows() if rows is None else rows
    open_keys = _journal_open_keys()
    out = []
    seen = set()
    for r in rows:
        if not (is_official(r) and is_closed_verified(r)):
            continue
        key = (r.get("ticker"), r.get("pick_date"))
        if key in open_keys and key not in seen:
            seen.add(key)
            out.append(r)
    return out


def run(apply: bool = False) -> dict:
    todo = find_unsynced()
    rep = {"unsynced": len(todo), "attached": 0, "mode": "apply" if apply else "dry_run"}
    if not todo:
        print("[journal-sync] ✅ journal outcomes already in sync with picks_log")
        return rep
    print(f"[journal-sync] {len(todo)} closed pick(s) missing a journal outcome "
          f"({'APPLY' if apply else 'DRY RUN'})")
    for r in todo:
        label = f"{r['pick_date']} {r['ticker']} {r.get('evaluation_status')} R={r.get('r_multiple')}"
        if not apply:
            print(f"  · {label}")
            continue
        ok = sj.attach_outcome(
            ticker=r["ticker"], pick_date=r["pick_date"],
            r_multiple=_to_float(r.get("r_multiple")),
            actual_return_pct=_to_float(r.get("actual_return_pct")),
            evaluated_on=r.get("evaluated_on") or r["pick_date"],
        )
        rep["attached"] += int(bool(ok))
        print(f"  {'✓' if ok else '✗'} {label}")
    print(f"[journal-sync] attached={rep['attached']}/{rep['unsynced']}")
    return rep


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--apply", action="store_true", help="write outcomes (default: dry run)")
    args = ap.parse_args(argv)
    run(apply=args.apply)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
