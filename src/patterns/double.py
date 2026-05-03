"""Double Top / Double Bottom detectors.

Double Top (bearish reversal):
  - Two distinct peaks within 30 bars at ~equal height (within 2%)
  - A clear trough between them ≥ 5% below the peaks
  - Today is at/near the second peak (or just rolled over)

Double Bottom = mirror.
"""
from __future__ import annotations
from typing import Optional, List, Tuple
from .base import PatternDetector, Match


def _local_peaks(values: List[float], k: int = 3) -> List[Tuple[int, float]]:
    out = []
    for i in range(k, len(values) - k):
        window = values[i-k:i+k+1]
        if values[i] == max(window) and window.count(values[i]) == 1:
            out.append((i, values[i]))
    return out


def _local_troughs(values: List[float], k: int = 3) -> List[Tuple[int, float]]:
    out = []
    for i in range(k, len(values) - k):
        window = values[i-k:i+k+1]
        if values[i] == min(window) and window.count(values[i]) == 1:
            out.append((i, values[i]))
    return out


class DoubleTopDetector(PatternDetector):
    name = "double_top"
    min_bars = 30
    direction = "bearish"

    LOOKBACK = 30
    PEAK_TOL_PCT = 2.0     # peaks must be within 2% of each other
    MIN_TROUGH_DROP_PCT = 5.0
    MIN_PEAK_SEPARATION = 5  # peaks at least 5 bars apart

    def detect(self, df) -> Optional[Match]:
        if not self._enough_bars(df):
            return None
        sub = df.tail(self.LOOKBACK)
        highs = sub["High"].tolist()
        lows  = sub["Low"].tolist()
        peaks = _local_peaks(highs)
        if len(peaks) < 2:
            return None
        # Take the two highest peaks
        peaks_sorted = sorted(peaks, key=lambda p: -p[1])[:2]
        peaks_sorted.sort(key=lambda p: p[0])  # back to chronological
        i1, p1 = peaks_sorted[0]
        i2, p2 = peaks_sorted[1]
        if abs(i2 - i1) < self.MIN_PEAK_SEPARATION:
            return None
        avg = (p1 + p2) / 2
        if abs(p1 - p2) / avg * 100 > self.PEAK_TOL_PCT:
            return None
        # Trough between peaks
        between = lows[i1:i2+1]
        if not between:
            return None
        trough = min(between)
        drop_pct = (avg - trough) / avg * 100
        if drop_pct < self.MIN_TROUGH_DROP_PCT:
            return None
        # Last peak should be near the end (still active pattern)
        if i2 < len(highs) - 10:
            return None
        conf = min(0.95, 0.55 + 0.04 * drop_pct + 0.05 * (self.PEAK_TOL_PCT - abs(p1-p2)/avg*100))
        return Match(
            pattern=self.name,
            confidence=round(conf, 3),
            lookback=self.LOOKBACK,
            trigger={
                "peak1": round(p1, 4),
                "peak2": round(p2, 4),
                "trough": round(trough, 4),
                "drop_pct": round(drop_pct, 2),
            },
            notes=f"two peaks at ~{avg:.2f}, trough -{drop_pct:.1f}%",
        )


class DoubleBottomDetector(PatternDetector):
    name = "double_bottom"
    min_bars = 30
    direction = "bullish"

    LOOKBACK = 30
    BOTTOM_TOL_PCT = 2.0
    MIN_PEAK_RISE_PCT = 5.0
    MIN_BOTTOM_SEPARATION = 5

    def detect(self, df) -> Optional[Match]:
        if not self._enough_bars(df):
            return None
        sub = df.tail(self.LOOKBACK)
        highs = sub["High"].tolist()
        lows  = sub["Low"].tolist()
        troughs = _local_troughs(lows)
        if len(troughs) < 2:
            return None
        troughs_sorted = sorted(troughs, key=lambda t: t[1])[:2]
        troughs_sorted.sort(key=lambda t: t[0])
        i1, b1 = troughs_sorted[0]
        i2, b2 = troughs_sorted[1]
        if abs(i2 - i1) < self.MIN_BOTTOM_SEPARATION:
            return None
        avg = (b1 + b2) / 2
        if abs(b1 - b2) / avg * 100 > self.BOTTOM_TOL_PCT:
            return None
        between = highs[i1:i2+1]
        if not between:
            return None
        peak = max(between)
        rise_pct = (peak - avg) / avg * 100
        if rise_pct < self.MIN_PEAK_RISE_PCT:
            return None
        if i2 < len(lows) - 10:
            return None
        conf = min(0.95, 0.55 + 0.04 * rise_pct + 0.05 * (self.BOTTOM_TOL_PCT - abs(b1-b2)/avg*100))
        return Match(
            pattern=self.name,
            confidence=round(conf, 3),
            lookback=self.LOOKBACK,
            trigger={
                "bottom1": round(b1, 4),
                "bottom2": round(b2, 4),
                "peak":    round(peak, 4),
                "rise_pct":round(rise_pct, 2),
            },
            notes=f"two bottoms at ~{avg:.2f}, peak +{rise_pct:.1f}%",
        )
