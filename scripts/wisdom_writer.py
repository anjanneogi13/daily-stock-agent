"""
Wisdom Writer — converts hypothesis_engine output into wisdom_base patterns.
Run weekly (or manually) after evaluator + hypothesis review.

Usage: python scripts/wisdom_writer.py [--dry-run]
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.signal_journal import load_closed
from src.hypothesis_engine import analyze
from src.wisdom_base import (
    add_pattern, load_active_patterns, add_lesson, stats,
)


def main(dry_run: bool = False):
    closed = load_closed()
    result = analyze(closed)

    print(f"📊 {result['summary']}")

    # Index existing patterns to avoid duplicates
    existing = {(p["signal"], p["bucket"], p["effect"]) for p in load_active_patterns()}

    new_count = 0
    for e in result.get("edges", []):
        key = (e["signal"], e["bucket"], "edge")
        if key in existing:
            continue
        if dry_run:
            print(f"  [dry-run] would add EDGE: {e['signal']}={e['bucket']} "
                  f"WR={e['win_rate']:.0%} n={e['n']} p={e['p_value']:.3f}")
        else:
            add_pattern(e["signal"], e["bucket"], "edge",
                        e["win_rate"], e["n"], e["p_value"])
            new_count += 1

    for d in result.get("drags", []):
        key = (d["signal"], d["bucket"], "drag")
        if key in existing:
            continue
        if dry_run:
            print(f"  [dry-run] would add DRAG: {d['signal']}={d['bucket']} "
                  f"WR={d['win_rate']:.0%} n={d['n']} p={d['p_value']:.3f}")
        else:
            add_pattern(d["signal"], d["bucket"], "drag",
                        d["win_rate"], d["n"], d["p_value"])
            new_count += 1

    if not dry_run and new_count:
        print(f"✅ Added {new_count} new patterns to wisdom base.")
        print(f"   Stats: {stats()}")
    elif not new_count:
        print("ℹ️  No new patterns to add (all already known or insufficient data).")


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    main(dry)
