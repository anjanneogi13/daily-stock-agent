"""Pillar 3 Phase 3: rising + falling wedges."""
import pandas as pd
import pytest
from src.patterns.wedges import FallingWedgeDetector, RisingWedgeDetector


def _df(highs, lows):
    n = len(highs)
    closes = [(h+l)/2 for h,l in zip(highs,lows)]
    return pd.DataFrame({
        "Open":closes,"High":highs,"Low":lows,"Close":closes,
        "Volume":[1000]*n})


def test_falling_wedge_fires():
    # Highs falling fast, lows falling slow → converging up
    n = 20
    highs = [120 - i*0.8 for i in range(n)]
    lows  = [80  - i*0.2 for i in range(n)]
    df = _df(highs, lows)
    m = FallingWedgeDetector().detect(df)
    assert m is not None
    assert m.pattern == "falling_wedge"


def test_falling_wedge_rejects_uptrend():
    n = 20
    highs = [100 + i for i in range(n)]
    lows  = [90 + i for i in range(n)]
    df = _df(highs, lows)
    assert FallingWedgeDetector().detect(df) is None


def test_rising_wedge_fires():
    n = 20
    highs = [80 + i*0.2 for i in range(n)]
    lows  = [40 + i*0.8 for i in range(n)]
    df = _df(highs, lows)
    m = RisingWedgeDetector().detect(df)
    assert m is not None
    assert m.pattern == "rising_wedge"


def test_rising_wedge_rejects_downtrend():
    n = 20
    highs = [100 - i for i in range(n)]
    lows  = [90 - i for i in range(n)]
    df = _df(highs, lows)
    assert RisingWedgeDetector().detect(df) is None


def test_wedges_handle_short_data():
    df = _df([100]*5, [99]*5)
    assert FallingWedgeDetector().detect(df) is None
    assert RisingWedgeDetector().detect(df) is None
