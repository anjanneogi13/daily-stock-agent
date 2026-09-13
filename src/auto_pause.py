"""
Auto-Pause Instrumentation — Pillar 4 prep v0.1

Computes a pause_signal score (0-10) based on:
  - consecutive losing closed picks
  - rolling 14d drawdown (sum of R-multiples)
  - rolling 30d win rate
  - latest weekly grade

ADVISORY / OBSERVE-ONLY: This module ONLY reports a risk signal. It does
NOT pause anything and the agent does NOT auto-pause. An enforce path
exists but is intentionally deferred (it requires durable pause state
first); until then all output here is advisory only.

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
CLOSED = {"tp_hit", "sl_hit", "expired", "day_close"}


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




def _ensure_dt(r):
    """T23: lazily parse evaluated_on→_evaluated_dt if not pre-cached."""
    if "_evaluated_dt" in r and r["_evaluated_dt"] is not None:
        return r["_evaluated_dt"]
    raw = r.get("evaluated_on") or r.get("pick_date") or ""
    try:
        return datetime.fromisoformat(str(raw)[:10])
    except Exception:
        return None


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
    recent = [r for r in closed if (_ensure_dt(r) or cutoff - timedelta(days=9999)) >= cutoff]
    rs = [_to_float(r.get("r_multiple")) for r in recent]
    rs = [x for x in rs if x is not None]
    if not rs:
        return None
    return round(sum(rs), 2)


def rolling_win_rate(closed: List[Dict], days: int) -> Optional[float]:
    cutoff = datetime.now() - timedelta(days=days)
    recent = [r for r in closed if (_ensure_dt(r) or cutoff - timedelta(days=9999)) >= cutoff]
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
    # T23: defensive defaults — never crash on partial dicts
    score   = result.get("score", 0)
    level   = result.get("level") or classify(score)
    reasons = result.get("reasons") or []
    would_pause = result.get("would_pause", score >= 8)

    lines = [f"🛡 *PAUSE SIGNAL:* {level} ({score}/10)"]
    if reasons:
        for r in reasons:
            lines.append(f"  • {r}")
    if would_pause:
        # Task 4 (#18): advisory-only labeling. The agent does NOT auto-pause
        # (observe-only by default; pause state is non-durable). Say so plainly.
        lines.append("  📊 ADVISORY ONLY — risk signal, not an active pause. The agent does NOT auto-pause.")
    elif not reasons:
        lines.append("  • All clear — no risk flags")
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════
# Pillar 5 GROUP PAUSE (planned May 2026, shipped Sep 2026) — the
# (dimension, value) group-level pause used by main.py's veto hook.
# main.py has imported get_paused_set since May 2026 but the function was
# never landed, so the hook failed with ImportError daily (silently
# caught) — the agent never actually vetoed anything. This implements the
# planned spec (docs/sessions/*may_03_2026*: "Ship Auto-Pause").
#
# Pause rules (conservative, per planned spec):
#   RULE_ZERO_WIN:    n>=5 closed picks AND zero tp_hit wins
#   RULE_LOSS_STREAK: last 3 consecutive closes were sl_hit
#   RULE_NEG_R:       total R <= -5.0 AND n>=4
#
# Observe-mode by default: main.py only filters when AUTO_PAUSE_ENABLED
# env var is "true". Watch-only rows never count; empty group keys are
# never pausable (so untagged picks can't be blanket-vetoed).
# ═══════════════════════════════════════════════════════════════════════
MIN_N_FOR_ZERO_WIN = 5
LOSS_STREAK_LEN = 3
MIN_N_FOR_NEG_R = 4
NEG_R_THRESHOLD = -5.0


def _is_watch_only(row: Dict) -> bool:
    return str(row.get("watch_only") or "").strip().lower() in (
        "1", "true", "yes", "y", "watch", "watch_only")


def _closed_in_window(lookback_days: int, today=None) -> List[Dict]:
    today = today or datetime.now()
    if hasattr(today, "date") is False:  # date -> datetime
        today = datetime(today.year, today.month, today.day)
    cutoff = today - timedelta(days=lookback_days)
    out = []
    for r in _load_closed():
        if _is_watch_only(r):
            continue
        if r.get("actual_return_pct") in (None, ""):
            continue
        if r["_evaluated_dt"] >= cutoff:
            out.append(r)
    return out


def _evaluate_group(items: List[Dict]):
    """Apply pause rules to one group's closes (chronological order)."""
    n = len(items)
    if n == 0:
        return False, None
    wins = sum(1 for r in items if r.get("evaluation_status") == "tp_hit")
    if n >= MIN_N_FOR_ZERO_WIN and wins == 0:
        return True, f"zero_win 0/{n}"
    if n >= LOSS_STREAK_LEN:
        tail = items[-LOSS_STREAK_LEN:]
        if all(r.get("evaluation_status") == "sl_hit" for r in tail):
            return True, f"loss_streak {LOSS_STREAK_LEN}x sl_hit"
    total_r = sum(_to_float(r.get("r_multiple"), 0.0) for r in items)
    if n >= MIN_N_FOR_NEG_R and total_r <= NEG_R_THRESHOLD:
        return True, f"neg_R total={total_r:+.1f}R (n={n})"
    return False, None


def get_paused_set(dimension: str, lookback_days: int = 30, today=None) -> Dict[str, str]:
    """Return {group_value: reason} for paused groups in this dimension."""
    rows = _closed_in_window(lookback_days, today)
    if not rows:
        return {}
    groups: Dict[str, List[Dict]] = {}
    for r in rows:
        key = (r.get(dimension) or "").strip()
        if key:
            groups.setdefault(key, []).append(r)
    paused = {}
    for value, items in groups.items():
        hit, reason = _evaluate_group(items)
        if hit:
            paused[value] = reason
    return paused


def is_group_paused(dimension: str, value: str, lookback_days: int = 30, today=None):
    """Convenience: check a single (dimension, value) pair."""
    if not value:
        return False, None
    reason = get_paused_set(dimension, lookback_days, today).get(value.strip())
    return (reason is not None), reason
