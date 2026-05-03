"""Pillar 3 — Pattern Recognition Engine.

Phase 1: HHHL, LHLL, breakout_20, breakdown_20.
Phase 2: bull_flag, bear_flag, ascending/descending/symmetric triangles, cup_and_handle.
Phase 3: head_and_shoulders (+ inverse), double_top/bottom, wedges (+ Layer 6).
"""
from .base import PatternDetector, Match
from .hhhl import HHHLDetector, LHLLDetector
from .breakouts import BreakoutDetector, BreakdownDetector
from .flags import BullFlagDetector, BearFlagDetector
from .triangles import (
    AscendingTriangleDetector,
    DescendingTriangleDetector,
    SymmetricTriangleDetector,
)
from .cup_handle import CupAndHandleDetector

ALL_DETECTORS = [
    HHHLDetector(),
    LHLLDetector(),
    BreakoutDetector(),
    BreakdownDetector(),
    BullFlagDetector(),
    BearFlagDetector(),
    AscendingTriangleDetector(),
    DescendingTriangleDetector(),
    SymmetricTriangleDetector(),
    CupAndHandleDetector(),
]

__all__ = ["PatternDetector", "Match", "ALL_DETECTORS",
           "HHHLDetector", "LHLLDetector",
           "BreakoutDetector", "BreakdownDetector",
           "BullFlagDetector", "BearFlagDetector",
           "AscendingTriangleDetector", "DescendingTriangleDetector",
           "SymmetricTriangleDetector", "CupAndHandleDetector"]
