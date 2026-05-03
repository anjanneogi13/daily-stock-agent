"""T36: book attribution in wisdom_hint."""
from src.wisdom_hint import _short_author, _format_lesson, wisdom_hint
import src.wisdom_hint as wh


# ───────── _short_author ─────────

def test_short_author_multi_via_slash():
    assert _short_author("Edwin Lefèvre / Jesse Livermore") == "Livermore"

def test_short_author_single():
    assert _short_author("Peter Lynch") == "Lynch"

def test_short_author_with_apostrophe():
    assert _short_author("William O'Neil") == "O'Neil"

def test_short_author_one_word():
    assert _short_author("Marks") == "Marks"

def test_short_author_empty():
    assert _short_author("") == ""

def test_short_author_only_slash():
    assert _short_author("/") == ""


# ───────── _format_lesson ─────────

def test_format_book_lesson_includes_author_prefix():
    line = _format_lesson({
        "text": "Never average down a losing position.",
        "source": "book:livermore",
        "author": "Edwin Lefèvre / Jesse Livermore",
    })
    assert "🧠" in line
    assert "Livermore:" in line
    assert "average down" in line

def test_format_organic_lesson_no_author_prefix():
    line = _format_lesson({
        "text": "Sector boosts leaked alpha.",
        "source": "backtester",
        "author": "internal",
    })
    assert "🧠" in line
    assert "internal:" not in line
    assert "backtester:" not in line
    assert "Sector boosts" in line

def test_format_book_lesson_with_no_author_falls_back():
    """If a book lesson has empty author, gracefully drop the prefix."""
    line = _format_lesson({
        "text": "Some rule.",
        "source": "book:unknown",
        "author": "",
    })
    assert "🧠" in line
    assert ":" not in line.split("_", 1)[1]  # no Author: prefix
    assert "Some rule." in line

def test_format_empty_text_returns_empty():
    assert _format_lesson({"text": "", "source": "book:x", "author": "X"}) == ""

def test_format_truncates_long_book_text():
    line = _format_lesson({
        "text": "x" * 200,
        "source": "book:livermore",
        "author": "Jesse Livermore",
    }, max_len=90)
    assert "…" in line
    # author + ":" + space accounted for; total visible <= max_len + emoji/markdown
    # check we don't blow well past max_len
    assert len(line) < 110

def test_format_truncates_long_organic_text():
    line = _format_lesson({
        "text": "y" * 200,
        "source": "manual",
        "author": "x",
    }, max_len=90)
    assert "…" in line
    assert len(line) < 100


# ───────── wisdom_hint integration (uses monkeypatched lessons_for_ticker) ─────────

def test_wisdom_hint_picks_book_lesson(monkeypatch):
    monkeypatch.setattr(wh, "_lft", lambda *a, **k: [
        {"text": "Cut losses quickly.", "source": "book:livermore",
         "author": "Jesse Livermore", "confidence": 0.95},
    ])
    out = wisdom_hint("NVDA")
    assert "Livermore:" in out
    assert "Cut losses quickly." in out

def test_wisdom_hint_picks_highest_confidence(monkeypatch):
    """Mixed lessons — the highest-confidence one wins, book or not."""
    monkeypatch.setattr(wh, "_lft", lambda *a, **k: [
        {"text": "Low-conf book rule.", "source": "book:lynch",
         "author": "Peter Lynch", "confidence": 0.6},
        {"text": "High-conf organic.", "source": "manual",
         "author": "system", "confidence": 0.95},
    ])
    out = wisdom_hint("AAPL")
    assert "High-conf organic." in out
    assert "Lynch:" not in out

def test_wisdom_hint_no_lessons_returns_empty(monkeypatch):
    monkeypatch.setattr(wh, "_lft", lambda *a, **k: [])
    assert wisdom_hint("XYZ") == ""
