"""T26: pattern-engine inline hints (drag/edge per pick row)."""
import importlib
import pytest
from src import wisdom_base


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(wisdom_base, "LESSONS",  tmp_path / "lessons.jsonl")
    monkeypatch.setattr(wisdom_base, "PATTERNS", tmp_path / "patterns.jsonl")
    monkeypatch.setattr(wisdom_base, "KILL",     tmp_path / "kill.json")
    return tmp_path


def _wh():
    import src.wisdom_hint as m
    importlib.reload(m)
    return m


class TestPatternHint:
    def test_empty_row_returns_empty(self, isolated):
        wh = _wh()
        assert wh.pattern_hint({}) == ""
        assert wh.pattern_hint(None) == ""

    def test_no_patterns_returns_empty(self, isolated):
        wh = _wh()
        assert wh.pattern_hint({"trade_type": "day"}) == ""

    def test_drag_pattern_surfaces(self, isolated):
        wisdom_base.add_pattern(signal="trade_type", bucket="day",
                                 effect="drag", win_rate=0.31,
                                 sample_n=42, p_value=0.02)
        wh = _wh()
        out = wh.pattern_hint({"trade_type": "day"})
        assert "⚠" in out
        assert "trade_type=day" in out
        assert "31%" in out
        assert "42 trades" in out

    def test_edge_pattern_surfaces(self, isolated):
        wisdom_base.add_pattern(signal="regime", bucket="RISK_ON",
                                 effect="edge", win_rate=0.62,
                                 sample_n=80, p_value=0.01)
        wh = _wh()
        out = wh.pattern_hint({"regime": "RISK_ON"})
        assert "✨" in out
        assert "62%" in out

    def test_drag_prioritized_over_edge(self, isolated):
        wisdom_base.add_pattern(signal="regime", bucket="MIXED",
                                 effect="edge", win_rate=0.55,
                                 sample_n=30, p_value=0.04)
        wisdom_base.add_pattern(signal="regime", bucket="MIXED",
                                 effect="drag", win_rate=0.40,
                                 sample_n=25, p_value=0.03)
        wh = _wh()
        out = wh.pattern_hint({"regime": "MIXED"})
        assert "⚠" in out and "✨" not in out

    def test_low_sample_excluded(self, isolated):
        wisdom_base.add_pattern(signal="trade_type", bucket="day",
                                 effect="drag", win_rate=0.20,
                                 sample_n=5, p_value=0.01)
        wh = _wh()
        assert wh.pattern_hint({"trade_type": "day"}) == ""

    def test_high_pvalue_excluded(self, isolated):
        wisdom_base.add_pattern(signal="trade_type", bucket="day",
                                 effect="drag", win_rate=0.40,
                                 sample_n=50, p_value=0.30)
        wh = _wh()
        assert wh.pattern_hint({"trade_type": "day"}) == ""

    def test_unknown_signal_ignored(self, isolated):
        wisdom_base.add_pattern(signal="moon_phase", bucket="full",
                                 effect="drag", win_rate=0.30,
                                 sample_n=50, p_value=0.01)
        wh = _wh()
        assert wh.pattern_hint({"moon_phase": "full"}) == ""

    def test_case_insensitive_bucket_match(self, isolated):
        wisdom_base.add_pattern(signal="regime", bucket="risk_on",
                                 effect="edge", win_rate=0.60,
                                 sample_n=30, p_value=0.02)
        wh = _wh()
        out = wh.pattern_hint({"regime": "RISK_ON"})
        assert "✨" in out

    def test_largest_sample_wins_among_drags(self, isolated):
        wisdom_base.add_pattern(signal="sector", bucket="tech",
                                 effect="drag", win_rate=0.35,
                                 sample_n=25, p_value=0.04)
        wisdom_base.add_pattern(signal="sector", bucket="tech",
                                 effect="drag", win_rate=0.30,
                                 sample_n=120, p_value=0.001)
        wh = _wh()
        out = wh.pattern_hint({"sector": "tech"})
        assert "120 trades" in out  # the bigger-sample one wins

    def test_never_crashes_on_garbage(self, isolated):
        wisdom_base.add_pattern(signal="trade_type", bucket="day",
                                 effect="drag", win_rate=0.30,
                                 sample_n=30, p_value=0.01)
        wh = _wh()
        for bad in [{}, None, {"trade_type": None}, {"x": 1}]:
            r = wh.pattern_hint(bad)
            assert isinstance(r, str)
