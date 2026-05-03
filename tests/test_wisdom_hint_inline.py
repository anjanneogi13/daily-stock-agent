"""T24: per-pick wisdom hint surfaces in Telegram pick formatting."""
import importlib
import pytest
from src import wisdom_base


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(wisdom_base, "LESSONS",  tmp_path / "lessons.jsonl")
    monkeypatch.setattr(wisdom_base, "PATTERNS", tmp_path / "patterns.jsonl")
    monkeypatch.setattr(wisdom_base, "KILL",     tmp_path / "kill.json")
    return tmp_path


# ═════════════════════════════════════════════════════════════
# wisdom_base.lessons_for_ticker
# ═════════════════════════════════════════════════════════════
class TestLessonsForTicker:
    def test_match_via_tag(self, isolated):
        wisdom_base.add_lesson(text="anything", source="t",
                                confidence=0.85,
                                tags=["cooldown", "auto", "AAPL"], author="t")
        assert len(wisdom_base.lessons_for_ticker("AAPL")) == 1

    def test_match_case_insensitive(self, isolated):
        wisdom_base.add_lesson(text="x", source="t", confidence=0.8,
                                tags=["aapl"], author="t")
        assert len(wisdom_base.lessons_for_ticker("AAPL")) == 1
        assert len(wisdom_base.lessons_for_ticker("aapl")) == 1

    def test_match_via_text_body(self, isolated):
        wisdom_base.add_lesson(text="TSLA gaps fade hard",
                                source="t", confidence=0.85,
                                tags=[], author="t")
        assert len(wisdom_base.lessons_for_ticker("TSLA")) == 1

    def test_below_confidence_threshold_excluded(self, isolated):
        wisdom_base.add_lesson(text="x", source="t", confidence=0.5,
                                tags=["NVDA"], author="t")
        assert wisdom_base.lessons_for_ticker("NVDA", min_confidence=0.7) == []

    def test_empty_ticker_returns_empty(self, isolated):
        wisdom_base.add_lesson(text="x", source="t", confidence=0.9,
                                tags=["AAPL"], author="t")
        assert wisdom_base.lessons_for_ticker("") == []

    def test_no_lessons_returns_empty(self, isolated):
        assert wisdom_base.lessons_for_ticker("AAPL") == []


# ═════════════════════════════════════════════════════════════
# src.wisdom_hint.wisdom_hint
# ═════════════════════════════════════════════════════════════
class TestWisdomHintFormatter:
    def _reload(self):
        import src.wisdom_hint as wh
        importlib.reload(wh)
        return wh

    def test_returns_empty_when_no_lesson(self, isolated):
        wh = self._reload()
        assert wh.wisdom_hint("CLEAN") == ""

    def test_returns_formatted_line_when_lesson_exists(self, isolated):
        wisdom_base.add_lesson(text="AAPL cooled 14d after 3 losses",
                                source="auto_cooldown", confidence=0.85,
                                tags=["cooldown", "AAPL"], author="auto")
        wh = self._reload()
        out = wh.wisdom_hint("AAPL")
        assert "🧠" in out
        assert "AAPL cooled" in out

    def test_truncates_very_long_lesson(self, isolated):
        wisdom_base.add_lesson(text="A" * 200, source="t", confidence=0.9,
                                tags=["LONG"], author="t")
        wh = self._reload()
        out = wh.wisdom_hint("LONG")
        assert "…" in out and len(out) < 120

    def test_low_confidence_lesson_not_shown(self, isolated):
        wisdom_base.add_lesson(text="weak signal", source="t",
                                confidence=0.6, tags=["WEAK"], author="t")
        wh = self._reload()
        assert wh.wisdom_hint("WEAK") == ""

    def test_helper_never_crashes(self, isolated):
        wh = self._reload()
        for bad in [None, "", "X", "NEVER_HEARD_OF_THIS_TICKER"]:
            r = wh.wisdom_hint(bad)
            assert isinstance(r, str)

    def test_picks_highest_confidence_when_multiple(self, isolated):
        wisdom_base.add_lesson(text="low",  source="t", confidence=0.71,
                                tags=["MULTI"], author="t")
        wisdom_base.add_lesson(text="high", source="t", confidence=0.95,
                                tags=["MULTI"], author="t")
        wh = self._reload()
        out = wh.wisdom_hint("MULTI")
        assert "high" in out and "low" not in out
