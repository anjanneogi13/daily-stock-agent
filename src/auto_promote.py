"""T29: Auto-promote consistent statistical patterns into wisdom lessons.

Closes the learning loop:

  hypothesis_engine writes patterns
       │
       ▼
  auto_promote (this) sees same pattern persist with high N + low p
       │
       ▼
  writes a wisdom lesson tagged with signal/bucket
       │
       ▼
  wisdom_hint surfaces lesson inline on every matching pick
       │
       ▼
  user sees risk warning BEFORE entering the trade

PROMOTION CRITERIA (all required):
  - sample_n  >= MIN_SAMPLE   (default 40)
  - p_value   <= MAX_P        (default 0.01)
  - signal in {trade_type, regime, sector, day_of_week}

IDEMPOTENCY:
  Each promotion adds a marker tag "auto_promote:{signal}:{bucket}"
  to the lesson. Re-running scans existing lessons for that marker
  and skips duplicates. Safe to invoke daily / weekly / on cron.
"""
from typing import Dict, List, Optional

from .wisdom_base import (
    add_lesson,
    load_active_lessons,
    load_active_patterns,
)

MIN_SAMPLE = 40
MAX_P      = 0.01

KNOWN_SIGNALS = {"trade_type", "regime", "sector", "day_of_week"}


def _marker(signal: str, bucket: str) -> str:
    return f"auto_promote:{signal}:{bucket}".lower()


def _already_promoted(signal: str, bucket: str,
                      existing_lessons: Optional[List[Dict]] = None) -> bool:
    """True if a lesson already carries the auto_promote marker tag."""
    mark = _marker(signal, bucket)
    lessons = existing_lessons if existing_lessons is not None \
              else load_active_lessons(min_confidence=0.0)
    for L in lessons:
        tags = [str(x).lower() for x in (L.get("tags") or [])]
        if mark in tags:
            return True
    return False


def _confidence_from_p(p: float) -> float:
    """Lower p → higher confidence. Clamped to [0.7, 0.95]."""
    try:
        c = 1.0 - float(p) * 10.0
    except (TypeError, ValueError):
        return 0.7
    return max(0.7, min(0.95, c))


def _format_text(p: Dict) -> str:
    """Human-readable lesson text from a pattern dict."""
    signal   = p.get("signal", "?")
    bucket   = p.get("bucket", "?")
    effect   = p.get("effect", "?")
    win_rate = p.get("win_rate", 0.0)
    n        = p.get("sample_n", 0)
    verb     = "avoid" if effect == "drag" else "favor"
    return (f"AUTO: {signal}={bucket} shows "
            f"{win_rate*100:.0f}% win-rate over {n} trades — {verb}")


def promote_patterns(min_sample: int = MIN_SAMPLE,
                     max_p: float = MAX_P,
                     dry_run: bool = False) -> List[Dict]:
    """Scan active patterns; for each that meets criteria and isn't
    already promoted, write a wisdom lesson.

    Returns: list of newly-created lesson dicts (or would-be-created
             dicts when dry_run=True).
    """
    promoted: List[Dict] = []
    patterns = load_active_patterns()
    if not patterns:
        return promoted

    # Snapshot existing lessons once to avoid O(N*M) reloads
    existing = load_active_lessons(min_confidence=0.0)

    for p in patterns:
        signal = (p.get("signal") or "").lower()
        bucket = str(p.get("bucket") or "").strip()
        effect = (p.get("effect") or "").lower()
        n      = int(p.get("sample_n") or 0)
        try:
            pv = float(p.get("p_value", 1.0))
        except (TypeError, ValueError):
            pv = 1.0

        if signal not in KNOWN_SIGNALS:        continue
        if not bucket:                          continue
        if effect not in ("drag", "edge"):      continue
        if n < min_sample:                      continue
        if pv > max_p:                          continue
        if _already_promoted(signal, bucket, existing):  continue

        text = _format_text(p)
        conf = _confidence_from_p(pv)
        tags = [signal, bucket, "auto_promote", _marker(signal, bucket)]

        if dry_run:
            promoted.append({
                "text": text, "confidence": conf, "tags": tags,
                "_dry_run": True,
            })
        else:
            rec = add_lesson(text=text, source="auto_promote",
                             confidence=conf, tags=tags,
                             author="auto_promote")
            promoted.append(rec)
            existing.append(rec)  # so subsequent iterations see it

    return promoted


# ═════════════════════════════════════════════════════════════
# CLI
# ═════════════════════════════════════════════════════════════
def _cli(argv=None):
    import argparse
    ap = argparse.ArgumentParser(
        description="Auto-promote significant patterns into wisdom lessons."
    )
    ap.add_argument("--min-sample", type=int, default=MIN_SAMPLE)
    ap.add_argument("--max-p", type=float, default=MAX_P)
    ap.add_argument("--dry-run", action="store_true",
                    help="Show what would be promoted without writing")
    args = ap.parse_args(argv)

    out = promote_patterns(min_sample=args.min_sample,
                           max_p=args.max_p,
                           dry_run=args.dry_run)
    if not out:
        print("ℹ No patterns met promotion criteria.")
        return 0

    label = "Would promote" if args.dry_run else "Promoted"
    print(f"\n🧠 {label} {len(out)} pattern(s) → lessons:")
    print("─" * 60)
    for L in out:
        print(f"  • [{L['confidence']:.2f}] {L['text']}")
        print(f"    tags: {L['tags']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
