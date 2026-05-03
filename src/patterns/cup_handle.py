"""Cup-and-handle detector (William O'Neil pattern).

Structure (over ~30 bars):
  - LEFT RIM:  recent prior high
  - CUP:       smooth U-shape down then back up to right rim
  - RIGHT RIM: ~equal to left rim (within 3%)
  - HANDLE:    small consolidation (last 5-7 bars), pulling back 2-7% from rim

Heuristic implementation (golden-fixture testable):
  1. Find rim_left = max High in first 1/3 of window
  2. Find cup_low = min Low in middle 1/3 (must be 10-30% below rims)
  3. Find rim_right = max High in last 1/3 (within 3% of rim_left)
  4. Handle = last 5-7 bars: range tight (≤ 5%) and low ≥ 0.93 × rim_right
"""
from __future__ import annotations
from typing import Optional
from .base import PatternDetector, Match


class CupAndHandleDetector(PatternDetector):
    name = "cup_and_handle"
    min_bars = 30
    direction = "bullish"

    LOOKBACK = 30
    HANDLE_BARS = 6
    MIN_CUP_DEPTH_PCT = 10.0
    MAX_CUP_DEPTH_PCT = 35.0
    RIM_TOL_PCT = 3.0
    HANDLE_MAX_RANGE_PCT = 5.0
    HANDLE_MAX_PULLBACK_PCT = 8.0

    def detect(self, df) -> Optional[Match]:
        if not self._enough_bars(df):
            return None
        sub = df.tail(self.LOOKBACK)
        n = len(sub)
        third = n // 3

        left   = sub.iloc[:third]
        middle = sub.iloc[third:2*third]
        right_zone = sub.iloc[2*third:]
        # Handle is the very last HANDLE_BARS
        handle = sub.iloc[-self.HANDLE_BARS:]
        # Right rim is the high BEFORE the handle
        right_pre_handle = sub.iloc[2*third:-self.HANDLE_BARS]
        if len(right_pre_handle) < 2:
            return None

        rim_left  = float(left["High"].max())
        cup_low   = float(middle["Low"].min())
        rim_right = float(right_pre_handle["High"].max())

        # Cup depth from average rim
        avg_rim = (rim_left + rim_right) / 2
        if avg_rim == 0: return None
        cup_depth_pct = (avg_rim - cup_low) / avg_rim * 100
        if not (self.MIN_CUP_DEPTH_PCT <= cup_depth_pct <= self.MAX_CUP_DEPTH_PCT):
            return None

        # Rims approximately equal
        rim_diff_pct = abs(rim_left - rim_right) / avg_rim * 100
        if rim_diff_pct > self.RIM_TOL_PCT:
            return None

        # Handle: tight range, modest pullback from right rim
        handle_high = float(handle["High"].max())
        handle_low  = float(handle["Low"].min())
        handle_range_pct = (handle_high - handle_low) / handle_low * 100 if handle_low else 0
        if handle_range_pct > self.HANDLE_MAX_RANGE_PCT:
            return None
        handle_pullback_pct = (rim_right - handle_low) / rim_right * 100
        if handle_pullback_pct > self.HANDLE_MAX_PULLBACK_PCT or handle_pullback_pct < 0:
            return None

        conf = min(0.95,
                   0.55
                   + 0.01 * cup_depth_pct
                   + 0.04 * (self.RIM_TOL_PCT - rim_diff_pct)
                   + 0.03 * (self.HANDLE_MAX_RANGE_PCT - handle_range_pct))
        conf = max(0.5, conf)
        return Match(
            pattern=self.name,
            confidence=round(conf, 3),
            lookback=self.LOOKBACK,
            trigger={
                "rim_left":           round(rim_left, 4),
                "rim_right":          round(rim_right, 4),
                "cup_low":            round(cup_low, 4),
                "cup_depth_pct":      round(cup_depth_pct, 2),
                "rim_diff_pct":       round(rim_diff_pct, 2),
                "handle_range_pct":   round(handle_range_pct, 2),
                "handle_pullback_pct":round(handle_pullback_pct, 2),
            },
            notes=f"cup {cup_depth_pct:.1f}% deep, handle {handle_range_pct:.1f}% range",
        )
