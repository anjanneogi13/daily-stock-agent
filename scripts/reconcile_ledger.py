#!/usr/bin/env python3
"""One-time ledger reconciliation — Cluster E (stale / orphaned positions).

Settles every position still open past its hold horizon (the phantom ANL
swing, the legacy CDNS…BZH block, and any other orphan) exactly once:

  * evaluation_status = "expired"  (projects to EXPIRED_OVERDUE, terminal)
  * evaluated_on      = the position's deterministic horizon date
                        (pick_date + max hold trading window), NEVER "today" —
                        so re-runs on later days produce identical output
  * exit fields       = left empty → the row classifies as UNVERIFIED, an
                        honest "settled without exit-price data" outcome that
                        is excluded from win/loss statistics rather than
                        fabricated as a $0 loss

Positions still inside their horizon are left untouched (the daily evaluator
owns them). Rows already terminal are never modified (write-once guard in
src/picks_csv.py also enforces this), which makes the script idempotent:
running it twice produces zero additional changes.

Usage:
    python scripts/reconcile_ledger.py --dry-run   # show what would settle
    python scripts/reconcile_ledger.py             # apply
"""
import argparse
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.trade_state import (
    expected_close_date, is_terminal, load_ledger, max_hold_days,
)
from src.picks_csv import update_pick_row


def find_orphans(rows, today=None, before=None):
    """Open rows whose hold horizon has fully elapsed as of `today`.

    `before` (YYYY-MM-DD) optionally restricts settlement to rows picked
    before that date — used for the one-time legacy cleanup so recent rows
    stay with the daily evaluator, which can still fetch their real bars.
    """
    today = today or datetime.now().date()
    orphans = []
    for r in rows:
        if is_terminal(r):
            continue
        pick_date = (r.get("pick_date") or "")[:10]
        if not pick_date:
            continue
        if before and pick_date >= before:
            continue
        horizon = expected_close_date(r)
        if horizon is None:
            continue
        if horizon < today:
            orphans.append((r, horizon))
    return orphans


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true",
                    help="report what would be settled without writing")
    ap.add_argument("--before", metavar="YYYY-MM-DD", default=None,
                    help="only settle rows picked before this date "
                         "(legacy cleanup; leaves recent rows to the evaluator)")
    args = ap.parse_args(argv)

    rows = load_ledger()
    if not rows:
        print("[reconcile] no ledger rows found")
        return 0

    orphans = find_orphans(rows, before=args.before)
    if not orphans:
        print("[reconcile] ledger clean — no open positions past horizon")
        return 0

    print(f"[reconcile] {len(orphans)} open position(s) past hold horizon:")
    settled = 0
    for row, horizon in orphans:
        ticker = row.get("ticker", "?")
        pick_date = (row.get("pick_date") or "")[:10]
        ttype = (row.get("trade_type") or "swing").lower()
        print(f"  {ticker:8s} picked {pick_date} ({ttype}, max {max_hold_days(ttype)}d) "
              f"→ expired, evaluated_on={horizon.isoformat()} (UNVERIFIED — no exit data)")
        if args.dry_run:
            continue
        ok = update_pick_row(pick_date, ticker, {
            "evaluation_status": "expired",
            "evaluated_on": horizon.isoformat(),
        })
        if ok:
            settled += 1
        else:
            print(f"  [warn] could not update row for {ticker} {pick_date}")

    if args.dry_run:
        print(f"[reconcile] DRY RUN — nothing written ({len(orphans)} would settle)")
    else:
        print(f"[reconcile] settled {settled}/{len(orphans)} orphaned position(s) — "
              "closed exactly once, immutable from here on")
    return 0


if __name__ == "__main__":
    sys.exit(main())
