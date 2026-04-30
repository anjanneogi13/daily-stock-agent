"""Adaptive Stop-Loss tighten engine (Phase 2B.5).

Mirror of adaptive_tp: when momentum FADES on a profitable position,
pull SL up close to current price to protect against giveback.

Conditions (ALL must be true):
  - Position profitable (≥ +2%)
  - RSI fading (current < fade_rsi_threshold AND was ≥ peak_rsi_threshold earlier)
  - Vol dying (current vol_ratio < vol_fade_threshold)
  - Cooldown (no recent tighten in last cooldown_min)

SL only moves UP, never down. Each tighten logged for audit.
"""
from datetime import datetime, timedelta
from typing import Tuple, Optional
import json


def should_tighten_sl(entry: float,
                      current_price: float,
                      current_sl: float,
                      current_rsi: Optional[float],
                      peak_rsi: Optional[float],
                      vol_ratio: Optional[float],
                      last_tighten_iso: Optional[str] = None,
                      min_profit_pct: float = 2.0,
                      fade_rsi_threshold: float = 55.0,
                      peak_rsi_threshold: float = 65.0,
                      vol_fade_threshold: float = 0.7,
                      cooldown_min: int = 30,
                      tighten_pct: float = 1.0,
                      now: Optional[datetime] = None) -> Tuple[bool, float, str]:
    """Decide whether to tighten SL on a fading-momentum profitable position.

    Args:
        entry: original entry price
        current_price: latest price
        current_sl: current stop-loss (after any prior trail/tighten)
        current_rsi: latest RSI value (None → no tighten)
        peak_rsi: highest RSI seen in this position (None → no tighten)
        vol_ratio: current volume / 20d avg (None → no tighten)
        last_tighten_iso: ISO timestamp of last tighten (None = never)
        min_profit_pct: must be at least this profitable (default 2%)
        fade_rsi_threshold: RSI dropped below this to confirm fade (default 55)
        peak_rsi_threshold: peak RSI must have been at least this (default 65)
        vol_fade_threshold: vol_ratio dropped below this (default 0.7)
        cooldown_min: min minutes between tightens (default 30)
        tighten_pct: new SL = current_price × (1 - tighten_pct/100) → 1% trail
        now: injectable for tests

    Returns:
        (should_tighten, new_sl, reason)
    """
    if entry <= 0 or current_price <= 0 or current_sl <= 0:
        return False, current_sl, "invalid prices"

    # 1. Must be profitable
    profit_pct = (current_price - entry) / entry * 100
    if profit_pct < min_profit_pct:
        return False, current_sl, f"only +{profit_pct:.1f}% (need +{min_profit_pct}%)"

    # 2. RSI required + must have peaked high
    if current_rsi is None or peak_rsi is None:
        return False, current_sl, "missing rsi data"
    if peak_rsi < peak_rsi_threshold:
        return False, current_sl, f"peak RSI {peak_rsi:.0f} never reached {peak_rsi_threshold}"
    if current_rsi >= fade_rsi_threshold:
        return False, current_sl, f"RSI {current_rsi:.0f} not yet faded (threshold {fade_rsi_threshold})"

    # 3. Vol required + must be dying
    if vol_ratio is None:
        return False, current_sl, "missing vol data"
    if vol_ratio >= vol_fade_threshold:
        return False, current_sl, f"vol {vol_ratio:.2f}x still elevated"

    # 4. Cooldown
    if last_tighten_iso:
        try:
            last = datetime.fromisoformat(last_tighten_iso)
            n = now or datetime.now()
            if (n - last) < timedelta(minutes=cooldown_min):
                mins = (n - last).total_seconds() / 60
                return False, current_sl, f"cooldown ({mins:.0f}min < {cooldown_min}min)"
        except (ValueError, TypeError):
            pass

    # 5. Calculate new SL — must be HIGHER than current (never moves down)
    proposed_sl = round(current_price * (1 - tighten_pct / 100), 2)
    if proposed_sl <= current_sl:
        return False, current_sl, f"proposed ${proposed_sl} not above current ${current_sl}"

    # New SL must still be below current price (sanity)
    if proposed_sl >= current_price:
        return False, current_sl, "proposed SL above price"

    locked_pct = (proposed_sl - entry) / entry * 100
    reason = (f"momentum fading: RSI {current_rsi:.0f} (peak {peak_rsi:.0f}), "
              f"vol {vol_ratio:.2f}x → SL ${current_sl:.2f} → ${proposed_sl:.2f} "
              f"(locks +{locked_pct:.1f}%)")
    return True, proposed_sl, reason


def append_tighten_audit(history_json: str, new_sl: float, reason: str,
                          ts: Optional[str] = None) -> str:
    """Append a tighten event to JSON audit trail."""
    try:
        history = json.loads(history_json) if history_json else []
        if not isinstance(history, list):
            history = []
    except json.JSONDecodeError:
        history = []
    history.append({
        "ts": ts or datetime.now().isoformat(timespec="seconds"),
        "new_sl": round(float(new_sl), 2),
        "reason": reason,
    })
    return json.dumps(history)


def last_tighten_ts(history_json: str) -> Optional[str]:
    """Extract timestamp of most recent tighten event."""
    try:
        history = json.loads(history_json) if history_json else []
        if isinstance(history, list) and history:
            return history[-1].get("ts")
    except (json.JSONDecodeError, KeyError, IndexError):
        pass
    return None
