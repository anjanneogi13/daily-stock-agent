"""T43/B4: trigger-context lesson matching."""
from __future__ import annotations
import json
from pathlib import Path

import pytest

from src import wisdom_base as wb


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    p = tmp_path / "lessons.jsonl"
    monkeypatch.setattr(wb, "LESSONS", p)
    return p


# ── eval_trigger ──
def test_eval_trigger_numeric():
    assert wb.eval_trigger("drawdown_pct>3", {"drawdown_pct": 5}) is True
    assert wb.eval_trigger("drawdown_pct>3", {"drawdown_pct": 1}) is False
    assert wb.eval_trigger("days_held<=2", {"days_held": 2}) is True

def test_eval_trigger_string_eq():
    assert wb.eval_trigger("regime=chop", {"regime": "chop"}) is True
    assert wb.eval_trigger("regime=chop", {"regime": "BULL"}) is False

def test_eval_trigger_missing_key_is_false():
    assert wb.eval_trigger("drawdown_pct>3", {}) is False
    assert wb.eval_trigger("drawdown_pct>3", {"drawdown_pct": None}) is False

def test_eval_trigger_malformed_returns_false():
    assert wb.eval_trigger("garbage", {"x": 1}) is False
    assert wb.eval_trigger("", {}) is False
    assert wb.eval_trigger(None, {}) is False  # type: ignore

def test_eval_triggers_all_required():
    ctx = {"drawdown_pct": 5, "regime": "chop"}
    assert wb.eval_triggers(["drawdown_pct>3","regime=chop"], ctx) is True
    assert wb.eval_triggers(["drawdown_pct>3","regime=bull"], ctx) is False
    assert wb.eval_triggers([], ctx) is False  # empty → no fire


# ── add_lesson persists triggers ──
def test_add_lesson_persists_triggers(isolated):
    wb.add_lesson("Don't average down.", source="book:liv",
                  confidence=0.95, triggers=["drawdown_pct>3"])
    rec = json.loads(isolated.read_text().splitlines()[0])
    assert rec["triggers"] == ["drawdown_pct>3"]


# ── lessons_for_context ──
def test_lessons_for_context_fires(isolated):
    wb.add_lesson("Don't average down.", source="book:liv",
                  confidence=0.95, triggers=["drawdown_pct>3"])
    wb.add_lesson("Stay calm.", source="book:misc",
                  confidence=0.9, triggers=["regime=chop"])
    hits = wb.lessons_for_context({"drawdown_pct": 5}, min_confidence=0.85)
    assert len(hits) == 1
    assert "average down" in hits[0]["text"]

def test_lessons_for_context_skips_no_trigger(isolated):
    wb.add_lesson("Generic wisdom.", source="manual",
                  confidence=0.9, triggers=None)
    hits = wb.lessons_for_context({"drawdown_pct": 5})
    assert hits == []


# ── book_ingest passes triggers through ──
def test_book_ingest_passes_triggers(tmp_path, monkeypatch):
    seed = tmp_path / "seed.yaml"
    seed.write_text("""
meta: {version: 1}
books:
  - slug: livermore
    author: "Jesse"
    rules:
      - id: liv-01
        text: "Never average down."
        triggers: [drawdown_pct>3]
        confidence: 0.95
""")
    lp = tmp_path / "lessons.jsonl"
    monkeypatch.setattr(wb, "LESSONS", lp)
    from src import book_ingest as bi
    res = bi.load_seed(seed)
    assert res["inserted"] == 1
    rec = json.loads(lp.read_text().splitlines()[0])
    assert rec["triggers"] == ["drawdown_pct>3"]


# ── wisdom_hint.context_hint ──
def test_context_hint_surfaces_triggered_lesson(isolated):
    wb.add_lesson("Cut losses fast.", source="book:liv",
                  confidence=0.95, triggers=["drawdown_pct>3"])
    from src import wisdom_hint as wh
    out = wh.context_hint({"drawdown_pct": 5})
    assert "Cut losses" in out

def test_context_hint_empty_when_no_match(isolated):
    from src import wisdom_hint as wh
    assert wh.context_hint({}) == ""
    assert wh.context_hint({"drawdown_pct": 0}) == ""
