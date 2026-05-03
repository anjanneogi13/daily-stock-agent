"""T33: Wisdom coverage stat for daily Telegram footer.

After every morning push, append a 1-line readout:

    🧠 Wisdom: 6/10 picks tagged (60%) · 4 lessons · 2 patterns

Tells you at a glance how often the brain is firing.
Low coverage → wisdom base needs growing.
High coverage → system has opinions on most picks.
"""
from typing import Dict, List

try:
    from .wisdom_hint import wisdom_hint, pattern_hint
except Exception:
    wisdom_hint = lambda *a, **k: ""
    pattern_hint = lambda *a, **k: ""


def coverage(rows: List[dict]) -> Dict:
    """Compute coverage stats over a list of pick rows.

    Returns:
      {total, tagged, lessons, patterns, pct}
    """
    total = len(rows or [])
    if total == 0:
        return {"total": 0, "tagged": 0, "lessons": 0,
                "patterns": 0, "pct": 0.0}

    n_lessons = n_patterns = n_tagged = 0
    for r in rows:
        try:
            wh = wisdom_hint(r.get("ticker"), sector=r.get("sector"))
        except Exception:
            wh = ""
        try:
            ph = pattern_hint(r)
        except Exception:
            ph = ""
        has_wh = bool((wh or "").strip())
        has_ph = bool((ph or "").strip())
        if has_wh:
            n_lessons += 1
        if has_ph:
            n_patterns += 1
        if has_wh or has_ph:
            n_tagged += 1

    return {
        "total":    total,
        "tagged":   n_tagged,
        "lessons":  n_lessons,
        "patterns": n_patterns,
        "pct":      round(n_tagged / total * 100, 1),
    }


def format_footer(stats: Dict) -> str:
    """Telegram-ready 1-line footer. Returns '' if no picks."""
    if not stats or stats.get("total", 0) == 0:
        return ""
    return (
        f"🧠 _Wisdom: {stats['tagged']}/{stats['total']} picks tagged "
        f"({stats['pct']:.0f}%) · {stats['lessons']} lesson"
        f"{'s' if stats['lessons'] != 1 else ''} · "
        f"{stats['patterns']} pattern"
        f"{'s' if stats['patterns'] != 1 else ''}_"
    )
