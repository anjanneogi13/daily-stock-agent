"""
Wisdom Base — Pillar 2 v0.1

Persistent store of learnings the brain reads before picking
and writes to after reflection.

Three artifacts (data/wisdom/):
  - lessons.jsonl   : curated text learnings with provenance
  - patterns.jsonl  : empirical "if X then Y" rules (from hypothesis_engine)
  - kill_list.json  : cooled-off tickers/setups (auto-expire)

OBSERVE-MODE: Wisdom INFORMS the brain via warnings; never auto-blocks.
Auto-block in v0.2 once we trust the signals.
"""
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional

ROOT = Path("data/wisdom")
ROOT.mkdir(parents=True, exist_ok=True)

LESSONS  = ROOT / "lessons.jsonl"
PATTERNS = ROOT / "patterns.jsonl"
KILL     = ROOT / "kill_list.json"


# ═══════════════════════════════════════════════════════════════
# Lessons — curated text learnings with confidence + source
# ═══════════════════════════════════════════════════════════════
def add_lesson(text: str,
               source: str = "manual",
               confidence: float = 0.5,
               tags: Optional[List[str]] = None,
               author: str = "system") -> Dict:
    """Append a new lesson. Returns the lesson record."""
    rec = {
        "ts":         datetime.now().isoformat(timespec="seconds"),
        "text":       text,
        "source":     source,         # "manual" | "hypothesis" | "backtester" | "evaluator"
        "confidence": float(confidence),  # 0.0-1.0
        "tags":       tags or [],
        "author":     author,
        "active":     True,
    }
    with LESSONS.open("a") as f:
        f.write(json.dumps(rec) + "\n")
    return rec


def load_active_lessons(min_confidence: float = 0.5) -> List[Dict]:
    """Return lessons with active=True and confidence >= threshold."""
    if not LESSONS.exists():
        return []
    out = []
    with LESSONS.open() as f:
        for line in f:
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if r.get("active", True) and r.get("confidence", 0) >= min_confidence:
                out.append(r)
    return out


def deactivate_lesson(text_substring: str) -> int:
    """Mark all lessons containing substring as active=False. Returns count."""
    if not LESSONS.exists():
        return 0
    rows, n = [], 0
    with LESSONS.open() as f:
        for line in f:
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if text_substring.lower() in r.get("text", "").lower() and r.get("active", True):
                r["active"] = False
                r["deactivated_at"] = datetime.now().isoformat(timespec="seconds")
                n += 1
            rows.append(r)
    with LESSONS.open("w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    return n


# ═══════════════════════════════════════════════════════════════
# Patterns — empirical rules from hypothesis_engine
# ═══════════════════════════════════════════════════════════════
def add_pattern(signal: str,
                bucket: str,
                effect: str,
                win_rate: float,
                sample_n: int,
                p_value: float,
                source: str = "hypothesis") -> Dict:
    """Record an empirical pattern. effect ∈ {edge, drag}."""
    rec = {
        "ts":        datetime.now().isoformat(timespec="seconds"),
        "signal":    signal,
        "bucket":    bucket,
        "effect":    effect,
        "win_rate":  round(float(win_rate), 3),
        "sample_n":  int(sample_n),
        "p_value":   round(float(p_value), 4),
        "source":    source,
        "active":    True,
    }
    with PATTERNS.open("a") as f:
        f.write(json.dumps(rec) + "\n")
    return rec


def load_active_patterns() -> List[Dict]:
    if not PATTERNS.exists():
        return []
    out = []
    with PATTERNS.open() as f:
        for line in f:
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if r.get("active", True):
                out.append(r)
    return out


# ═══════════════════════════════════════════════════════════════
# Kill list — cooled-off tickers with expiry
# ═══════════════════════════════════════════════════════════════
def _load_kill() -> Dict:
    if not KILL.exists():
        return {}
    try:
        return json.loads(KILL.read_text())
    except Exception:
        return {}


def _save_kill(d: Dict) -> None:
    KILL.write_text(json.dumps(d, indent=2))


def add_to_kill_list(ticker: str,
                     reason: str,
                     cool_off_days: int = 14,
                     source: str = "manual") -> Dict:
    """Cool off a ticker for N days. Returns the entry."""
    d = _load_kill()
    expires_at = (datetime.now() + timedelta(days=cool_off_days)).isoformat(timespec="seconds")
    d[ticker.upper()] = {
        "reason":     reason,
        "added_at":   datetime.now().isoformat(timespec="seconds"),
        "expires_at": expires_at,
        "source":     source,
    }
    _save_kill(d)
    return d[ticker.upper()]


def get_kill_list() -> Dict[str, Dict]:
    """Return active kill list (auto-expires past entries)."""
    d = _load_kill()
    now = datetime.now()
    active = {}
    changed = False
    for tk, entry in d.items():
        try:
            exp = datetime.fromisoformat(entry.get("expires_at", ""))
        except Exception:
            exp = now + timedelta(days=365)  # malformed → keep as safety net
        if exp >= now:
            active[tk] = entry
        else:
            changed = True
    if changed:
        _save_kill(active)
    return active


def is_killed(ticker: str) -> Optional[Dict]:
    """Return kill entry if ticker is currently on the kill list, else None."""
    return get_kill_list().get(ticker.upper())


def remove_from_kill_list(ticker: str) -> bool:
    d = _load_kill()
    if ticker.upper() in d:
        del d[ticker.upper()]
        _save_kill(d)
        return True
    return False


# ═══════════════════════════════════════════════════════════════
# Stats / summary
# ═══════════════════════════════════════════════════════════════
def stats() -> Dict:
    return {
        "active_lessons":  len(load_active_lessons()),
        "active_patterns": len(load_active_patterns()),
        "kill_list_size":  len(get_kill_list()),
    }
