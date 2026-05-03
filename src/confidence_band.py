"""T30: Per-pick confidence band — fuses score + edge/drag + lessons
into one glanceable emoji shown next to each pick in Telegram.

Decision matrix (top-down, first match wins):

  drag + score < 1.0    → 🚫 AVOID
  drag                  → ⚠  CAUTION
  edge + score > 1.2    → 🔥 HIGH
  score > 1.2           → ✅ GOOD
  score < 0.8           → ⚠  CAUTION
  default               → ✅ GOOD

`drag` and `edge` are derived purely from pattern_hint() output so
this module stays decoupled from the wisdom internals.
"""
from typing import Optional


# Confidence band emojis
HIGH    = "🔥"
GOOD    = "✅"
CAUTION = "⚠"
AVOID   = "🚫"


def _has_drag(pattern_hint_text: str) -> bool:
    """pattern_hint emits '⚠' for drag matches."""
    return "⚠" in (pattern_hint_text or "")


def _has_edge(pattern_hint_text: str) -> bool:
    """pattern_hint emits '✨' for edge matches."""
    return "✨" in (pattern_hint_text or "")


def confidence_band(score: float,
                    pattern_hint_text: Optional[str] = "",
                    wisdom_hint_text: Optional[str] = "") -> str:
    """Return one of {🔥, ✅, ⚠, 🚫}.

    Args:
        score:             composite score (typical range 0.5–2.0)
        pattern_hint_text: full pattern_hint() return string
        wisdom_hint_text:  full wisdom_hint() return string (presence
                           tilts a borderline pick toward CAUTION)
    """
    try:
        s = float(score)
    except (TypeError, ValueError):
        s = 0.0

    drag      = _has_drag(pattern_hint_text)
    edge      = _has_edge(pattern_hint_text)
    has_lesson = bool((wisdom_hint_text or "").strip())

    # Drag is a hard signal — always demote
    if drag and s < 1.0:
        return AVOID
    if drag:
        return CAUTION

    # Edge boosts high-scorers to 🔥
    if edge and s > 1.2:
        return HIGH

    # Pure score-based bands
    if s > 1.2:
        return GOOD
    if s < 0.8:
        return CAUTION

    # Borderline + lesson present → nudge to CAUTION (be safe)
    if has_lesson and s < 1.0:
        return CAUTION

    return GOOD


def band_label(emoji: str) -> str:
    """Map emoji → human label (for tests/logs)."""
    return {
        HIGH:    "HIGH",
        GOOD:    "GOOD",
        CAUTION: "CAUTION",
        AVOID:   "AVOID",
    }.get(emoji, "UNKNOWN")
