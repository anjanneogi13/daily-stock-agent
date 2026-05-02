"""Point-in-time data slicer — prevents look-ahead bias.

CRITICAL: All historical data must be sliced so that on simulated
day D, only data with timestamp < D is visible to the algo.
"""
from __future__ import annotations
import pandas as pd
from datetime import date, datetime
from typing import Optional


def slice_pit(df: pd.DataFrame, as_of: date | datetime | str,
              min_history_days: int = 60) -> Optional[pd.DataFrame]:
    """Slice a price DataFrame to only include data BEFORE as_of.

    Args:
        df: OHLCV DataFrame indexed by date
        as_of: cutoff date (exclusive). Algo can see data up to as_of-1.
        min_history_days: minimum bars required to return data

    Returns:
        Sliced DataFrame, or None if insufficient history.
    """
    if df is None or df.empty:
        return None

    if isinstance(as_of, str):
        as_of = pd.Timestamp(as_of).date()
    elif isinstance(as_of, datetime):
        as_of = as_of.date()

    # Ensure index is datetime
    if not isinstance(df.index, pd.DatetimeIndex):
        df = df.copy()
        df.index = pd.to_datetime(df.index)

    cutoff = pd.Timestamp(as_of)
    sliced = df[df.index < cutoff]

    if len(sliced) < min_history_days:
        return None

    return sliced


def get_forward_window(df: pd.DataFrame, as_of: date | str,
                       n_days: int = 10) -> Optional[pd.DataFrame]:
    """Get N trading days AFTER as_of (for outcome simulation).

    This is the ONLY place where future data is used — for measuring
    what actually happened to a pick we 'made' on as_of.
    """
    if df is None or df.empty:
        return None

    if isinstance(as_of, str):
        as_of = pd.Timestamp(as_of).date()

    if not isinstance(df.index, pd.DatetimeIndex):
        df = df.copy()
        df.index = pd.to_datetime(df.index)

    cutoff = pd.Timestamp(as_of)
    forward = df[df.index >= cutoff].head(n_days)

    if len(forward) == 0:
        return None

    return forward
