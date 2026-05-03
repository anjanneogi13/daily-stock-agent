"""
Idempotent wisdom-base seeder. Runs on first execution + after data resets.
Safe to run repeatedly — only adds entries if missing.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.wisdom_base import (
    add_lesson, load_active_lessons,
    add_to_kill_list, is_killed,
    stats,
)


SEED_LESSONS = [
    {
        "fingerprint": "sector-boost-leak",
        "text": ("Sector boosts (SEMI/AI multipliers) leaked -24.8 Sharpe in backtest. "
                 "Removed in May 2 sprint. DO NOT re-introduce blanket sector boosts; "
                 "instead use sector_alpha tracking + per-pattern hypothesis testing."),
        "source": "backtester", "confidence": 0.95,
        "tags": ["sector", "regime", "post-mortem"],
    },
    {
        "fingerprint": "5-ticker-exclusion",
        "text": ("Backtester proved 5 specific tickers (UNH, TEAM, SMCI, DIS, SCHW) "
                 "have negative R-multiples across 20 months. Excluded permanently."),
        "source": "backtester", "confidence": 0.90,
        "tags": ["universe", "exclusion"],
    },
    {
        "fingerprint": "observe-mode-discipline",
        "text": ("New ML/statistical features ship in OBSERVE-MODE first. Never wire "
                 "a new signal to auto-block or auto-flip until it has 30+ samples "
                 "AND statistical significance."),
        "source": "manual", "confidence": 0.95,
        "tags": ["philosophy", "safety"],
    },
    {
        "fingerprint": "pillar-order",
        "text": ("Pillar 1 (Brain) MUST ship before Pillar 2 (Wisdom) which MUST ship "
                 "before Pillar 4 (Auto-Adapt). Don't reorder."),
        "source": "manual", "confidence": 0.85,
        "tags": ["roadmap", "philosophy"],
    },
]

SEED_KILLS = [
    ("UNH",  "Backtester avg -1.35R"),
    ("TEAM", "Backtester avg -1.00R"),
    ("SMCI", "Backtester avg -0.94R + high vol penalty"),
    ("DIS",  "Backtester avg -0.64R"),
    ("SCHW", "Backtester avg -0.64R"),
]


def main():
    existing_text = {L.get("text", "")[:60] for L in load_active_lessons(min_confidence=0.0)}
    added_lessons = 0
    for spec in SEED_LESSONS:
        # Match by first 60 chars to dedupe
        if spec["text"][:60] in existing_text:
            continue
        add_lesson(
            text=spec["text"], source=spec["source"],
            confidence=spec["confidence"], tags=spec["tags"],
            author="bootstrap",
        )
        added_lessons += 1

    added_kills = 0
    for tk, reason in SEED_KILLS:
        if is_killed(tk) is None:
            add_to_kill_list(tk, reason=reason, cool_off_days=180, source="backtester")
            added_kills += 1

    if added_lessons or added_kills:
        print(f"🌱 Bootstrapped wisdom: +{added_lessons} lessons, +{added_kills} kills")
    else:
        print(f"ℹ️  Wisdom already seeded — no changes")
    print(f"   Stats: {stats()}")


if __name__ == "__main__":
    main()
