"""T32: Stale-lesson garbage collector.

Auto-deactivates lessons older than MAX_AGE_DAYS so the wisdom base
stays signal-rich. Lessons aren't deleted — they get active=False,
preserving an audit trail and keeping idempotency.

PROTECTIONS:
  - lessons with confidence >= PROTECT_CONF (default 0.90) are kept
    forever (user-curated truths)
  - already-inactive lessons are skipped
  - lessons missing/unparseable ts are kept (fail safe)

CLI:
  python -m src.lesson_gc                 # actually deactivate
  python -m src.lesson_gc --dry-run       # preview only
  python -m src.lesson_gc --max-age 30    # tighter cull
  python -m src.lesson_gc --protect 0.95  # raise protection bar
"""
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

from .wisdom_base import LESSONS

MAX_AGE_DAYS = 90
PROTECT_CONF = 0.90


def _parse_ts(s: str):
    """Best-effort ISO-8601 parse. Returns datetime or None."""
    if not s:
        return None
    try:
        return datetime.fromisoformat(s)
    except (ValueError, TypeError):
        return None


def find_stale(max_age_days: int = MAX_AGE_DAYS,
               protect_conf: float = PROTECT_CONF,
               now: datetime = None) -> List[Dict]:
    """Return list of stale lesson dicts that WOULD be deactivated."""
    if not LESSONS.exists():
        return []
    now = now or datetime.now()
    cutoff = now - timedelta(days=max_age_days)

    stale = []
    with LESSONS.open() as f:
        for line in f:
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not r.get("active", True):
                continue
            if float(r.get("confidence", 0)) >= protect_conf:
                continue
            ts = _parse_ts(r.get("ts"))
            if ts is None:
                continue  # fail safe — keep
            if ts < cutoff:
                stale.append(r)
    return stale


def gc_stale(max_age_days: int = MAX_AGE_DAYS,
             protect_conf: float = PROTECT_CONF,
             dry_run: bool = False,
             now: datetime = None) -> Tuple[int, List[Dict]]:
    """Deactivate stale lessons in place.

    Returns: (count_deactivated, list_of_deactivated_records)
    """
    if not LESSONS.exists():
        return 0, []
    now = now or datetime.now()
    cutoff = now - timedelta(days=max_age_days)

    rows = []
    deactivated = []
    with LESSONS.open() as f:
        for line in f:
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if (r.get("active", True)
                    and float(r.get("confidence", 0)) < protect_conf):
                ts = _parse_ts(r.get("ts"))
                if ts is not None and ts < cutoff:
                    r["active"] = False
                    r["deactivated_at"] = now.isoformat(timespec="seconds")
                    r["deactivated_reason"] = f"stale>{max_age_days}d"
                    deactivated.append(r)
            rows.append(r)

    if not dry_run and deactivated:
        with LESSONS.open("w") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")

    return len(deactivated), deactivated


# ═════════════════════════════════════════════════════════════
# CLI
# ═════════════════════════════════════════════════════════════
def _cli(argv=None):
    import argparse
    ap = argparse.ArgumentParser(
        description="Deactivate wisdom lessons older than --max-age days."
    )
    ap.add_argument("--max-age", type=int, default=MAX_AGE_DAYS,
                    help=f"Age threshold in days (default {MAX_AGE_DAYS})")
    ap.add_argument("--protect", type=float, default=PROTECT_CONF,
                    help=f"Spare lessons with conf >= this (default {PROTECT_CONF})")
    ap.add_argument("--dry-run", action="store_true",
                    help="Show what would be deactivated; don't write")
    args = ap.parse_args(argv)

    n, recs = gc_stale(
        max_age_days=args.max_age,
        protect_conf=args.protect,
        dry_run=args.dry_run,
    )
    if n == 0:
        print("✅ No stale lessons to deactivate.")
        return 0

    label = "Would deactivate" if args.dry_run else "Deactivated"
    print(f"\n🗑  {label} {n} stale lesson(s):")
    print("─" * 60)
    for r in recs:
        ts = r.get("ts", "?")[:10]
        conf = float(r.get("confidence", 0))
        text = (r.get("text") or "")[:65]
        print(f"  • [{ts}] [{conf:.2f}] {text}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
