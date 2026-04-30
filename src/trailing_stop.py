"""Trailing stop engine (Phase 2B.2).

Activates after position is +activation_pct in profit. Then SL = peak × (1 - trail_pct/100).
SL only moves UP, never down. Locks partial gains while letting winners run.
"""
from typing import Tuple


def compute_trailing_sl(entry: float,
                         peak_price: float,
                         current_sl: float,
                         activation_pct: float = 3.0,
                         trail_pct: float = 2.0) -> Tuple[float, bool]:
    """Compute new trailing SL.

    Args:
        entry: original entry price
        peak_price: highest price seen since entry (MFE peak)
        current_sl: current stop-loss (could be original or already-trailed)
        activation_pct: % gain required before trailing activates (default 3%)
        trail_pct: how far below peak to trail (default 2%)

    Returns:
        (new_sl, did_raise)
        - new_sl: updated SL (always >= current_sl)
        - did_raise: True if SL was moved UP this call
    """
    if entry <= 0 or peak_price <= 0:
        return current_sl, False

    # Activation threshold: peak must be >= entry × (1 + activation_pct/100)
    activation_price = entry * (1 + activation_pct / 100)
    if peak_price < activation_price:
        return current_sl, False

    # Compute candidate trailing SL
    candidate_sl = round(peak_price * (1 - trail_pct / 100), 2)

    # SL never moves down — only up
    if candidate_sl > current_sl:
        return candidate_sl, True
    return current_sl, False


def trail_status(entry: float, peak_price: float, current_sl: float,
                 original_sl: float) -> dict:
    """Return human-readable trail state for logs/Telegram.

    Returns:
        {
          "active": bool,
          "peak_gain_pct": float,   # how much above entry the peak is
          "locked_gain_pct": float, # gain locked in by trailed SL (vs entry)
          "sl_raised_pct": float,   # how much SL moved from original
        }
    """
    peak_gain = ((peak_price - entry) / entry * 100) if entry > 0 else 0.0
    locked_gain = ((current_sl - entry) / entry * 100) if entry > 0 else 0.0
    sl_raised = ((current_sl - original_sl) / original_sl * 100) if original_sl > 0 else 0.0
    return {
        "active": current_sl > original_sl,
        "peak_gain_pct": round(peak_gain, 2),
        "locked_gain_pct": round(locked_gain, 2),
        "sl_raised_pct": round(sl_raised, 2),
    }
