"""Pillar 3 Phase 3: double_top + double_bottom."""
import pandas as pd
import pytest
from src.patterns.double import DoubleTopDetector, DoubleBottomDetector


def _df(highs, lows, closes=None):
    n = len(highs)
    return pd.DataFrame({
        "Open": closes or highs, "High": highs, "Low": lows,
        "Close": closes or highs, "Volume": [1000]*n,
    })


def test_double_top_fires_classic():
    # 30 bars. Need TWO strictly-unique local peaks (k=3 window).
    # Peak1 at idx 6 = 100, peak2 at idx 25 = 101 (both unique in their ±3 window).
    # Trough between at idx 13 = 88. i2 must be in last 10 bars (idx ≥ 20).
    highs = [85,87,90,93,96,99,100,99,96,93,
             90,89,88,89,88,89,90,93,95,97,
             98,99,97,99,101,99,97,95,93,91]
    lows  = [h - 2 for h in highs]
    df = _df(highs, lows)
    m = DoubleTopDetector().detect(df)
    assert m is not None, "expected double_top to fire"
    assert m.pattern == "double_top"
    assert m.trigger["drop_pct"] >= 5
    # peaks within tol
    assert abs(m.trigger["peak1"] - m.trigger["peak2"]) / m.trigger["peak1"] * 100 <= 2.0


def test_double_top_rejects_uneven_peaks():
    # Peak1 ~100 at idx 6, peak2 ~110 at idx 25 — too uneven (>2%)
    highs = [85,90,95,100,95,90,85,90,95,98,
             95,90,85,90,95,98,100,98,95,90,
             85,90,95,100,103,106,108,110,108,105]
    lows = [h - 2 for h in highs]
    df = _df(highs, lows)
    assert DoubleTopDetector().detect(df) is None


def test_double_top_rejects_short_data():
    df = _df([100]*10, [99]*10)
    assert DoubleTopDetector().detect(df) is None


def test_double_bottom_fires_classic():
    # Bottom1 idx 4 = 5, bottom2 idx 24 = 5 (both unique strict mins in ±3 window).
    # Peak between at idx 9 = 18. i2 = 24 in last 10 bars (idx ≥ 20).
    lows  = [15,13,10,7,5,8,12,14,16,18,
             16,15,14,16,17,16,14,12,10,8,
             7,6,7,6,5,8,12,14,16,18]
    highs = [l + 2 for l in lows]
    df = _df(highs, lows)
    m = DoubleBottomDetector().detect(df)
    assert m is not None, "expected double_bottom to fire"
    assert m.pattern == "double_bottom"
    assert m.trigger["rise_pct"] >= 5
    assert abs(m.trigger["bottom1"] - m.trigger["bottom2"]) / m.trigger["bottom1"] * 100 <= 2.0


def test_double_bottom_rejects_uneven():
    # Bottoms 5 and 10 — way too uneven
    lows  = [15,12,8,5,5,5,8,12,15,12,
             8,7,6,5,7,12,15,17,15,12,
             10,11,10,11,10,11,10,11,10,11]
    highs = [l + 2 for l in lows]
    df = _df(highs, lows)
    assert DoubleBottomDetector().detect(df) is None
