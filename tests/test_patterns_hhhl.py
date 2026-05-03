"""Pillar 3 Phase 1: HHHL + LHLL detectors."""
import pandas as pd
import pytest
from src.patterns.hhhl import HHHLDetector, LHLLDetector, _pivot_highs, _pivot_lows


def _df(highs, lows, closes=None, vols=None):
    n = len(highs)
    return pd.DataFrame({
        "Open":  closes or highs,
        "High":  highs,
        "Low":   lows,
        "Close": closes or highs,
        "Volume": vols or [1000] * n,
    })


def test_pivot_highs_finds_local_max():
    h = [1,2,3,2,1,4,5,6,5,4]
    pivots = _pivot_highs(h, k=2)
    # peaks at index 2 (value 3) and 7 (value 6)
    assert (2, 3) in pivots
    assert (7, 6) in pivots


def test_hhhl_fires_on_clean_uptrend():
    # Synthetic: stair-step up with clear pivots
    highs = [10,11,12,11,10,12,13,14,13,12,14,15,16,15,14,16,17,18,17,16]
    lows  = [9, 10,11,10,9, 11,12,13,12,11,13,14,15,14,13,15,16,17,16,15]
    df = _df(highs, lows)
    m = HHHLDetector().detect(df)
    assert m is not None
    assert m.pattern == "hhhl"
    assert m.confidence > 0.5
    assert m.trigger["last_high"] > m.trigger["prev_high"]
    assert m.trigger["last_low"]  > m.trigger["prev_low"]


def test_hhhl_does_not_fire_on_downtrend():
    highs = [20,19,18,19,20,18,17,16,17,18,16,15,14,15,16,14,13,12,13,14]
    lows  = [19,18,17,18,19,17,16,15,16,17,15,14,13,14,15,13,12,11,12,13]
    df = _df(highs, lows)
    assert HHHLDetector().detect(df) is None


def test_hhhl_short_data_returns_none():
    df = _df([1,2,3], [0,1,2])
    assert HHHLDetector().detect(df) is None


def test_lhll_fires_on_downtrend():
    highs = [20,19,18,19,20,18,17,16,17,18,16,15,14,15,16,14,13,12,13,14]
    lows  = [19,18,17,18,19,17,16,15,16,17,15,14,13,14,15,13,12,11,12,13]
    df = _df(highs, lows)
    m = LHLLDetector().detect(df)
    assert m is not None
    assert m.pattern == "lhll"
    assert m.trigger["last_high"] < m.trigger["prev_high"]


def test_lhll_does_not_fire_on_uptrend():
    highs = [10,11,12,11,10,12,13,14,13,12,14,15,16,15,14,16,17,18,17,16]
    lows  = [9, 10,11,10,9, 11,12,13,12,11,13,14,15,14,13,15,16,17,16,15]
    df = _df(highs, lows)
    assert LHLLDetector().detect(df) is None


def test_hhhl_handles_flat_market():
    highs = [10] * 20
    lows  = [9] * 20
    df = _df(highs, lows)
    assert HHHLDetector().detect(df) is None
