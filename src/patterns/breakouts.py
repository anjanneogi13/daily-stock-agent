"""20-day Donchian breakout + breakdown detectors.

Breakout: today's CLOSE strictly exceeds the highest HIGH of the prior
N bars (excluding today). Bullish.
Breakdown: today's CLOSE strictly below lowest LOW of prior N. Bearish.

Confidence scales with:
  - magnitude of breakout (% above/below the band)
  - volume confirmation (today vs 20-day avg)
"""
from __future__ import annotations
from typing import Optional

from .base import PatternDetector, Match


class BreakoutDetector(PatternDetector):
    name = "breakout_20"
    min_bars = 21       # need 20 for the band + today
    direction = "bullish"

    def detect(self, df) -> Optional[Match]:
        if not self._enough_bars(df):
            return None
        sub = df.tail(self.min_bars)
        prior = sub.iloc[:-1]
        today = sub.iloc[-1]
        band_high = float(prior["High"].max())
        close_today = float(today["Close"])
        if close_today <= band_high:
            return None
        gap_pct = (close_today - band_high) / band_high * 100
        # volume confirmation
        avg_vol = float(prior["Volume"].mean()) if "Volume" in prior else 0.0
        vol_today = float(today["Volume"]) if "Volume" in today else 0.0
        vol_ratio = (vol_today / avg_vol) if avg_vol > 0 else 1.0
        conf = min(0.95, 0.55 + 0.05 * gap_pct + 0.05 * (vol_ratio - 1))
        conf = max(0.5, conf)
        return Match(
            pattern=self.name,
            confidence=round(conf, 3),
            lookback=20,
            trigger={
                "band_high": round(band_high, 4),
                "close":     round(close_today, 4),
                "gap_pct":   round(gap_pct, 3),
                "vol_ratio": round(vol_ratio, 2),
            },
            notes="20d high broken with volume" if vol_ratio > 1.2
                  else "20d high broken (low vol)",
        )


class BreakdownDetector(PatternDetector):
    name = "breakdown_20"
    min_bars = 21
    direction = "bearish"

    def detect(self, df) -> Optional[Match]:
        if not self._enough_bars(df):
            return None
        sub = df.tail(self.min_bars)
        prior = sub.iloc[:-1]
        today = sub.iloc[-1]
        band_low = float(prior["Low"].min())
        close_today = float(today["Close"])
        if close_today >= band_low:
            return None
        gap_pct = (band_low - close_today) / band_low * 100
        avg_vol = float(prior["Volume"].mean()) if "Volume" in prior else 0.0
        vol_today = float(today["Volume"]) if "Volume" in today else 0.0
        vol_ratio = (vol_today / avg_vol) if avg_vol > 0 else 1.0
        conf = min(0.95, 0.55 + 0.05 * gap_pct + 0.05 * (vol_ratio - 1))
        conf = max(0.5, conf)
        return Match(
            pattern=self.name,
            confidence=round(conf, 3),
            lookback=20,
            trigger={
                "band_low":  round(band_low, 4),
                "close":     round(close_today, 4),
                "gap_pct":   round(gap_pct, 3),
                "vol_ratio": round(vol_ratio, 2),
            },
            notes="20d low broken with volume" if vol_ratio > 1.2
                  else "20d low broken (low vol)",
        )
