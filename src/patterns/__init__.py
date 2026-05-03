"""Pillar 3 — Pattern Recognition Engine.

ALL 15 DETECTORS LIVE (T49 — Phase 3 complete).
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
from .double import DoubleTopDetector, DoubleBottomDetector
from .head_shoulders import HeadShouldersDetector, InverseHeadShouldersDetector
from .wedges import FallingWedgeDetector, RisingWedgeDetector

ALL_DETECTORS = [
    HHHLDetector(), LHLLDetector(),
    BreakoutDetector(), BreakdownDetector(),
    BullFlagDetector(), BearFlagDetector(),
    AscendingTriangleDetector(), DescendingTriangleDetector(),
    SymmetricTriangleDetector(),
    CupAndHandleDetector(),
    DoubleTopDetector(), DoubleBottomDetector(),
    HeadShouldersDetector(), InverseHeadShouldersDetector(),
    FallingWedgeDetector(), RisingWedgeDetector(),
]

__all__ = ["PatternDetector", "Match", "ALL_DETECTORS"] + [
    "HHHLDetector", "LHLLDetector",
    "BreakoutDetector", "BreakdownDetector",
    "BullFlagDetector", "BearFlagDetector",
    "AscendingTriangleDetector", "DescendingTriangleDetector",
    "SymmetricTriangleDetector",
    "CupAndHandleDetector",
    "DoubleTopDetector", "DoubleBottomDetector",
    "HeadShouldersDetector", "InverseHeadShouldersDetector",
    "FallingWedgeDetector", "RisingWedgeDetector",
]
