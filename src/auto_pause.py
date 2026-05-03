"""
Auto-Pause Instrumentation — Pillar 4 prep v0.1

Computes a pause_signal score (0-10) based on:
  - consecutive losing closed picks
  - rolling 14d drawdown (sum of R-multiples)
  - rolling 30d win rate
  - latest weekly grade

OBSERVE-MODE: This module ONLY reports. It does NOT pause anything.
Manual flip from observe → enforce planned for Wed 2026-05-06.

Score interpretation:
  0-2  🟢 GREEN     normal ops
  3-5  🟡 ELEVATED  watch closely
  6-7  🟠 AMBER     consider 50% size cut
  8-10 🔴 RED       pause recommended (would stop if enforced)
"""
import csv
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional


def _is_enforced() -> bool:
    """Read config/auto_pause.json — single source of truth for enforce flag."""
    try:
        from src.pause_state import load_config
        return bool(load_config().get("enforced", False))
    except Exception:
        return False


PICKS_LOG = Path("data/picks_log.csv")
CLOSED = {"tp_hit", "sl_hit", "expired"}


def _to_float(v, default=None):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _load_closed() -> List[Dict]:
    if not PICKS_LOG.exists():
        return []
    out = []
    with PICKS_LOG.open() as f:
        for r in csv.DictReader(f):
            if r.get("evaluation_status") not in CLOSED:
                continue
            try:
                d = datetime.strptime(r.get("evaluated_on") or r.get("pick_date", ""),
                                       "%Y-%m-%d")
            except ValueError:
                continue
            r["_evaluated_dt"] = d
            out.append(r)
    out.sort(key=lambda r: r["_evaluated_dt"])
    return out


def consecutive_losses(closed: List[Dict]) -> int:
    """How many losses in a row, ending with the most recent close."""
    n = 0
    for r in reversed(closed):
        if r.get("evaluation_status") == "sl_hit":
            n += 1
        else:
            break
    return n


def rolling_r(closed: List[Dict], days: int) -> Optional[float]:
    """Sum of R-multiples in the last N calendar days."""
    if not closed:
        return None
    cutoff = datetime.now() - timedelta(days=days)
    recent = [r for r in closed if r["_evaluated_dt"] >= cutoff]
    rs = [_to_float(r.get("r_multiple")) for r in recent]
    rs = [x for x in rs if x is not None]
    if not rs:
        return None
    return round(sum(rs), 2)


def rolling_win_rate(closed: List[Dict], days: int) -> Optional[float]:
    cutoff = datetime.now() - timedelta(days=days)
    recent = [r for r in closed if r["_evaluated_dt"] >= cutoff]
    if not recent:
        return None
    wins = sum(1 for r in recent if r.get("evaluation_status") == "tp_hit")
    return round(wins / len(recent), 3)


def compute_score(closed: Optional[List[Dict]] = None) -> Dict:
    """Compute the pause_signal score with full breakdown."""
    if closed is None:
        closed = _load_closed()

    streak = consecutive_losses(closed)
    dd_14  = rolling_r(closed, 14)
    wr_30  = rolling_win_rate(closed, 30)

    score = 0
    reasons = []

    # 1. Consecutive losses
    if streak >= 5:
        score += 4; reasons.append(f"🔴 {streak} consecutive losses")
    elif streak >= 3:
        score += 2; reasons.append(f"🟡 {streak} consecutive losses")
    elif streak >= 2:
        score += 1; reasons.append(f"🟢 {streak} losses in a row")

    # 2. Drawdown 14d
    if dd_14 is not None:
        if dd_14 <= -8:
            score += 4; reasons.append(f"🔴 14d drawdown {dd_14:+.1f}R")
        elif dd_14 <= -5:
            score += 3; reasons.append(f"🟠 14d drawdown {dd_14:+.1f}R")
        elif dd_14 <= -2:
            score += 1; reasons.append(f"🟡 14d drawdown {dd_14:+.1f}R")

    # 3. 30d win rate
    if wr_30 is not None:
        if wr_30 < 0.20:
            score += 2; reasons.append(f"🟠 30d WR {wr_30:.0%}")
        elif wr_30 < 0.30:
            score += 1; reasons.append(f"🟡 30d WR {wr_30:.0%}")

    score = min(score, 10)
    return {
        "score":    score,
        "level":    classify(score),
        "reasons":  reasons,
        "streak":   streak,
        "dd_14":    dd_14,
        "wr_30":    wr_30,
        "would_pause": score >= 8,
        "enforced": _is_enforced(),
    }


def classify(score: int) -> str:
    if score >= 8: return "🔴 RED"
    if score >= 6: return "🟠 AMBER"
    if score >= 3: return "🟡 ELEVATED"
    return "🟢 GREEN"


def format_summary(result: Dict) -> str:
    """One-line summary suitable for Telegram daily message."""
    lines = []
    lines.append(f"🛡 *PAUSE SIGNAL:* {result['level']} ({result['score']}/10)")
    if result["reasons"]:
        for r in result["reasons"]:
            lines.append(f"  • {r}")
    if result["would_pause"]:
        lines.append("  ⚠️ Enforce-mode would PAUSE for 3 days (currently observe-mode)")
    elif not result["reasons"]:
        lines.append("  • All clear — no risk flags")
    return "\n".join(lines)
