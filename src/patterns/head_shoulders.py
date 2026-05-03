"""Head and Shoulders detectors (classic + inverse).

H&S (bearish reversal): three peaks where middle (head) > both shoulders,
left and right shoulders within ~3% of each other.

Inverse H&S (bullish reversal) = mirror with three troughs.
"""
from __future__ import annotations
from typing import Optional
from .base import PatternDetector, Match
from .double import _local_peaks, _local_troughs


class HeadShouldersDetector(PatternDetector):
    name = "head_shoulders"
    min_bars = 30
    direction = "bearish"

    LOOKBACK = 35
    SHOULDER_TOL_PCT = 4.0     # shoulders within 4% of each other
    HEAD_PROMINENCE_PCT = 3.0  # head ≥ 3% above shoulders
    MIN_SEPARATION = 4

    def detect(self, df) -> Optional[Match]:
        if not self._enough_bars(df):
            return None
        sub = df.tail(self.LOOKBACK)
        highs = sub["High"].tolist()
        peaks = _local_peaks(highs)
        if len(peaks) < 3:
            return None
        # Take top 3 peaks chronologically — try every consecutive triple
        # to find one matching H&S shape
        for i in range(len(peaks) - 2):
            (il, l), (ih, h), (ir, r) = peaks[i], peaks[i+1], peaks[i+2]
            if (ih - il) < self.MIN_SEPARATION: continue
            if (ir - ih) < self.MIN_SEPARATION: continue
            # Head must be highest
            if h <= l or h <= r: continue
            # Shoulders within tolerance
            avg_s = (l + r) / 2
            if abs(l - r) / avg_s * 100 > self.SHOULDER_TOL_PCT: continue
            # Head prominence
            head_prom = (h - avg_s) / avg_s * 100
            if head_prom < self.HEAD_PROMINENCE_PCT: continue
            # Right shoulder must be near the end
            if ir < len(highs) - 8: continue
            conf = min(0.95, 0.55 + 0.05 * head_prom + 0.04 * (self.SHOULDER_TOL_PCT - abs(l-r)/avg_s*100))
            return Match(
                pattern=self.name,
                confidence=round(conf, 3),
                lookback=self.LOOKBACK,
                trigger={
                    "left_shoulder":  round(l, 4),
                    "head":           round(h, 4),
                    "right_shoulder": round(r, 4),
                    "head_prominence_pct": round(head_prom, 2),
                },
                notes=f"H&S: head {h:.2f} > shoulders {l:.2f}/{r:.2f}",
            )
        return None


class InverseHeadShouldersDetector(PatternDetector):
    name = "inverse_head_shoulders"
    min_bars = 30
    direction = "bullish"

    LOOKBACK = 35
    SHOULDER_TOL_PCT = 4.0
    HEAD_PROMINENCE_PCT = 3.0
    MIN_SEPARATION = 4

    def detect(self, df) -> Optional[Match]:
        if not self._enough_bars(df):
            return None
        sub = df.tail(self.LOOKBACK)
        lows = sub["Low"].tolist()
        troughs = _local_troughs(lows)
        if len(troughs) < 3:
            return None
        for i in range(len(troughs) - 2):
            (il, l), (ih, h), (ir, r) = troughs[i], troughs[i+1], troughs[i+2]
            if (ih - il) < self.MIN_SEPARATION: continue
            if (ir - ih) < self.MIN_SEPARATION: continue
            # Head must be lowest
            if h >= l or h >= r: continue
            avg_s = (l + r) / 2
            if abs(l - r) / avg_s * 100 > self.SHOULDER_TOL_PCT: continue
            head_prom = (avg_s - h) / avg_s * 100
            if head_prom < self.HEAD_PROMINENCE_PCT: continue
            if ir < len(lows) - 8: continue
            conf = min(0.95, 0.55 + 0.05 * head_prom + 0.04 * (self.SHOULDER_TOL_PCT - abs(l-r)/avg_s*100))
            return Match(
                pattern=self.name,
                confidence=round(conf, 3),
                lookback=self.LOOKBACK,
                trigger={
                    "left_shoulder":  round(l, 4),
                    "head":           round(h, 4),
                    "right_shoulder": round(r, 4),
                    "head_prominence_pct": round(head_prom, 2),
                },
                notes=f"Inverse H&S: head {h:.2f} < shoulders {l:.2f}/{r:.2f}",
            )
        return None
