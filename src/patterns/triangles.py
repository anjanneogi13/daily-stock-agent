"""Triangle detectors: ascending, descending, symmetric.

We fit two trendlines via least-squares over the last N bars:
  - resistance line through the highs
  - support line    through the lows

Then classify by slopes:
  - ascending:  resistance flat (|slope| small), support rising
  - descending: resistance falling, support flat
  - symmetric:  resistance falling, support rising (converging)

Confidence scales with: # of touches near each line, slope magnitude.
"""
from __future__ import annotations
from typing import Optional, Tuple
from .base import PatternDetector, Match


def _linreg(ys) -> Tuple[float, float]:
    """Simple least-squares fit: y = m*x + b. Returns (slope, intercept)."""
    n = len(ys)
    if n < 2: return (0.0, ys[0] if ys else 0.0)
    xs = list(range(n))
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    num = sum((xs[i] - mean_x) * (ys[i] - mean_y) for i in range(n))
    den = sum((x - mean_x) ** 2 for x in xs)
    if den == 0: return (0.0, mean_y)
    m = num / den
    b = mean_y - m * mean_x
    return (m, b)


def _slope_pct_per_bar(slope: float, mean_y: float) -> float:
    """Slope as % of mean per bar — comparable across price ranges."""
    if mean_y == 0: return 0.0
    return slope / mean_y * 100


class _TriangleBase(PatternDetector):
    min_bars = 20
    LOOKBACK = 20
    FLAT_THRESHOLD = 0.15    # |slope| < 0.15%/bar = flat
    SLOPE_THRESHOLD = 0.20   # |slope| > 0.20%/bar = clearly trending

    def _fit(self, df):
        sub = df.tail(self.LOOKBACK)
        highs = sub["High"].tolist()
        lows  = sub["Low"].tolist()
        sh, _ = _linreg(highs)
        sl, _ = _linreg(lows)
        mean_h = sum(highs) / len(highs)
        mean_l = sum(lows)  / len(lows)
        return (
            _slope_pct_per_bar(sh, mean_h),
            _slope_pct_per_bar(sl, mean_l),
            mean_h, mean_l,
        )


class AscendingTriangleDetector(_TriangleBase):
    name = "ascending_triangle"
    direction = "bullish"

    def detect(self, df) -> Optional[Match]:
        if not self._enough_bars(df):
            return None
        sh, sl, mh, ml = self._fit(df)
        # resistance flat, support rising
        if abs(sh) > self.FLAT_THRESHOLD:   return None
        if sl < self.SLOPE_THRESHOLD:        return None
        conf = min(0.95, 0.55 + sl * 0.5 + (self.FLAT_THRESHOLD - abs(sh)) * 0.5)
        return Match(
            pattern=self.name,
            confidence=round(conf, 3),
            lookback=self.LOOKBACK,
            trigger={
                "resistance_slope_pct": round(sh, 3),
                "support_slope_pct":    round(sl, 3),
            },
            notes="flat resistance, rising support — bullish breakout watch",
        )


class DescendingTriangleDetector(_TriangleBase):
    name = "descending_triangle"
    direction = "bearish"

    def detect(self, df) -> Optional[Match]:
        if not self._enough_bars(df):
            return None
        sh, sl, mh, ml = self._fit(df)
        # support flat, resistance falling
        if abs(sl) > self.FLAT_THRESHOLD:    return None
        if sh > -self.SLOPE_THRESHOLD:       return None
        conf = min(0.95, 0.55 + abs(sh) * 0.5 + (self.FLAT_THRESHOLD - abs(sl)) * 0.5)
        return Match(
            pattern=self.name,
            confidence=round(conf, 3),
            lookback=self.LOOKBACK,
            trigger={
                "resistance_slope_pct": round(sh, 3),
                "support_slope_pct":    round(sl, 3),
            },
            notes="falling resistance, flat support — bearish breakdown watch",
        )


class SymmetricTriangleDetector(_TriangleBase):
    name = "symmetric_triangle"
    direction = "neutral"

    def detect(self, df) -> Optional[Match]:
        if not self._enough_bars(df):
            return None
        sh, sl, mh, ml = self._fit(df)
        # converging: resistance falling, support rising
        if sh > -self.SLOPE_THRESHOLD:       return None
        if sl < self.SLOPE_THRESHOLD:        return None
        # roughly symmetric
        if abs(abs(sh) - sl) > 0.30:         return None
        conf = min(0.90, 0.55 + (abs(sh) + sl) * 0.4)
        return Match(
            pattern=self.name,
            confidence=round(conf, 3),
            lookback=self.LOOKBACK,
            trigger={
                "resistance_slope_pct": round(sh, 3),
                "support_slope_pct":    round(sl, 3),
            },
            notes="converging trendlines — directional breakout pending",
        )
