"""Pillar 3 Phase 1: base contract."""
import pytest
from src.patterns.base import PatternDetector, Match


def test_match_to_dict():
    m = Match(pattern="x", confidence=0.7, lookback=20)
    d = m.to_dict()
    assert d["pattern"] == "x"
    assert d["confidence"] == 0.7
    assert d["trigger"] == {}


def test_detector_abc_cannot_instantiate():
    with pytest.raises(TypeError):
        PatternDetector()


def test_enough_bars_helper():
    class _D(PatternDetector):
        name = "t"; min_bars = 5
        def detect(self, df): return None
    d = _D()
    import pandas as pd
    assert d._enough_bars(pd.DataFrame({"x":[1,2,3]})) is False
    assert d._enough_bars(pd.DataFrame({"x":[1,2,3,4,5,6]})) is True
    assert d._enough_bars(None) is False
