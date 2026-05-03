"""T27: sector-wide wisdom hints surface on every ticker in that sector."""
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


# ═════════════════════════════════════════════════════════════
# wisdom_base.lessons_for_ticker(sector=...)
# ═════════════════════════════════════════════════════════════
class TestLessonsForSector:
    def test_sector_match(self, isolated):
        wisdom_base.add_lesson(text="All semis cooled 7d",
                                source="auto", confidence=0.85,
                                tags=["sector", "semis"], author="auto")
        out = wisdom_base.lessons_for_ticker("NVDA", sector="semis")
        assert len(out) == 1
        assert "semis" in out[0]["text"].lower()

    def test_sector_match_case_insensitive(self, isolated):
        wisdom_base.add_lesson(text="x", source="t", confidence=0.85,
                                tags=["TECH"], author="t")
        assert len(wisdom_base.lessons_for_ticker("AAPL", sector="tech")) == 1
        assert len(wisdom_base.lessons_for_ticker("AAPL", sector="Tech")) == 1

    def test_sector_without_ticker(self, isolated):
        wisdom_base.add_lesson(text="all energy weak",
                                source="t", confidence=0.85,
                                tags=["energy"], author="t")
        out = wisdom_base.lessons_for_ticker("", sector="energy")
        assert len(out) == 1

    def test_no_sector_no_match_for_sector_lesson(self, isolated):
        # Sector-tagged lesson should NOT surface on a non-matching ticker
        # when sector is not passed
        wisdom_base.add_lesson(text="all semis cooled",
                                source="t", confidence=0.85,
                                tags=["semis"], author="t")
        assert wisdom_base.lessons_for_ticker("NVDA") == []

    def test_ticker_lesson_still_works_with_sector(self, isolated):
        # Mix: ticker-specific lesson + sector — both should match
        wisdom_base.add_lesson(text="NVDA cooled",
                                source="t", confidence=0.85,
                                tags=["NVDA"], author="t")
        wisdom_base.add_lesson(text="all semis weak",
                                source="t", confidence=0.85,
                                tags=["semis"], author="t")
        out = wisdom_base.lessons_for_ticker("NVDA", sector="semis")
        assert len(out) == 2

    def test_empty_inputs_return_empty(self, isolated):
        assert wisdom_base.lessons_for_ticker("", sector="") == []
        assert wisdom_base.lessons_for_ticker(None, sector=None) == []


# ═════════════════════════════════════════════════════════════
# wisdom_hint(ticker, sector=...)
# ═════════════════════════════════════════════════════════════
class TestSectorWisdomHint:
    def test_sector_hint_surfaces_on_member(self, isolated):
        wisdom_base.add_lesson(text="All semis cooled 7d (3/4 losses)",
                                source="auto", confidence=0.9,
                                tags=["semis"], author="auto")
        wh = _wh()
        out = wh.wisdom_hint("AMD", sector="semis")
        assert "🧠" in out
        assert "semis cooled" in out

    def test_no_hint_when_sector_not_passed(self, isolated):
        wisdom_base.add_lesson(text="all semis cooled",
                                source="t", confidence=0.9,
                                tags=["semis"], author="t")
        wh = _wh()
        # Without sector, NVDA gets no hint (it isn't tagged literally)
        assert wh.wisdom_hint("NVDA") == ""

    def test_sector_hint_works_across_multiple_tickers(self, isolated):
        wisdom_base.add_lesson(text="energy weak this week",
                                source="t", confidence=0.85,
                                tags=["energy"], author="t")
        wh = _wh()
        for tk in ["XOM", "CVX", "OXY"]:
            assert "energy weak" in wh.wisdom_hint(tk, sector="energy")

    def test_ticker_hint_takes_precedence(self, isolated):
        # A ticker-specific high-confidence lesson should beat sector
        wisdom_base.add_lesson(text="sector general note",
                                source="t", confidence=0.75,
                                tags=["semis"], author="t")
        wisdom_base.add_lesson(text="NVDA earnings tomorrow",
                                source="t", confidence=0.95,
                                tags=["NVDA"], author="t")
        wh = _wh()
        out = wh.wisdom_hint("NVDA", sector="semis")
        # Highest confidence wins (NVDA-specific 0.95 > sector 0.75)
        assert "NVDA earnings" in out

    def test_no_crash_on_none_sector(self, isolated):
        wh = _wh()
        assert wh.wisdom_hint("AAPL", sector=None) == ""
        assert wh.wisdom_hint("", sector=None) == ""
