"""Outcome simulator — v1.1: gap-down fill realism."""
from __future__ import annotations
import pandas as pd
from typing import Dict, Optional


def simulate_outcome(
    forward_bars: pd.DataFrame,
    entry: float,
    stop_loss: float,
    take_profit: float,
    max_hold_days: int = 10,
    side: str = "long",
) -> Dict:
    """v1.1: if gap-down opens BELOW stop, fill at open (worse than stop)."""
    if forward_bars is None or forward_bars.empty:
        return {"exit_status": "no_data", "exit_price": None,
                "days_held": 0, "r_multiple": 0.0, "return_pct": 0.0,
                "exit_date": None}

    risk = abs(entry - stop_loss)
    if risk == 0:
        return {"exit_status": "invalid_sl", "exit_price": None,
                "days_held": 0, "r_multiple": 0.0, "return_pct": 0.0,
                "exit_date": None}

    bars = forward_bars.head(max_hold_days)

    for i, (dt, row) in enumerate(bars.iterrows()):
        open_p = float(row["Open"])
        high = float(row["High"])
        low = float(row["Low"])
        close = float(row["Close"])

        if side == "long":
            # ── v1.1 FIX: gap-down opens below stop → fill at open ──
            if open_p <= stop_loss:
                exit_price = open_p  # worse than stop (gap-down)
                r = (exit_price - entry) / risk
                return {
                    "exit_status": "sl_gap", "exit_price": round(exit_price, 2),
                    "days_held": i + 1, "r_multiple": round(r, 3),
                    "return_pct": round((exit_price - entry) / entry * 100, 2),
                    "exit_date": str(dt.date()),
                }

            # ── v1.1 FIX: gap-up above TP → fill at open (better) ──
            if open_p >= take_profit:
                exit_price = open_p
                r = (exit_price - entry) / risk
                return {
                    "exit_status": "tp_gap", "exit_price": round(exit_price, 2),
                    "days_held": i + 1, "r_multiple": round(r, 3),
                    "return_pct": round((exit_price - entry) / entry * 100, 2),
                    "exit_date": str(dt.date()),
                }

            # Normal intraday SL/TP — conservative SL-first
            sl_hit = low <= stop_loss
            tp_hit = high >= take_profit

            if sl_hit:
                return {
                    "exit_status": "sl_hit", "exit_price": stop_loss,
                    "days_held": i + 1,
                    "r_multiple": round((stop_loss - entry) / risk, 3),
                    "return_pct": round((stop_loss - entry) / entry * 100, 2),
                    "exit_date": str(dt.date()),
                }
            if tp_hit:
                return {
                    "exit_status": "tp_hit", "exit_price": take_profit,
                    "days_held": i + 1,
                    "r_multiple": round((take_profit - entry) / risk, 3),
                    "return_pct": round((take_profit - entry) / entry * 100, 2),
                    "exit_date": str(dt.date()),
                }

    last_close = float(bars.iloc[-1]["Close"])
    last_date = bars.index[-1].date()
    return {
        "exit_status": "max_hold", "exit_price": round(last_close, 2),
        "days_held": len(bars),
        "r_multiple": round((last_close - entry) / risk, 3),
        "return_pct": round((last_close - entry) / entry * 100, 2),
        "exit_date": str(last_date),
    }
