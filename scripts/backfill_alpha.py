"""Backfill `alpha_pct` and `spy_close_at_exit` for closed picks logged
BEFORE the _add_spy_alpha helper landed (2026-05-01).

Background (Bug #9, audit 2026-05-05):
  9 picks from 2026-04-28 → 2026-05-01 closed but never got their
  SPY-relative alpha computed. They have spy_close, evaluated_on, and
  actual_return_pct — everything we need. Reuses the live calculator
  (src.pick_evaluator._add_spy_alpha) so logic stays in one place.

Usage:
    python scripts/backfill_alpha.py            # dry run (preview)
    python scripts/backfill_alpha.py --apply    # write changes

Idempotent: only fills rows where alpha_pct is empty. Safe to re-run.
Atomic: writes to a temp file then renames, so a crash mid-write
won't corrupt picks_log.csv.
"""
import csv
import os
import sys
import tempfile
from pathlib import Path

# Make src/ importable when running from repo root
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.pick_evaluator import _add_spy_alpha  # noqa: E402


PICKS_LOG = Path("data/picks_log.csv")
CLOSED_STATUSES = {"tp_hit", "sl_hit", "expired", "day_close"}


def is_candidate(row: dict) -> bool:
    """A row qualifies for backfill if it's closed, has the SPY anchor
    (spy_close at pick time), has an exit date (evaluated_on), has the
    pick's actual return, and is missing alpha_pct."""
    if row.get("evaluation_status") not in CLOSED_STATUSES:
        return False
    if not row.get("spy_close"):
        return False
    if not row.get("evaluated_on"):
        return False
    if not row.get("actual_return_pct"):
        return False
    if row.get("alpha_pct"):  # already backfilled — idempotent
        return False
    return True


def backfill(apply: bool) -> int:
    """Returns count of rows backfilled (or that WOULD be in dry run)."""
    if not PICKS_LOG.exists():
        print(f"[backfill_alpha] {PICKS_LOG} not found — nothing to do.")
        return 0

    with PICKS_LOG.open() as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    candidates = [r for r in rows if is_candidate(r)]
    print(f"[backfill_alpha] {len(candidates)} candidate(s) for backfill "
          f"(out of {len(rows)} total rows)")

    if not candidates:
        print("[backfill_alpha] Nothing to do. Exit.")
        return 0

    filled = 0
    for r in candidates:
        try:
            pick_return = float(r["actual_return_pct"])
        except (ValueError, TypeError):
            print(f"  ⚠ {r['ticker']} {r['pick_date']}: bad actual_return_pct={r.get('actual_return_pct')!r} — skip")
            continue

        # _add_spy_alpha mutates row in place: writes spy_return_pct, alpha_pct
        # and returns spy_close_at_exit as string.
        spy_at_exit_str = _add_spy_alpha(r, r["evaluated_on"], pick_return)
        if not spy_at_exit_str or r.get("alpha_pct") is None:
            print(f"  ⚠ {r['ticker']} {r['pick_date']}: SPY fetch failed for {r['evaluated_on']} — skip")
            continue
        r["spy_close_at_exit"] = spy_at_exit_str

        print(f"  ✓ {r['ticker']:6} {r['pick_date']} → {r['evaluated_on']}: "
              f"return={pick_return:+.2f}%  spy={r['spy_return_pct']:+.2f}%  "
              f"alpha={r['alpha_pct']:+.2f}%")
        filled += 1

    if not apply:
        print(f"\n[backfill_alpha] DRY RUN — would backfill {filled} row(s). "
              "Re-run with --apply to write.")
        return filled

    # Atomic write: temp file then rename
    tmp_fd, tmp_path = tempfile.mkstemp(
        prefix="picks_log.", suffix=".tmp", dir=str(PICKS_LOG.parent)
    )
    try:
        with os.fdopen(tmp_fd, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            w.writeheader()
            w.writerows(rows)
        os.replace(tmp_path, PICKS_LOG)
    except Exception:
        # Clean up temp file on any failure; don't leave debris
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise

    print(f"\n[backfill_alpha] ✅ APPLIED — backfilled {filled} row(s) into {PICKS_LOG}")
    return filled


def main():
    apply = "--apply" in sys.argv
    backfill(apply=apply)


if __name__ == "__main__":
    main()
