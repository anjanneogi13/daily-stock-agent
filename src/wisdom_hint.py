"""T24: per-pick wisdom hint formatter (used by Telegram pick blocks).

Kept standalone so tests can import it without triggering the
top-level sys.exit() that scripts/send_telegram.py performs when
TELEGRAM_BOT_TOKEN is unset.
"""
from typing import Optional

try:
    from src.wisdom_base import lessons_for_ticker as _lft
except Exception:
    _lft = lambda *a, **k: []


def wisdom_hint(ticker: Optional[str], min_confidence: float = 0.7) -> str:
    """Return a one-line Telegram-ready hint for a ticker, or '' if none."""
    if not ticker:
        return ""
    try:
        ls = _lft(ticker, min_confidence=min_confidence)
    except Exception:
        return ""
    if not ls:
        return ""
    best = max(ls, key=lambda L: L.get("confidence", 0))
    text = str(best.get("text", "")).strip()
    if not text:
        return ""
    if len(text) > 90:
        text = text[:87] + "…"
    return f"   🧠 _{text}_"
