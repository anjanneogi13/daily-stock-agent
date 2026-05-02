"""Simulate what would have happened to a pick given historical bars.

Conservative assumptions:
  - If both SL and TP touched on same day → SL filled first (pessimistic)
  - Entry assumed at next-day open (slippage = open - prev close)
  - Max hold = configurable (default 10 days swing, 1 day day-trade)
"""
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
    """Simulate the lifecycle of a single pick.

    Returns dict with:
      - exit_status: 'sl_hit' | 'tp_hit' | 'max_hold'
      - exit_price: float
      - days_held: int
      - r_multiple: (exit - entry) / (entry - sl)  for long
      - return_pct: float
      - exit_date: str
    """
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
        high = float(row["High"])
        low = float(row["Low"])
        close = float(row["Close"])

        if side == "long":
            # CONSERVATIVE: if SL and TP both touched, SL wins
            sl_hit = low <= stop_loss
            tp_hit = high >= take_profit

            if sl_hit:
                exit_price = stop_loss
                r = (exit_price - entry) / risk
                return {
                    "exit_status": "sl_hit", "exit_price": exit_price,
                    "days_held": i + 1, "r_multiple": round(r, 3),
                    "return_pct": round((exit_price - entry) / entry * 100, 2),
                    "exit_date": str(dt.date()),
                }
            if tp_hit:
                exit_price = take_profit
                r = (exit_price - entry) / risk
                return {
                    "exit_status": "tp_hit", "exit_price": exit_price,
                    "days_held": i + 1, "r_multiple": round(r, 3),
                    "return_pct": round((exit_price - entry) / entry * 100, 2),
                    "exit_date": str(dt.date()),
                }

    # Max hold reached — exit at last close
    last_close = float(bars.iloc[-1]["Close"])
    last_date = bars.index[-1].date()
    r = (last_close - entry) / risk
    return {
        "exit_status": "max_hold", "exit_price": last_close,
        "days_held": len(bars), "r_multiple": round(r, 3),
        "return_pct": round((last_close - entry) / entry * 100, 2),
        "exit_date": str(last_date),
    }
