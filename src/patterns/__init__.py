"""Pillar 3 — Pattern Recognition Engine.

Each detector lives in its own module and inherits PatternDetector.
Phase 1: HHHL, breakout, breakdown.
Phase 2: bull_flag, bear_flag, triangles, cup-and-handle.
Phase 3: double_top/bottom, head-and-shoulders, wedges.
"""
from .base import PatternDetector, Match
from .hhhl import HHHLDetector, LHLLDetector
from .breakouts import BreakoutDetector, BreakdownDetector

ALL_DETECTORS = [
    HHHLDetector(),
    LHLLDetector(),
    BreakoutDetector(),
    BreakdownDetector(),
]

__all__ = ["PatternDetector", "Match", "ALL_DETECTORS",
           "HHHLDetector", "LHLLDetector",
           "BreakoutDetector", "BreakdownDetector"]
