"""
Agent Memoir — the agent's persistent identity & narrative self-knowledge.

Created 2026-05-04 in response to founder insight:
  "Agent should not forget its mistakes and learnings, the wins,
   and what its task is supposed to be."

Unlike raw event journals, the memoir is a NARRATED self-portrait the agent
rewrites every night. It gives identity continuity across nightly runs.

Output: data/agent_memoir.json
"""
from __future__ import annotations
import json
import csv
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional

MEMOIR_PATH       = Path("data/agent_memoir.json")
PICKS_LOG         = Path("data/picks_log.csv")
LEARNING_JOURNAL  = Path("data/learning_journal.jsonl")

MISSION_STATEMENT = (
    "I am the daily-stock-agent. My purpose is to help Anjan trade US stocks "
    "profitably with controlled risk. I learn from every trade — wins teach me "
    "what works; losses teach me what to avoid. I will be honest about my "
    "performance, never hide my mistakes, and improve a little bit every night."
)


def _safe_float(v) -> Optional[float]:
    try:
        return float(v) if v not in (None, "", "none", "null") else None
    except (ValueError, TypeError):
        return None


def _load_closed_picks() -> List[Dict]:
    if not PICKS_LOG.exists():
        return []
    rows = []
    with PICKS_LOG.open() as f:
        for r in csv.DictReader(f):
            if r.get("evaluation_status") in ("tp_hit", "sl_hit", "expired"):
                rows.append(r)
    return rows


def _load_learning_events() -> List[Dict]:
    if not LEARNING_JOURNAL.exists():
        return []
    out = []
    with LEARNING_JOURNAL.open() as f:
        for ln in f:
            ln = ln.strip()
            if not ln: continue
            try:
                out.append(json.loads(ln))
            except Exception:
                pass
    return out


def _biggest_win(closed: List[Dict]) -> Optional[Dict]:
    cands = [(r, _safe_float(r.get("r_multiple"))) for r in closed]
    cands = [(r, rm) for r, rm in cands if rm is not None and rm > 0]
    if not cands:
        return None
    best, rm = max(cands, key=lambda x: x[1])
    return {
        "ticker": best.get("ticker"),
        "date":   best.get("pick_date"),
        "r_multiple": round(rm, 2),
        "return_pct": _safe_float(best.get("actual_return_pct")),
        "regime":   best.get("regime"),
        "narrative": (
            f"On {best.get('pick_date')}, I picked {best.get('ticker')} "
            f"in a {best.get('regime') or 'unknown'} regime. It hit "
            f"{rm:.2f}× my risked amount — my best trade so far. "
            f"This is the kind of setup I should look for more of."
        ),
    }


def _biggest_loss(closed: List[Dict]) -> Optional[Dict]:
    cands = [(r, _safe_float(r.get("r_multiple"))) for r in closed]
    cands = [(r, rm) for r, rm in cands if rm is not None and rm < 0]
    if not cands:
        return None
    worst, rm = min(cands, key=lambda x: x[1])
    d2e = worst.get("days_to_earnings", "")
    earn_warn = ""
    try:
        if d2e and int(d2e) <= 7:
            earn_warn = f" The stock was only {d2e} days from earnings — possibly too close."
    except (ValueError, TypeError):
        pass
    return {
        "ticker": worst.get("ticker"),
        "date":   worst.get("pick_date"),
        "r_multiple": round(rm, 2),
        "return_pct": _safe_float(worst.get("actual_return_pct")),
        "regime":   worst.get("regime"),
        "lesson_learned": (
            f"I lost {abs(rm):.2f}× on {worst.get('ticker')} ({worst.get('pick_date')}) "
            f"in a {worst.get('regime') or 'unknown'} regime.{earn_warn} "
            f"I should remember this when similar setups appear."
        ),
    }


def _summarize_recent_learning(events: List[Dict], days: int = 7) -> Dict:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    recent = []
    for e in events:
        ts = e.get("ts", "")
        try:
            t = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            if t >= cutoff:
                recent.append(e)
        except Exception:
            pass
    return {
        "window_days": days,
        "weight_changes":   sum(1 for e in recent if e.get("kind") == "weight_applied"),
        "lessons_promoted": sum(1 for e in recent if e.get("kind") == "lesson_promoted"),
        "nightly_runs":     sum(1 for e in recent if e.get("kind") == "nightly_brain_run"),
    }


def write_memoir() -> Dict:
    closed = _load_closed_picks()
    events = _load_learning_events()
    wins   = sum(1 for r in closed if (_safe_float(r.get("r_multiple")) or 0) > 0)
    losses = sum(1 for r in closed if (_safe_float(r.get("r_multiple")) or 0) < 0)
    n      = len(closed)
    win_rate = (wins / n) if n else 0.0

    if n < 30:
        current_focus = (
            f"I have only {n} closed trades. I need at least 30 before my "
            f"learning becomes statistically meaningful. Until then I am in "
            f"OBSERVATION MODE — collecting data, not making big changes."
        )
    elif win_rate < 0.40:
        current_focus = (
            f"My win rate is {win_rate:.0%}, below my target of 45%. "
            f"I need to study my losses more carefully and tighten my filters."
        )
    elif win_rate >= 0.50:
        current_focus = (
            f"My win rate is {win_rate:.0%} which is healthy. I should focus "
            f"on improving my R-multiple (size of wins vs losses)."
        )
    else:
        current_focus = (
            f"My win rate is {win_rate:.0%} — acceptable. I am refining my "
            f"per-pattern × per-regime statistics to find my true edge."
        )

    memoir = {
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "identity":     MISSION_STATEMENT,
        "lifetime_stats": {
            "closed_trades": n,
            "wins":          wins,
            "losses":        losses,
            "win_rate":      round(win_rate, 3),
        },
        "biggest_win":     _biggest_win(closed),
        "biggest_loss":    _biggest_loss(closed),
        "current_focus":   current_focus,
        "what_im_proud_of": (
            "I report my own bad performance honestly instead of hiding it. "
            "I refuse to make weight changes when I have too little data. "
            "I run every night and learn a little, even when nothing dramatic happens."
        ),
        "recent_learning_7d": _summarize_recent_learning(events),
        "promise_to_anjan": (
            "I will keep learning. I will not forget my mistakes. I will tell you "
            "the truth about how I'm doing — even when the truth isn't flattering."
        ),
    }

    MEMOIR_PATH.parent.mkdir(parents=True, exist_ok=True)
    MEMOIR_PATH.write_text(json.dumps(memoir, indent=2))
    return memoir


if __name__ == "__main__":
    m = write_memoir()
    print(json.dumps(m, indent=2))
