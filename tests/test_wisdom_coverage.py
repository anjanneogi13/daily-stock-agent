"""T33: wisdom coverage stat for daily footer."""
import pytest
from src import wisdom_coverage


@pytest.fixture
def stub_hints(monkeypatch):
    """Allow per-test control over wisdom_hint / pattern_hint output."""
    state = {"wh": {}, "ph": {}}

    def fake_wh(ticker=None, sector=None, **k):
        return state["wh"].get(ticker, "")

    def fake_ph(row, **k):
        return state["ph"].get(row.get("ticker"), "") if row else ""

    monkeypatch.setattr(wisdom_coverage, "wisdom_hint", fake_wh)
    monkeypatch.setattr(wisdom_coverage, "pattern_hint", fake_ph)
    return state


# ═════════════════════════════════════════════════════════════
class TestCoverage:
    def test_empty_returns_zeros(self, stub_hints):
        c = wisdom_coverage.coverage([])
        assert c == {"total": 0, "tagged": 0, "lessons": 0,
                     "patterns": 0, "pct": 0.0}

    def test_none_safe(self, stub_hints):
        assert wisdom_coverage.coverage(None)["total"] == 0

    def test_no_hints(self, stub_hints):
        rows = [{"ticker": "AAPL"}, {"ticker": "MSFT"}]
        c = wisdom_coverage.coverage(rows)
        assert c["total"] == 2
        assert c["tagged"] == 0
        assert c["pct"] == 0.0

    def test_lesson_only(self, stub_hints):
        stub_hints["wh"] = {"AAPL": "   🧠 _avoid earnings_"}
        rows = [{"ticker": "AAPL"}, {"ticker": "MSFT"}]
        c = wisdom_coverage.coverage(rows)
        assert c["lessons"] == 1
        assert c["patterns"] == 0
        assert c["tagged"] == 1
        assert c["pct"] == 50.0

    def test_pattern_only(self, stub_hints):
        stub_hints["ph"] = {"NVDA": "   ⚠ _drag_"}
        rows = [{"ticker": "NVDA"}, {"ticker": "AMD"}]
        c = wisdom_coverage.coverage(rows)
        assert c["lessons"] == 0
        assert c["patterns"] == 1
        assert c["tagged"] == 1

    def test_both_counted_once_in_tagged(self, stub_hints):
        stub_hints["wh"] = {"NVDA": "   🧠 _x_"}
        stub_hints["ph"] = {"NVDA": "   ⚠ _y_"}
        rows = [{"ticker": "NVDA"}]
        c = wisdom_coverage.coverage(rows)
        assert c["lessons"] == 1
        assert c["patterns"] == 1
        assert c["tagged"] == 1   # not double-counted
        assert c["pct"] == 100.0

    def test_full_coverage_pct(self, stub_hints):
        stub_hints["wh"] = {"A": "x", "B": "y", "C": "z"}
        rows = [{"ticker": t} for t in "ABC"]
        c = wisdom_coverage.coverage(rows)
        assert c["pct"] == 100.0

    def test_partial_pct(self, stub_hints):
        stub_hints["wh"] = {"A": "x"}
        rows = [{"ticker": t} for t in "ABCD"]
        c = wisdom_coverage.coverage(rows)
        assert c["pct"] == 25.0

    def test_hint_exception_safe(self, stub_hints, monkeypatch):
        def boom(*a, **k): raise RuntimeError("kaboom")
        monkeypatch.setattr(wisdom_coverage, "wisdom_hint", boom)
        # Should not crash
        c = wisdom_coverage.coverage([{"ticker": "X"}])
        assert c["total"] == 1
        assert c["lessons"] == 0


class TestFormatFooter:
    def test_empty_returns_blank(self):
        assert wisdom_coverage.format_footer({"total": 0}) == ""
        assert wisdom_coverage.format_footer({}) == ""
        assert wisdom_coverage.format_footer(None) == ""

    def test_full_format(self):
        s = {"total": 10, "tagged": 6, "lessons": 4,
             "patterns": 2, "pct": 60.0}
        out = wisdom_coverage.format_footer(s)
        assert "6/10" in out
        assert "60%" in out
        assert "4 lessons" in out
        assert "2 patterns" in out
        assert out.startswith("🧠")

    def test_singular_grammar(self):
        s = {"total": 5, "tagged": 1, "lessons": 1,
             "patterns": 1, "pct": 20.0}
        out = wisdom_coverage.format_footer(s)
        assert "1 lesson " in out  # singular, trailing space (no 's')
        assert "1 pattern" in out
        assert "patterns" not in out

    def test_zero_grammar_plural(self):
        # 0 → "0 lessons" (plural)
        s = {"total": 5, "tagged": 0, "lessons": 0,
             "patterns": 0, "pct": 0.0}
        out = wisdom_coverage.format_footer(s)
        assert "0 lessons" in out
        assert "0 patterns" in out
