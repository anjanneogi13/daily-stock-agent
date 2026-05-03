"""T44 / Pillar 4: Learning Journal — every brain mutation in one place.

Append-only log of:
  - lesson_added       (manual / hypothesis / book / backtester)
  - lesson_deactivated (lesson_gc, kill list)
  - pattern_promoted   (auto_promote)
  - weight_applied     (weight_applier)
  - kill_listed        (kill_list addition)

One line, machine-readable. Used by weekly review to render
'🧠 Brain learned X this week' summary.
"""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

JOURNAL = Path("data/learning_journal.jsonl")


def log(kind: str, **payload) -> Dict:
    """Append a learning event. kind ∈ {lesson_added, lesson_deactivated,
    pattern_promoted, weight_applied, kill_listed}.
    """
    rec = {
        "ts":   datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "kind": kind,
        **payload,
    }
    JOURNAL.parent.mkdir(parents=True, exist_ok=True)
    with JOURNAL.open("a") as f:
        f.write(json.dumps(rec) + "\n")
    return rec


def read(days: Optional[int] = None) -> list[Dict]:
    if not JOURNAL.exists():
        return []
    out = []
    cutoff = None
    if days is not None:
        cutoff = datetime.now(timezone.utc).timestamp() - days * 86400
    for line in JOURNAL.read_text().splitlines():
        if not line.strip(): continue
        try:
            r = json.loads(line)
        except Exception:
            continue
        if cutoff is not None:
            try:
                ts = datetime.fromisoformat(r["ts"].replace("Z","+00:00")).timestamp()
            except Exception:
                continue
            if ts < cutoff:
                continue
        out.append(r)
    return out


def summary(days: int = 7) -> Dict:
    """Counts by kind for the last N days."""
    rows = read(days=days)
    by_kind: Dict[str, int] = {}
    for r in rows:
        k = r.get("kind", "other")
        by_kind[k] = by_kind.get(k, 0) + 1
    return {"days": days, "total": len(rows), "by_kind": by_kind}
