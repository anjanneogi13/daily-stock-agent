"""T44 / Pillar 4: learning_journal."""
from __future__ import annotations
import json
from pathlib import Path

import pytest

from src import learning_journal as lj


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    p = tmp_path / "lj.jsonl"
    monkeypatch.setattr(lj, "JOURNAL", p)
    return p


def test_log_appends_record(isolated):
    rec = lj.log("lesson_added", text="hello", source="manual")
    lines = isolated.read_text().strip().splitlines()
    assert len(lines) == 1
    out = json.loads(lines[0])
    assert out["kind"] == "lesson_added"
    assert out["text"] == "hello"
    assert "ts" in out


def test_read_returns_all(isolated):
    lj.log("lesson_added", text="a")
    lj.log("pattern_promoted", text="b")
    out = lj.read()
    assert len(out) == 2


def test_read_filters_by_days(isolated, monkeypatch):
    # write an old record manually
    isolated.write_text(json.dumps({
        "ts": "2020-01-01T00:00:00+00:00",
        "kind": "lesson_added", "text": "old"
    }) + "\n")
    lj.log("lesson_added", text="new")
    recent = lj.read(days=7)
    assert len(recent) == 1
    assert recent[0]["text"] == "new"


def test_summary_counts_by_kind(isolated):
    lj.log("lesson_added")
    lj.log("lesson_added")
    lj.log("pattern_promoted")
    s = lj.summary(days=7)
    assert s["total"] == 3
    assert s["by_kind"]["lesson_added"] == 2
    assert s["by_kind"]["pattern_promoted"] == 1


def test_empty_when_no_journal(isolated):
    # Don't write anything
    assert lj.read() == []
    assert lj.summary()["total"] == 0
