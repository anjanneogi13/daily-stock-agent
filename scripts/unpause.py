"""Manually clear an active auto-pause.

Usage:
    python scripts/unpause.py
    python scripts/unpause.py --reason "owner override after review"
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.pause_state import is_paused, clear_state


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reason", default="manual override")
    args = ap.parse_args()

    cur = is_paused()
    if not cur["paused"]:
        print("✅ Agent is NOT currently paused. Nothing to do.")
        return 0

    print(f"⚠ Active pause:")
    print(f"   Until:  {cur['until']} ({cur['days_remaining']}d remaining)")
    print(f"   Reason: {cur['reason']}")
    print(f"   Score:  {cur.get('score', '?')}/10")
    print()
    confirm = input(f"Clear this pause? Reason: {args.reason!r} [y/N] ")
    if confirm.strip().lower() not in ("y", "yes"):
        print("Aborted.")
        return 1

    clear_state()
    print("✅ Pause cleared. Next daily run will proceed normally.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
