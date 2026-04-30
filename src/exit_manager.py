"""Scale-out exit tier engine (Phase 2B.1).

Splits a position into 3 tiers:
- TP1: lock partial profit early (1.5×ATR)
- TP2: bulk profit target (2.5×ATR) — same as old single-TP
- TP3: trail final third for momentum runs (handled by trailing_stop module later)
"""
from typing import Dict


def compute_exit_tiers(entry: float, atr: float, qty: int,
                        trade_type: str = "swing") -> Dict:
    """Return a 3-tier scale-out plan.

    Args:
        entry: entry price
        atr: ATR value (volatility)
        qty: total share quantity
        trade_type: "swing" or "day" (day uses tighter mults)

    Returns:
        {
          "tp1": price, "tp2": price, "tp3_mode": "trail",
          "qty_t1": int, "qty_t2": int, "qty_t3": int,
          "atr_mult_tp1": float, "atr_mult_tp2": float,
        }
    """
    # ATR multipliers per trade type
    if trade_type == "day":
        mult_tp1, mult_tp2 = 0.75, 1.5
    else:  # swing (default)
        mult_tp1, mult_tp2 = 1.5, 2.5

    # ATR fallback if missing
    if not atr or atr <= 0:
        atr = entry * 0.02

    tp1 = round(entry + atr * mult_tp1, 2)
    tp2 = round(entry + atr * mult_tp2, 2)

    # Quantity split: 1/3, 1/3, remainder (handles non-divisible-by-3)
    qty = max(1, int(qty))
    qty_t1 = qty // 3
    qty_t2 = qty // 3
    qty_t3 = qty - qty_t1 - qty_t2

    # Edge case: qty < 3 → put all in tier 2 (single exit)
    if qty < 3:
        qty_t1 = 0
        qty_t2 = qty
        qty_t3 = 0

    return {
        "tp1": tp1,
        "tp2": tp2,
        "tp3_mode": "trail",
        "qty_t1": qty_t1,
        "qty_t2": qty_t2,
        "qty_t3": qty_t3,
        "atr_mult_tp1": mult_tp1,
        "atr_mult_tp2": mult_tp2,
    }
