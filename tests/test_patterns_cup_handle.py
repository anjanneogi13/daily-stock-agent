"""Pillar 3 Phase 2: cup-and-handle detector."""
import pandas as pd
import pytest
from src.patterns.cup_handle import CupAndHandleDetector


def _df(closes):
    n = len(closes)
    return pd.DataFrame({
        "Open":  closes,
        "High":  [c * 1.005 for c in closes],
        "Low":   [c * 0.995 for c in closes],
        "Close": closes,
        "Volume": [1000] * n,
    })


def test_cup_and_handle_fires_on_classic_shape():
    # 30 bars: left rim → cup down → right rim → handle
    # Left third (0-9): rises to ~100
    left   = [95, 96, 97, 98, 99, 100, 100, 99, 98, 97]
    # Middle third (10-19): U-shape down to ~85, back up to 99
    middle = [95, 92, 89, 87, 85, 87, 90, 93, 96, 99]
    # Right third pre-handle (20-23): peak ~100 again
    right  = [100, 99.5, 100, 99]
    # Handle (24-29): tight 6-bar consolidation 96-98
    handle = [98, 97.5, 97, 96.5, 97, 97.5]
    df = _df(left + middle + right + handle)
    assert len(df) == 30
    m = CupAndHandleDetector().detect(df)
    assert m is not None, "expected cup-and-handle to fire"
    assert m.pattern == "cup_and_handle"
    assert 10 <= m.trigger["cup_depth_pct"] <= 35
    assert m.trigger["rim_diff_pct"] <= 3
    assert m.trigger["handle_range_pct"] <= 5


def test_cup_and_handle_rejects_no_cup():
    # Just a flat trend — no U-shape
    df = _df([100] * 30)
    assert CupAndHandleDetector().detect(df) is None


def test_cup_and_handle_rejects_uneven_rims():
    # Left rim 100, right rim 110 — too uneven
    left   = [95, 96, 97, 98, 99, 100, 100, 99, 98, 97]
    middle = [95, 92, 89, 87, 85, 87, 90, 93, 96, 100]
    right  = [108, 109, 110, 109]   # rim too high
    handle = [108, 107.5, 107, 106.5, 107, 107.5]
    df = _df(left + middle + right + handle)
    assert CupAndHandleDetector().detect(df) is None


def test_cup_and_handle_rejects_loose_handle():
    left   = [95, 96, 97, 98, 99, 100, 100, 99, 98, 97]
    middle = [95, 92, 89, 87, 85, 87, 90, 93, 96, 99]
    right  = [100, 99.5, 100, 99]
    # Handle swings 90-100 — way too loose
    handle = [98, 90, 100, 92, 99, 91]
    df = _df(left + middle + right + handle)
    assert CupAndHandleDetector().detect(df) is None


def test_cup_and_handle_rejects_short_data():
    df = _df([100] * 10)
    assert CupAndHandleDetector().detect(df) is None
