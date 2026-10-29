"""Backfill UNVERIFIED expired outcomes in data/picks_log.csv.

Problem (audit 2026-10-29): 68 of 238 logged picks (all of June/July 2026 and
batches in Apr/May/Aug) are ``expired`` with NO exit_price / r_multiple.
The evaluator's results were not being pushed for weeks (silent
``git pull --rebase`` failures, since fixed); when it resumed, every pending
pick older than EVAL_LOOKBACK_DAYS was bulk-settled "expired, unverified"
without ever looking at a price bar. Those rows are invisible to every
learning report, so months of outcomes were simply lost.

This script re-walks those rows against real historical OHLC with the SAME
evaluator logic (``pick_evaluator.evaluate_pending`` with the lookback cutoff
disabled), so the result is byte-for-byte what the evaluator would have
written had it run on time: tp_hit / sl_hit / day_close / expired-at-horizon
(with price) / unreachable_entry. Rows whose data genuinely cannot be
fetched stay unverified.

Safety:
- Only rows with evaluation_status == "expired" AND empty r_multiple are
  touched. Verified outcomes are NEVER overwritten (first decision wins).
- Dry-run by default; ``--apply`` writes picks_log.csv atomically and
  attaches outcomes to data/signal_journal.jsonl (only rows with outcome None).
- Idempotent: once repaired, a row carries exit data and is skipped.
- Writes an audit artifact data/learning/outcome_backfill_<date>.json.

Usage:
    python scripts/backfill_unverified_outcomes.py            # preview
    python scripts/backfill_unverified_outcomes.py --apply    # repair
    python scripts/backfill_unverified_outcomes.py --apply --since 2026-06-01
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import pick_evaluator as pe  # noqa: E402
from src.outcome_window import is_unverified_expired, is_official  # noqa: E402

AUDIT_DIR = Path("data/learning")
NO_CUTOFF_DAYS = 10_000  # effectively disables the "too old → unverified" path


def select_candidates(rows: list, since: str | None = None,
                      include_watch_only: bool = False) -> list:
    out = []
    for r in rows:
        if not is_unverified_expired(r):
            continue
        if not include_watch_only and not is_official(r):
            continue
        if since and (r.get("pick_date") or "") < since:
            continue
        out.append(r)
    return out


def run(apply: bool = False, since: str | None = None,
        include_watch_only: bool = False, limit: int | None = None) -> dict:
    rows = pe._load_picks()
    candidates = select_candidates(rows, since=since,
                                   include_watch_only=include_watch_only)
    if limit:
        candidates = candidates[:limit]
    report = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "mode": "apply" if apply else "dry_run",
        "candidates": len(candidates),
        "repaired": 0,
        "still_unverified": 0,
        "by_status": {},
        "rows": [],
    }
    if not candidates:
        print("[backfill] ✅ No unverified expired rows — nothing to do.")
        return report

    print(f"[backfill] {len(candidates)} unverified expired row(s) to re-walk "
          f"({'APPLY' if apply else 'DRY RUN'})")
    before = {id(r): dict(r) for r in candidates}
    for r in candidates:
        # Re-open the row so the evaluator walks it with the real price path.
        r["evaluation_status"] = "pending"
        r["evaluated_on"] = ""

    # Evaluate ONLY the re-opened rows: everything else is left untouched.
    # Journal attachment happens inside the evaluator; in dry-run we must not
    # mutate the journal, so stub it out.
    journal_attach = pe._journal_attach
    if not apply:
        pe._journal_attach = lambda **kw: False
    try:
        pe.evaluate_pending(lookback_days=NO_CUTOFF_DAYS, rows=candidates, save=False)
    finally:
        pe._journal_attach = journal_attach

    statuses = Counter()
    for r in candidates:
        old = before[id(r)]
        verified = r.get("r_multiple") not in (None, "", "None")
        if not verified:
            # Evaluator could not settle it against real bars (no data) —
            # restore the original row untouched rather than leaving it
            # pending or re-stamping evaluated_on (first decision wins).
            r.clear()
            r.update(old)
        statuses[r.get("evaluation_status")] += 1
        if verified:
            report["repaired"] += 1
        else:
            report["still_unverified"] += 1
        report["rows"].append({
            "pick_date": r.get("pick_date"), "ticker": r.get("ticker"),
            "trade_type": r.get("trade_type"),
            "status": r.get("evaluation_status"),
            "evaluated_on": r.get("evaluated_on"),
            "exit_price": r.get("exit_price"),
            "r_multiple": r.get("r_multiple"),
            "verified": verified,
        })
    report["by_status"] = dict(statuses)

    if apply:
        pe._save_picks(rows)
        AUDIT_DIR.mkdir(parents=True, exist_ok=True)
        out = AUDIT_DIR / f"outcome_backfill_{report['date']}.json"
        out.write_text(json.dumps(report, indent=2))
        print(f"[backfill] 💾 picks_log.csv updated; audit → {out}")
    else:
        print("[backfill] dry run — picks_log.csv NOT modified (use --apply)")

    print(f"[backfill] repaired={report['repaired']} still_unverified={report['still_unverified']} "
          f"by_status={report['by_status']}")
    return report


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--apply", action="store_true", help="write results (default: dry run)")
    ap.add_argument("--since", default=None, help="only rows with pick_date >= YYYY-MM-DD")
    ap.add_argument("--include-watch-only", action="store_true")
    ap.add_argument("--limit", type=int, default=None, help="max rows to re-walk")
    args = ap.parse_args(argv)
    run(apply=args.apply, since=args.since,
        include_watch_only=args.include_watch_only, limit=args.limit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
