"""Telegram message deduplication.

Prevents sending the same message multiple times within a window.
Solves the 'workflow ran 5x → Telegram got 14 picks' problem.

Usage:
    from src.dedup_sender import should_send, mark_sent

    msg = "Daily Stock Picks ..."
    if should_send(msg, window_minutes=60):
        send_telegram(msg)
        mark_sent(msg)
"""
import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict

DEDUP_PATH = Path("data/telegram_sent.json")


def _content_hash(text: str) -> str:
    """Hash the message content (first 500 chars to ignore minor price drift)."""
    # Strip whitespace and take first 500 chars to allow for price drift in same pick
    normalized = " ".join(text.split())[:500]
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]


def _load_sent() -> Dict[str, str]:
    """Load sent message log: {hash: iso_timestamp}."""
    if not DEDUP_PATH.exists():
        return {}
    try:
        return json.loads(DEDUP_PATH.read_text())
    except (json.JSONDecodeError, ValueError):
        return {}


def _save_sent(sent: Dict[str, str]) -> None:
    """Save sent log atomically (temp file + rename)."""
    DEDUP_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = DEDUP_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(sent, indent=2))
    tmp.replace(DEDUP_PATH)


def _purge_old(sent: Dict[str, str], window_minutes: int) -> Dict[str, str]:
    """Remove entries older than window_minutes. Keeps file small."""
    cutoff = datetime.now() - timedelta(minutes=window_minutes * 24)  # keep 24x window
    fresh = {}
    for h, ts in sent.items():
        try:
            sent_at = datetime.fromisoformat(ts)
            if sent_at >= cutoff:
                fresh[h] = ts
        except (ValueError, TypeError):
            continue  # skip corrupted entries
    return fresh


def should_send(text: str, window_minutes: int = 60) -> bool:
    """Return True if message hasn't been sent within window_minutes."""
    if not text or not text.strip():
        return False
    h = _content_hash(text)
    sent = _load_sent()
    if h not in sent:
        return True
    try:
        last_sent = datetime.fromisoformat(sent[h])
    except (ValueError, TypeError):
        return True  # corrupted entry → send
    age_min = (datetime.now() - last_sent).total_seconds() / 60
    return age_min >= window_minutes


def mark_sent(text: str, window_minutes: int = 60) -> None:
    """Record that a message was sent. Auto-purges old entries."""
    if not text or not text.strip():
        return
    h = _content_hash(text)
    sent = _load_sent()
    sent[h] = datetime.now().isoformat()
    sent = _purge_old(sent, window_minutes)
    _save_sent(sent)


def stats() -> dict:
    """Return current dedup state for diagnostics."""
    sent = _load_sent()
    return {
        "total_tracked": len(sent),
        "path": str(DEDUP_PATH),
    }