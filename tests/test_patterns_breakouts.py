"""Pillar 3 Phase 1: breakout + breakdown detectors."""
import pandas as pd
import pytest
from src.patterns.breakouts import BreakoutDetector, BreakdownDetector


def _df(closes, highs=None, lows=None, vols=None):
    n = len(closes)
    return pd.DataFrame({
        "Open":  closes,
        "High":  highs or closes,
        "Low":   lows  or closes,
        "Close": closes,
        "Volume": vols or [1000]*n,
    })


def test_breakout_fires_on_new_high():
    closes = [10] * 20 + [12]   # 21 bars, today closes above prior 20
    df = _df(closes)
    m = BreakoutDetector().detect(df)
    assert m is not None
    assert m.pattern == "breakout_20"
    assert m.trigger["close"] == 12
    assert m.trigger["band_high"] == 10
    assert m.trigger["gap_pct"] == 20.0


def test_breakout_does_not_fire_inside_range():
    closes = [10] * 20 + [10]
    df = _df(closes)
    assert BreakoutDetector().detect(df) is None


def test_breakout_volume_boost_raises_confidence():
    # Small gap (1%) so we don't saturate the 0.95 confidence ceiling
    closes = [10]*20 + [10.1]
    low_vol  = _df(closes, vols=[1000]*20 + [1000])
    high_vol = _df(closes, vols=[1000]*20 + [3000])  # 3x volume
    m_lo = BreakoutDetector().detect(low_vol)
    m_hi = BreakoutDetector().detect(high_vol)
    assert m_lo is not None and m_hi is not None
    assert m_hi.confidence > m_lo.confidence
    assert "volume" in m_hi.notes


def test_breakout_short_data_returns_none():
    df = _df([10]*5)
    assert BreakoutDetector().detect(df) is None


def test_breakdown_fires_on_new_low():
    closes = [10]*20 + [8]
    df = _df(closes)
    m = BreakdownDetector().detect(df)
    assert m is not None
    assert m.pattern == "breakdown_20"
    assert m.trigger["close"] == 8


def test_breakdown_does_not_fire_inside_range():
    df = _df([10]*21)
    assert BreakdownDetector().detect(df) is None


def test_breakdown_short_data_returns_none():
    df = _df([10]*5)
    assert BreakdownDetector().detect(df) is None
