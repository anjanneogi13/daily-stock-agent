"""Base contract for all Pillar 3 pattern detectors.

A detector is a deterministic function:
    detect(ohlcv: pd.DataFrame) -> Optional[Match]

OHLCV input must have columns: Open, High, Low, Close, Volume (yfinance
shape). Most-recent bar is at the END of the dataframe.

A Match describes WHAT was found, with enough metadata for the
probability engine + outcome evaluator to use it later.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict, field
from typing import Dict, Optional


@dataclass
class Match:
    pattern:    str               # canonical name, e.g. "bull_flag"
    confidence: float             # 0.0 – 1.0 (detector-specific)
    lookback:   int               # bars analysed
    trigger:    Dict = field(default_factory=dict)  # numeric details
    notes:      str = ""

    def to_dict(self) -> Dict:
        return asdict(self)


class PatternDetector(ABC):
    """All detectors must implement detect() returning Match or None."""

    name: str = "abstract"
    min_bars: int = 20
    direction: str = "neutral"   # "bullish" | "bearish" | "neutral"

    @abstractmethod
    def detect(self, df) -> Optional[Match]:
        ...

    def _enough_bars(self, df) -> bool:
        try:
            return len(df) >= self.min_bars
        except Exception:
            return False
