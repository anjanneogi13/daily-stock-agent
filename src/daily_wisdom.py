"""Daily wisdom hint — runs hypothesis engine on quality-floor picks.

Surfaces edges/drags discovered in outcome data, with explicit
sample-size warnings so future-you doesn't over-read small-n results.

Usage:
    from src.daily_wisdom import generate_daily_wisdom
    text = generate_daily_wisdom()       # plain text for Telegram
    print(text)

Or CLI:
    python -m src.daily_wisdom

Designed to be safe to run on n=0: returns "no data yet" message
rather than crashing.
"""
from __future__ import annotations
import csv
from pathlib import Path
from typing import List, Dict

from src.data_quality import filter_to_quality, DATA_QUALITY_FLOOR


PICKS_LOG = Path("data/picks_log.csv")

# Sample-size honesty thresholds
N_ANECDOTAL  = 20   # below this: don't draw conclusions
N_DIRECTIONAL = 50  # 20-50: directional only
N_CONFIDENT  = 100  # 50-100: useful, 100+: confident


def _confidence_label(n: int) -> str:
    if n < N_ANECDOTAL:    return f"⏳ ANECDOTAL (n={n}, need {N_ANECDOTAL}+ for direction)"
    if n < N_DIRECTIONAL:  return f"📊 DIRECTIONAL (n={n}, need {N_DIRECTIONAL}+ for confidence)"
    if n < N_CONFIDENT:    return f"📈 USEFUL (n={n})"
    return f"✅ CONFIDENT (n={n})"


def _row_to_journal_format(r: Dict) -> Dict:
    """Convert picks_log row → hypothesis engine input format."""
    try:
        rmul = float(r["r_multiple"])
    except (KeyError, ValueError, TypeError):
        return None
    outcome = "win" if rmul > 0 else "loss"
    # Bucket score
    score_str = r.get("score", "")
    try:
        s = float(score_str)
        if   s >= 0.79: sb = "very_high"
        elif s >= 0.72: sb = "high"
        elif s >= 0.66: sb = "mid"
        else:           sb = "low"
    except (ValueError, TypeError):
        sb = "unknown"
    return {
        "ticker":  r.get("ticker", ""),
        "outcome": outcome,
        "r_multiple": rmul,
        "signals": {
            "regime":      r.get("regime", "unknown") or "unknown",
            "trade_type":  r.get("trade_type", "unknown") or "unknown",
            "score_bucket": sb,
            "tag":         (r.get("tag") or "none").split(" / ")[0].upper() or "none",
            "is_monster":  "yes" if r.get("is_monster") in ("True","true","1") else "no",
        }
    }


def _load_quality_closed_picks() -> List[Dict]:
    """Load post-floor picks with recorded r_multiple."""
    if not PICKS_LOG.exists():
        return []
    rows = list(csv.DictReader(open(PICKS_LOG)))
    clean = filter_to_quality(rows)
    closed = []
    for r in clean:
        j = _row_to_journal_format(r)
        if j is not None:
            closed.append(j)
    return closed


def generate_daily_wisdom() -> str:
    """Return human-readable wisdom report."""
    closed = _load_quality_closed_picks()
    n = len(closed)

    lines = []
    lines.append("═" * 60)
    lines.append("🧠 DAILY WISDOM — Hypothesis Engine Report")
    lines.append(f"   Floor: pick_date >= {DATA_QUALITY_FLOOR.isoformat()} (excludes pre-gate fossils)")
    lines.append("═" * 60)
    lines.append("")
    lines.append(f"Sample: {_confidence_label(n)}")
    lines.append("")

    if n == 0:
        lines.append("No closed picks above quality floor yet. Wisdom engine")
        lines.append("will activate once outcomes start being recorded for")
        lines.append("post-floor picks.")
        lines.append("═" * 60)
        return "\n".join(lines)

    if n < N_ANECDOTAL:
        lines.append(f"⚠ Sample too small for statistical claims.")
        lines.append(f"  Showing observations only; do NOT change strategy on this.")
        lines.append("")

    # Run hypothesis engine
    try:
        from src.hypothesis_engine import analyze, format_report
        result = analyze(closed)
        report = format_report(result)
        lines.append(report)
    except Exception as e:
        lines.append(f"⚠ hypothesis_engine error: {e}")
        # Fallback: simple win-rate
        wins = sum(1 for c in closed if c["outcome"] == "win")
        wr = wins / n if n else 0
        lines.append(f"Fallback win rate: {wins}/{n} = {wr:.0%}")

    lines.append("")
    lines.append("═" * 60)
    return "\n".join(lines)


if __name__ == "__main__":
    print(generate_daily_wisdom())
