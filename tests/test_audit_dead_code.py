"""F2: dead-code audit must catch all 3 import shapes + stay clean."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.audit_dead_code import _imports_from, find_dead


def test_catches_from_src_dot_X():
    assert "foo" in _imports_from("from src.foo import bar")


def test_catches_import_src_dot_X():
    assert "foo" in _imports_from("import src.foo")


def test_catches_from_src_import_X():
    """Shape that v1 audit MISSED."""
    assert "foo" in _imports_from("from src import foo")
    deps = _imports_from("from src import foo, bar, baz")
    assert {"foo", "bar", "baz"}.issubset(deps)


def test_catches_aliased_from_src_import_X():
    deps = _imports_from("from src import pattern_stats as ps")
    assert "pattern_stats" in deps


def test_catches_relative_dot_imports():
    assert "foo" in _imports_from("from .foo import bar")


def test_pattern_stats_no_longer_dead():
    """Regression: v1 audit incorrectly flagged pattern_stats."""
    r = find_dead()
    assert "pattern_stats" not in r["dead"]


def test_learning_journal_no_longer_dead():
    """Regression: v1 audit incorrectly flagged learning_journal."""
    r = find_dead()
    assert "learning_journal" not in r["dead"]


def test_tracker_no_longer_dead():
    """v1 audit flagged tracker but it IS reachable via app.py + scripts."""
    r = find_dead()
    assert "tracker" not in r["dead"]


def test_dead_list_locked():
    """Locks the current dead-list. Forces conscious update if it grows.

    Bumping this set requires either:
      (a) wiring a module up (preferred — see E4 smell faculty),
      (b) deleting the module (cruft), or
      (c) explicit acknowledgment that this is a CLI-only tool.
    """
    r = find_dead()
    KNOWN_DEAD = {
        "book_ingest",   # CLI: python -m src.book_ingest load-seed
        "exit_metrics",  # F2 wired into wisdom; will move live next run
        "yearly_report", # CLI: python -m src.yearly_report
    }
    unexpected = set(r["dead"]) - KNOWN_DEAD
    assert not unexpected, (
        f"NEW dead modules detected. Wire them up, delete them, "
        f"or update KNOWN_DEAD with justification: {unexpected}"
    )
