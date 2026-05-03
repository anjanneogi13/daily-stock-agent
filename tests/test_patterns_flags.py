"""Pillar 3 Phase 2: bull_flag + bear_flag detectors."""
import pandas as pd
import pytest
from src.patterns.flags import BullFlagDetector, BearFlagDetector


def _df(closes, highs=None, lows=None):
    n = len(closes)
    return pd.DataFrame({
        "Open":  closes,
        "High":  highs or [c * 1.01 for c in closes],
        "Low":   lows  or [c * 0.99 for c in closes],
        "Close": closes,
        "Volume": [1000] * n,
    })


def test_bull_flag_fires_on_classic_shape():
    # Pole: 100 → 115 over 7 bars (+15%)
    pole   = [100, 102, 105, 108, 111, 113, 115]
    # Flag: 7 bars consolidating in 113-115 range with slight drift
    flag   = [115, 114.5, 114, 113.5, 113, 113.2, 114]
    df = _df(pole + flag)
    m = BullFlagDetector().detect(df)
    assert m is not None
    assert m.pattern == "bull_flag"
    assert m.trigger["pole_gain_pct"] >= 8
    assert m.trigger["flag_range_pct"] <= 5


def test_bull_flag_rejects_weak_pole():
    # Only 3% pole — too weak
    pole = [100, 100.5, 101, 101.5, 102, 102.5, 103]
    flag = [103, 102.8, 102.5, 102.7, 103, 102.9, 103]
    df = _df(pole + flag)
    assert BullFlagDetector().detect(df) is None


def test_bull_flag_rejects_loose_flag():
    pole = [100, 102, 105, 108, 111, 113, 115]
    # Flag swings 110-118 = ~7% range
    flag = [115, 110, 118, 111, 117, 112, 116]
    df = _df(pole + flag)
    assert BullFlagDetector().detect(df) is None


def test_bull_flag_rejects_short_data():
    df = _df([100, 105, 110])
    assert BullFlagDetector().detect(df) is None


def test_bull_flag_rejects_flag_that_rallies():
    # Flag that keeps going up — not a flag, just continuation
    pole = [100, 102, 105, 108, 111, 113, 115]
    flag = [115, 116, 117, 118, 119, 120, 121]
    df = _df(pole + flag)
    assert BullFlagDetector().detect(df) is None


def test_bear_flag_fires_on_inverse():
    # Pole: 100 → 85 (-15%) over 7 bars
    pole = [100, 98, 95, 92, 89, 87, 85]
    # Flag: tight bounce 85-87
    flag = [85, 85.5, 86, 86.5, 86.2, 85.8, 85.5]
    df = _df(pole + flag)
    m = BearFlagDetector().detect(df)
    assert m is not None
    assert m.pattern == "bear_flag"
    assert m.trigger["pole_drop_pct"] >= 8


def test_bear_flag_rejects_weak_pole():
    pole = [100, 99.5, 99, 98.5, 98, 97.5, 97]
    flag = [97, 97.2, 97.5, 97.3, 97.1, 97, 97.2]
    df = _df(pole + flag)
    assert BearFlagDetector().detect(df) is None


def test_bear_flag_rejects_flag_that_drops_further():
    pole = [100, 98, 95, 92, 89, 87, 85]
    flag = [85, 84, 83, 82, 81, 80, 79]   # already broken down
    df = _df(pole + flag)
    assert BearFlagDetector().detect(df) is None
