"""Bull flag / Bear flag detectors.

Bull flag (bullish continuation):
  - POLE: sharp rally — last 5-10 bars before flag rose >= 8%
  - FLAG: tight consolidation — next 5-10 bars stay within 3-5% range,
          with a slight downward drift (or flat)
  - Today must be at/near the top of the flag (preparing to break out)

Bear flag = mirror.

Confidence scales with: pole steepness, flag tightness, position in flag.
"""
from __future__ import annotations
from typing import Optional
from .base import PatternDetector, Match


def _pct_change(a: float, b: float) -> float:
    if b == 0: return 0.0
    return (a - b) / b * 100


class BullFlagDetector(PatternDetector):
    name = "bull_flag"
    min_bars = 14
    direction = "bullish"

    POLE_BARS = 7
    FLAG_BARS = 7
    MIN_POLE_PCT = 8.0   # pole must rise ≥ 8%
    MAX_FLAG_PCT = 5.0   # flag range ≤ 5%

    def detect(self, df) -> Optional[Match]:
        if not self._enough_bars(df):
            return None
        sub = df.tail(self.POLE_BARS + self.FLAG_BARS)
        pole = sub.iloc[:self.POLE_BARS]
        flag = sub.iloc[self.POLE_BARS:]

        pole_start = float(pole["Close"].iloc[0])
        pole_end   = float(pole["Close"].iloc[-1])
        pole_gain  = _pct_change(pole_end, pole_start)
        if pole_gain < self.MIN_POLE_PCT:
            return None

        flag_high = float(flag["High"].max())
        flag_low  = float(flag["Low"].min())
        flag_range_pct = _pct_change(flag_high, flag_low)
        if flag_range_pct > self.MAX_FLAG_PCT:
            return None

        # Flag should drift down or stay flat (not rally further)
        flag_start = float(flag["Close"].iloc[0])
        flag_end   = float(flag["Close"].iloc[-1])
        flag_drift = _pct_change(flag_end, flag_start)
        if flag_drift > 2.0:   # flag rallied — not a flag, it's a continuation already
            return None

        # Position: today should be in upper half of flag
        today_close = float(flag["Close"].iloc[-1])
        flag_mid = (flag_high + flag_low) / 2
        position_top = today_close >= flag_mid

        # Confidence: stronger pole, tighter flag, near top
        conf = 0.5 + 0.02 * pole_gain + 0.03 * (self.MAX_FLAG_PCT - flag_range_pct)
        if position_top: conf += 0.05
        conf = max(0.5, min(0.95, conf))

        return Match(
            pattern=self.name,
            confidence=round(conf, 3),
            lookback=self.POLE_BARS + self.FLAG_BARS,
            trigger={
                "pole_gain_pct":  round(pole_gain, 2),
                "flag_range_pct": round(flag_range_pct, 2),
                "flag_drift_pct": round(flag_drift, 2),
                "near_top":       position_top,
            },
            notes=f"pole +{pole_gain:.1f}% / flag {flag_range_pct:.1f}% range",
        )


class BearFlagDetector(PatternDetector):
    name = "bear_flag"
    min_bars = 14
    direction = "bearish"

    POLE_BARS = 7
    FLAG_BARS = 7
    MIN_POLE_PCT = 8.0
    MAX_FLAG_PCT = 5.0

    def detect(self, df) -> Optional[Match]:
        if not self._enough_bars(df):
            return None
        sub = df.tail(self.POLE_BARS + self.FLAG_BARS)
        pole = sub.iloc[:self.POLE_BARS]
        flag = sub.iloc[self.POLE_BARS:]

        pole_start = float(pole["Close"].iloc[0])
        pole_end   = float(pole["Close"].iloc[-1])
        pole_drop  = _pct_change(pole_start, pole_end)   # positive if dropped
        if pole_drop < self.MIN_POLE_PCT:
            return None

        flag_high = float(flag["High"].max())
        flag_low  = float(flag["Low"].min())
        flag_range_pct = _pct_change(flag_high, flag_low)
        if flag_range_pct > self.MAX_FLAG_PCT:
            return None

        flag_start = float(flag["Close"].iloc[0])
        flag_end   = float(flag["Close"].iloc[-1])
        flag_drift = _pct_change(flag_start, flag_end)   # positive if dropped further
        if flag_drift > 2.0:    # flag dropped further — already broken down
            return None
        # Bear flag: small upward drift in flag is OK (and expected)

        today_close = float(flag["Close"].iloc[-1])
        flag_mid = (flag_high + flag_low) / 2
        position_bottom = today_close <= flag_mid

        conf = 0.5 + 0.02 * pole_drop + 0.03 * (self.MAX_FLAG_PCT - flag_range_pct)
        if position_bottom: conf += 0.05
        conf = max(0.5, min(0.95, conf))

        return Match(
            pattern=self.name,
            confidence=round(conf, 3),
            lookback=self.POLE_BARS + self.FLAG_BARS,
            trigger={
                "pole_drop_pct":  round(pole_drop, 2),
                "flag_range_pct": round(flag_range_pct, 2),
                "flag_drift_pct": round(flag_drift, 2),
                "near_bottom":    position_bottom,
            },
            notes=f"pole -{pole_drop:.1f}% / flag {flag_range_pct:.1f}% range",
        )
