"""Pillar 3 Phase 2: ascending / descending / symmetric triangle detectors."""
import pandas as pd
import pytest
from src.patterns.triangles import (
    AscendingTriangleDetector,
    DescendingTriangleDetector,
    SymmetricTriangleDetector,
    _linreg,
)


def _df(highs, lows):
    n = len(highs)
    closes = [(h + l) / 2 for h, l in zip(highs, lows)]
    return pd.DataFrame({
        "Open":  closes,
        "High":  highs,
        "Low":   lows,
        "Close": closes,
        "Volume": [1000] * n,
    })


def test_linreg_basic():
    # y = 2x + 1
    m, b = _linreg([1, 3, 5, 7, 9])
    assert m == pytest.approx(2.0)
    assert b == pytest.approx(1.0)


def test_linreg_flat():
    m, b = _linreg([5, 5, 5, 5, 5])
    assert m == pytest.approx(0.0)
    assert b == pytest.approx(5.0)


def test_ascending_triangle_fires():
    # Highs flat at ~100, lows rising from 90 → 99
    n = 20
    highs = [100 + (i % 3) * 0.05 for i in range(n)]
    lows  = [90 + i * 0.5 for i in range(n)]
    df = _df(highs, lows)
    m = AscendingTriangleDetector().detect(df)
    assert m is not None
    assert m.pattern == "ascending_triangle"
    assert m.trigger["support_slope_pct"] > 0.2


def test_ascending_triangle_rejects_flat_market():
    df = _df([100]*20, [99]*20)
    assert AscendingTriangleDetector().detect(df) is None


def test_descending_triangle_fires():
    # Highs falling from 110 → 101, lows flat at ~90
    n = 20
    highs = [110 - i * 0.5 for i in range(n)]
    lows  = [90 + (i % 3) * 0.05 for i in range(n)]
    df = _df(highs, lows)
    m = DescendingTriangleDetector().detect(df)
    assert m is not None
    assert m.pattern == "descending_triangle"
    assert m.trigger["resistance_slope_pct"] < -0.2


def test_descending_triangle_rejects_uptrend():
    n = 20
    highs = [100 + i for i in range(n)]
    lows  = [90 + i for i in range(n)]
    df = _df(highs, lows)
    assert DescendingTriangleDetector().detect(df) is None


def test_symmetric_triangle_fires():
    # Highs falling, lows rising — converging
    n = 20
    highs = [110 - i * 0.4 for i in range(n)]
    lows  = [90 + i * 0.4 for i in range(n)]
    df = _df(highs, lows)
    m = SymmetricTriangleDetector().detect(df)
    assert m is not None
    assert m.pattern == "symmetric_triangle"


def test_symmetric_triangle_rejects_one_sided():
    # Only highs falling, lows flat → that's descending, not symmetric
    n = 20
    highs = [110 - i * 0.4 for i in range(n)]
    lows  = [90] * n
    df = _df(highs, lows)
    assert SymmetricTriangleDetector().detect(df) is None


def test_triangles_handle_short_data():
    df = _df([100]*5, [99]*5)
    assert AscendingTriangleDetector().detect(df) is None
    assert DescendingTriangleDetector().detect(df) is None
    assert SymmetricTriangleDetector().detect(df) is None
