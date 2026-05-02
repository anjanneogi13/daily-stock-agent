"""Auto-pause module — Pillar 5 (Self-Awareness) foundation.

Reads picks_log.csv and identifies (dimension, value) groups that should
be auto-paused based on outcome history.

Pause rules (conservative, configurable):
  RULE_ZERO_WIN:    n>=5 closed picks AND win_rate==0
  RULE_LOSS_STREAK: last 3 consecutive picks were sl_hit
  RULE_NEG_R:       total_R <= -5R AND n>=4

Mirrors EV-gate pattern: env var AUTO_PAUSE_ENABLED gates enforcement.
Defaults to OBSERVE-MODE (logs but doesn't filter) — same safe rollout.

Usage:
    from src.auto_pause import get_paused_set, is_paused
    paused = get_paused_set('tag')   # {'SEMI / AI': 'zero_win 0/7', ...}
    blocked, reason = is_paused('tag', 'SEMI / AI')

Window: only considers picks closed in the last `lookback_days` (default 30).
"""
import csv
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

PICKS_LOG = Path("data/picks_log.csv")
CLOSED_STATUSES = {"tp_hit", "sl_hit", "expired"}
DEFAULT_LOOKBACK_DAYS = 30

# Conservative defaults — tunable later
MIN_N_FOR_ZERO_WIN = 5
LOSS_STREAK_LEN = 3
MIN_N_FOR_NEG_R = 4
NEG_R_THRESHOLD = -5.0


def _parse_date(s: str):
    if not s:
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        return None


def _load_closed(lookback_days: int = DEFAULT_LOOKBACK_DAYS, today: date | None = None) -> list[dict]:
    if not PICKS_LOG.exists():
        return []
    today = today or date.today()
    cutoff = today - timedelta(days=lookback_days)
    with PICKS_LOG.open() as f:
        rows = list(csv.DictReader(f))
    out = []
    for r in rows:
        if r.get("evaluation_status") not in CLOSED_STATUSES:
            continue
        if r.get("actual_return_pct") in (None, ""):
            continue
        d = _parse_date(r.get("evaluated_on") or r.get("pick_date") or "")
        if d is None or d < cutoff:
            continue
        out.append(r)
    out.sort(key=lambda r: (r.get("evaluated_on") or r.get("pick_date") or ""))
    return out


def _r_value(r: dict) -> float:
    try:
        return float(r.get("r_multiple") or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _evaluate_group(items: list[dict]) -> tuple[bool, str | None]:
    """Apply pause rules to a single group's items (chronological)."""
    n = len(items)
    if n == 0:
        return False, None

    wins = sum(1 for r in items if r.get("evaluation_status") == "tp_hit")
    if n >= MIN_N_FOR_ZERO_WIN and wins == 0:
        return True, f"zero_win 0/{n}"

    # Last K consecutive sl_hit?
    if n >= LOSS_STREAK_LEN:
        tail = items[-LOSS_STREAK_LEN:]
        if all(r.get("evaluation_status") == "sl_hit" for r in tail):
            return True, f"loss_streak {LOSS_STREAK_LEN}x sl_hit"

    total_r = sum(_r_value(r) for r in items)
    if n >= MIN_N_FOR_NEG_R and total_r <= NEG_R_THRESHOLD:
        return True, f"neg_R total={total_r:+.1f}R (n={n})"

    return False, None


def get_paused_set(dimension: str,
                   lookback_days: int = DEFAULT_LOOKBACK_DAYS,
                   today: date | None = None) -> dict[str, str]:
    """Return {value: reason} for all paused groups in this dimension."""
    rows = _load_closed(lookback_days, today)
    if not rows:
        return {}
    groups: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        key = (r.get(dimension) or "").strip()
        if key:
            groups[key].append(r)
    paused = {}
    for value, items in groups.items():
        is_pause, reason = _evaluate_group(items)
        if is_pause:
            paused[value] = reason
    return paused


def is_paused(dimension: str, value: str,
              lookback_days: int = DEFAULT_LOOKBACK_DAYS,
              today: date | None = None) -> tuple[bool, str | None]:
    """Convenience: check a single (dimension, value) pair."""
    if not value:
        return False, None
    paused = get_paused_set(dimension, lookback_days, today)
    reason = paused.get(value.strip())
    return (reason is not None), reason


def format_paused_summary(dimensions=("tag", "trade_type", "regime"),
                          lookback_days: int = DEFAULT_LOOKBACK_DAYS,
                          today: date | None = None) -> str:
    """Plain-text summary for dashboard / Telegram."""
    lines = [f"🛑 AUTO-PAUSE STATUS (last {lookback_days}d)"]
    any_paused = False
    for dim in dimensions:
        paused = get_paused_set(dim, lookback_days, today)
        if paused:
            any_paused = True
            for value, reason in paused.items():
                lines.append(f"   ❌ {dim}={value!r}: {reason}")
    if not any_paused:
        lines.append("   ✅ no groups currently paused")
    return "\n".join(lines) + "\n"
