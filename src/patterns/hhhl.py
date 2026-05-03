"""Higher-Highs Higher-Lows + Lower-Highs Lower-Lows detectors.

Definition (HHHL = bullish trend confirmation):
  Over the last 20 bars, identify swing-pivot highs and swing-pivot lows
  (a pivot = local max/min within ±k bars). Pattern fires when the most
  recent 2 pivot-highs and 2 pivot-lows are each strictly increasing.

Confidence = combination of:
  - n_pivots found (more = stronger trend)
  - average gap between consecutive pivots
"""
from __future__ import annotations
from typing import List, Optional, Tuple

from .base import PatternDetector, Match


def _pivot_highs(highs: List[float], k: int = 2) -> List[Tuple[int, float]]:
    out = []
    for i in range(k, len(highs) - k):
        window = highs[i-k : i+k+1]
        if highs[i] == max(window) and window.count(highs[i]) == 1:
            out.append((i, highs[i]))
    return out


def _pivot_lows(lows: List[float], k: int = 2) -> List[Tuple[int, float]]:
    out = []
    for i in range(k, len(lows) - k):
        window = lows[i-k : i+k+1]
        if lows[i] == min(window) and window.count(lows[i]) == 1:
            out.append((i, lows[i]))
    return out


class HHHLDetector(PatternDetector):
    name = "hhhl"
    min_bars = 20
    direction = "bullish"

    def detect(self, df) -> Optional[Match]:
        if not self._enough_bars(df):
            return None
        highs = df["High"].tail(self.min_bars).tolist()
        lows  = df["Low"].tail(self.min_bars).tolist()
        ph = _pivot_highs(highs)
        pl = _pivot_lows(lows)
        if len(ph) < 2 or len(pl) < 2:
            return None
        # last 2 pivot highs strictly increasing
        if not (ph[-1][1] > ph[-2][1]):
            return None
        # last 2 pivot lows strictly increasing
        if not (pl[-1][1] > pl[-2][1]):
            return None
        # confidence: scaled by (n_pivots, gap%)
        n = min(len(ph), len(pl))
        gap_h = (ph[-1][1] - ph[-2][1]) / max(ph[-2][1], 1e-9)
        gap_l = (pl[-1][1] - pl[-2][1]) / max(pl[-2][1], 1e-9)
        conf = min(0.95, 0.5 + 0.1 * n + 5 * (gap_h + gap_l))
        return Match(
            pattern=self.name,
            confidence=round(conf, 3),
            lookback=self.min_bars,
            trigger={
                "last_high": ph[-1][1], "prev_high": ph[-2][1],
                "last_low":  pl[-1][1], "prev_low":  pl[-2][1],
                "n_pivots":  n,
            },
            notes="bullish trend continuation",
        )


class LHLLDetector(PatternDetector):
    """Lower-Highs Lower-Lows (bearish mirror)."""
    name = "lhll"
    min_bars = 20
    direction = "bearish"

    def detect(self, df) -> Optional[Match]:
        if not self._enough_bars(df):
            return None
        highs = df["High"].tail(self.min_bars).tolist()
        lows  = df["Low"].tail(self.min_bars).tolist()
        ph = _pivot_highs(highs)
        pl = _pivot_lows(lows)
        if len(ph) < 2 or len(pl) < 2:
            return None
        if not (ph[-1][1] < ph[-2][1]):  return None
        if not (pl[-1][1] < pl[-2][1]):  return None
        n = min(len(ph), len(pl))
        gap_h = (ph[-2][1] - ph[-1][1]) / max(ph[-2][1], 1e-9)
        gap_l = (pl[-2][1] - pl[-1][1]) / max(pl[-2][1], 1e-9)
        conf = min(0.95, 0.5 + 0.1 * n + 5 * (gap_h + gap_l))
        return Match(
            pattern=self.name,
            confidence=round(conf, 3),
            lookback=self.min_bars,
            trigger={
                "last_high": ph[-1][1], "prev_high": ph[-2][1],
                "last_low":  pl[-1][1], "prev_low":  pl[-2][1],
                "n_pivots":  n,
            },
            notes="bearish trend continuation",
        )
