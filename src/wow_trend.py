"""T46 / Pillar 6: Week-over-Week trend.

Compares the trailing-7d window vs the prior-7d window (8-14 days ago)
across the headline metrics: trades, win-rate, mean R, total R, alpha.

Surfaces 'getting better / worse / flat' for the weekly review.
"""
from __future__ import annotations
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional


def _to_float(v) -> Optional[float]:
    try: return float(v)
    except (TypeError, ValueError): return None


def _within(rec: Dict, start: datetime, end: datetime) -> bool:
    """end-exclusive."""
    for key in ("evaluated_on", "pick_date"):
        v = rec.get(key)
        if not v: continue
        try:
            dt = datetime.fromisoformat(str(v).split("T")[0])
            return start <= dt < end
        except Exception:
            continue
    return False


def _summarize(picks: List[Dict]) -> Dict:
    n = len(picks)
    if n == 0:
        return {"n": 0, "wins": 0, "win_rate": 0.0,
                "mean_r": 0.0, "total_r": 0.0, "alpha": 0.0}
    rs    = [r for r in (_to_float(p.get("r_multiple"))    for p in picks) if r is not None]
    alphs = [a for a in (_to_float(p.get("alpha_pct"))      for p in picks) if a is not None]
    wins  = sum(1 for r in rs if r > 0)
    return {
        "n":        n,
        "wins":     wins,
        "win_rate": round(wins / max(len(rs),1), 3),
        "mean_r":   round(sum(rs)/len(rs), 3) if rs else 0.0,
        "total_r":  round(sum(rs), 3) if rs else 0.0,
        "alpha":    round(sum(alphs)/len(alphs), 3) if alphs else 0.0,
    }


def compare(picks: List[Dict], today: Optional[datetime] = None) -> Dict:
    """Return {this_week, last_week, deltas}."""
    today = today or datetime.now()
    end_this  = today
    start_this = today - timedelta(days=7)
    start_last = today - timedelta(days=14)
    this = [p for p in (picks or []) if _within(p, start_this, end_this)]
    last = [p for p in (picks or []) if _within(p, start_last, start_this)]
    s_this = _summarize(this)
    s_last = _summarize(last)
    deltas = {
        "n":        s_this["n"]        - s_last["n"],
        "win_rate": round(s_this["win_rate"] - s_last["win_rate"], 3),
        "mean_r":   round(s_this["mean_r"]   - s_last["mean_r"],   3),
        "total_r":  round(s_this["total_r"]  - s_last["total_r"],  3),
        "alpha":    round(s_this["alpha"]    - s_last["alpha"],    3),
    }
    return {"this_week": s_this, "last_week": s_last, "deltas": deltas}


def _arrow(d: float, good_positive: bool = True) -> str:
    if abs(d) < 1e-6:  return "→"
    up = d > 0
    if good_positive:
        return "🟢↑" if up else "🔴↓"
    return "🔴↑" if up else "🟢↓"


def format_footer(cmp: Dict) -> str:
    """Telegram-ready WoW block. Returns '' if no prior-week baseline."""
    last = cmp["last_week"]
    if last["n"] == 0:
        return ""
    d = cmp["deltas"]
    t = cmp["this_week"]
    lines = []
    lines.append(
        f"• Trades: {t['n']} (vs {last['n']}, {d['n']:+d}) "
    )
    lines.append(
        f"• WR: {t['win_rate']:.0%} {_arrow(d['win_rate'])} "
        f"({d['win_rate']:+.0%})"
    )
    lines.append(
        f"• Mean R: {t['mean_r']:+.2f} {_arrow(d['mean_r'])} "
        f"({d['mean_r']:+.2f})"
    )
    lines.append(
        f"• Total R: {t['total_r']:+.2f} {_arrow(d['total_r'])} "
        f"({d['total_r']:+.2f})"
    )
    if last["alpha"] or t["alpha"]:
        lines.append(
            f"• Alpha vs SPY: {t['alpha']:+.2f}% {_arrow(d['alpha'])} "
            f"({d['alpha']:+.2f}%)"
        )
    return "\n".join(lines)
