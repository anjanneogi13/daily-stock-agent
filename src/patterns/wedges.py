"""Falling Wedge (bullish) + Rising Wedge (bearish).

Both lines slope in the SAME direction but converge:
  - Falling wedge: both highs+lows declining, but lows decline slower
                   → support catches up → bullish breakout
  - Rising wedge:  both highs+lows rising, but highs rise slower
                   → resistance caps gains → bearish breakdown
"""
from __future__ import annotations
from typing import Optional
from .base import PatternDetector, Match
from .triangles import _linreg, _slope_pct_per_bar


class _WedgeBase(PatternDetector):
    min_bars = 20
    LOOKBACK = 20
    MIN_SLOPE = 0.15    # both lines must slope ≥ 0.15%/bar
    MIN_CONVERGENCE = 0.10  # gap between slopes must be ≥ 0.10%/bar

    def _fit(self, df):
        sub = df.tail(self.LOOKBACK)
        highs = sub["High"].tolist()
        lows  = sub["Low"].tolist()
        sh, _ = _linreg(highs)
        sl, _ = _linreg(lows)
        mh = sum(highs)/len(highs)
        ml = sum(lows)/len(lows)
        return _slope_pct_per_bar(sh, mh), _slope_pct_per_bar(sl, ml)


class FallingWedgeDetector(_WedgeBase):
    name = "falling_wedge"
    direction = "bullish"

    def detect(self, df) -> Optional[Match]:
        if not self._enough_bars(df):
            return None
        sh, sl = self._fit(df)
        # Both negative, highs falling FASTER than lows (converging upward)
        if sh > -self.MIN_SLOPE: return None
        if sl > -self.MIN_SLOPE: return None
        if sl <= sh: return None  # lows must fall LESS than highs (sl > sh, both negative)
        if abs(sh) - abs(sl) < self.MIN_CONVERGENCE: return None
        conf = min(0.90, 0.55 + (abs(sh) - abs(sl)) * 0.6)
        return Match(
            pattern=self.name,
            confidence=round(conf, 3),
            lookback=self.LOOKBACK,
            trigger={
                "resistance_slope_pct": round(sh, 3),
                "support_slope_pct":    round(sl, 3),
            },
            notes="falling wedge — bullish reversal watch",
        )


class RisingWedgeDetector(_WedgeBase):
    name = "rising_wedge"
    direction = "bearish"

    def detect(self, df) -> Optional[Match]:
        if not self._enough_bars(df):
            return None
        sh, sl = self._fit(df)
        # Both positive, lows rising FASTER than highs (converging upward into ceiling)
        if sh < self.MIN_SLOPE: return None
        if sl < self.MIN_SLOPE: return None
        if sl <= sh: return None  # lows must rise MORE than highs
        if sl - sh < self.MIN_CONVERGENCE: return None
        conf = min(0.90, 0.55 + (sl - sh) * 0.6)
        return Match(
            pattern=self.name,
            confidence=round(conf, 3),
            lookback=self.LOOKBACK,
            trigger={
                "resistance_slope_pct": round(sh, 3),
                "support_slope_pct":    round(sl, 3),
            },
            notes="rising wedge — bearish reversal watch",
        )
