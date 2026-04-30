"""Adaptive Take-Profit raising engine (Phase 2B.3).

When a position is screaming higher with strong momentum, the original TP becomes
a cap that limits gains. This module decides when to push TP UP based on:
  - Already significantly profitable (price > entry × gain_threshold)
  - Strong momentum (RSI > rsi_threshold)
  - Institutional buying (vol_ratio > vol_threshold)
  - Debounced (no recent raise in last cooldown_min)

TP only moves UP, never down. Each raise is logged for audit.
"""
from datetime import datetime
from typing import Tuple, Optional, List
import json


def should_raise_tp(entry: float,
                     current_price: float,
                     current_tp: float,
                     current_rsi: Optional[float],
                     vol_ratio: Optional[float],
                     last_raise_iso: Optional[str] = None,
                     gain_threshold_pct: float = 5.0,
                     rsi_threshold: float = 70.0,
                     vol_threshold: float = 1.8,
                     cooldown_min: int = 60,
                     headroom_pct: float = 5.0,
                     now: Optional[datetime] = None) -> Tuple[bool, float, str]:
    """Decide whether to raise TP and by how much.

    Args:
        entry: original entry price
        current_price: latest price
        current_tp: current take-profit
        current_rsi: latest RSI value (None → no raise)
        vol_ratio: today's volume / 20d avg (None → no raise)
        last_raise_iso: ISO timestamp of last raise (None = never raised)
        gain_threshold_pct: minimum % gain required (default 5%)
        rsi_threshold: minimum RSI to confirm momentum (default 70)
        vol_threshold: minimum vol ratio (default 1.8x)
        cooldown_min: min minutes between raises (default 60)
        headroom_pct: new TP = current_price × (1 + headroom_pct/100)
        now: injectable for tests (defaults to datetime.now())

    Returns:
        (should_raise, new_tp, reason)
        - should_raise: True if all conditions met
        - new_tp: proposed new TP (= current_tp if no raise)
        - reason: human-readable string for logs/Telegram
    """
    now = now or datetime.now()

    if entry <= 0 or current_price <= 0 or current_tp <= 0:
        return False, current_tp, "invalid inputs"

    # Condition 1: enough gain
    gain_pct = (current_price - entry) / entry * 100
    if gain_pct < gain_threshold_pct:
        return False, current_tp, f"gain only +{gain_pct:.1f}% (need +{gain_threshold_pct}%)"

    # Condition 2: strong RSI
    if current_rsi is None or current_rsi < rsi_threshold:
        return False, current_tp, f"RSI {current_rsi} below {rsi_threshold}"

    # Condition 3: volume confirmation
    if vol_ratio is None or vol_ratio < vol_threshold:
        return False, current_tp, f"vol {vol_ratio}x below {vol_threshold}x"

    # Condition 4: cooldown
    if last_raise_iso:
        try:
            last_dt = datetime.fromisoformat(last_raise_iso)
            elapsed_min = (now - last_dt).total_seconds() / 60
            if elapsed_min < cooldown_min:
                return False, current_tp, f"cooldown ({elapsed_min:.0f}min < {cooldown_min}min)"
        except ValueError:
            pass  # malformed timestamp → ignore

    # Compute new TP — current_price × (1 + headroom_pct/100)
    candidate_tp = round(current_price * (1 + headroom_pct / 100), 2)

    # TP only moves UP
    if candidate_tp <= current_tp:
        return False, current_tp, f"candidate ${candidate_tp} not above current ${current_tp}"

    reason = (f"+{gain_pct:.1f}% gain, RSI {current_rsi:.0f}, vol {vol_ratio:.1f}× "
              f"→ TP ${current_tp:.2f} → ${candidate_tp:.2f}")
    return True, candidate_tp, reason


def append_raise_audit(existing_json: str, new_tp: float, reason: str,
                        now: Optional[datetime] = None) -> str:
    """Append a raise event to the JSON audit trail (stored in tp_raises CSV col).

    Returns: updated JSON string (list of {ts, new_tp, reason} dicts)
    """
    now = now or datetime.now()
    try:
        history = json.loads(existing_json) if existing_json else []
        if not isinstance(history, list):
            history = []
    except (json.JSONDecodeError, TypeError):
        history = []
    history.append({
        "ts": now.isoformat(timespec="seconds"),
        "new_tp": new_tp,
        "reason": reason,
    })
    return json.dumps(history)


def last_raise_ts(audit_json: str) -> Optional[str]:
    """Extract timestamp of most recent raise from audit JSON."""
    try:
        history = json.loads(audit_json) if audit_json else []
        if history and isinstance(history, list):
            return history[-1].get("ts")
    except (json.JSONDecodeError, TypeError):
        pass
    return None
