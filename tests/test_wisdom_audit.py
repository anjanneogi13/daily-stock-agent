"""Tests for scripts/wisdom_audit.py — text + JSON output, empty + populated."""
import importlib.util
import json
from datetime import datetime
from pathlib import Path

import pytest

from src import wisdom_base


SPEC = importlib.util.spec_from_file_location(
    "wisdom_audit", Path("scripts/wisdom_audit.py"))


@pytest.fixture
def audit(tmp_path, monkeypatch):
    monkeypatch.setattr(wisdom_base, "LESSONS",  tmp_path / "lessons.jsonl")
    monkeypatch.setattr(wisdom_base, "PATTERNS", tmp_path / "patterns.jsonl")
    monkeypatch.setattr(wisdom_base, "KILL",     tmp_path / "kill.json")
    mod = importlib.util.module_from_spec(SPEC)
    SPEC.loader.exec_module(mod)
    return mod


def test_empty_text_shows_none(audit):
    txt = audit.render_text()
    assert "WISDOM AUDIT" in txt
    assert "(none)" in txt
    assert "Lessons (active): 0" in txt


def test_empty_json_valid(audit):
    obj = json.loads(audit.render_json())
    assert obj["lessons"] == []
    assert obj["patterns"] == []
    assert obj["kill_list"] == {}
    assert "generated_at" in obj


def test_populated_text(audit):
    wisdom_base.add_lesson(
        text="AVOID swing in bear regime", source="manual",
        confidence=0.85, tags=["regime"], author="test")
    wisdom_base.add_pattern(
        signal="regime", bucket="bear", effect="drag",
        win_rate=0.2, sample_n=20, p_value=0.03)
    wisdom_base.add_to_kill_list(
        "BURN", reason="3 losses", cool_off_days=14, source="auto_cooldown")

    txt = audit.render_text()
    assert "AVOID swing in bear regime" in txt
    assert "DRAG" in txt
    assert "regime=bear" in txt
    assert "BURN" in txt
    assert "auto_cooldown" in txt
    # confidence emoji rendered
    assert "🟢" in txt


def test_populated_json_round_trip(audit):
    wisdom_base.add_to_kill_list(
        "ABC", reason="x", cool_off_days=10, source="manual")
    obj = json.loads(audit.render_json())
    assert "ABC" in obj["kill_list"]
    assert obj["kill_list"]["ABC"]["source"] == "manual"


def test_lessons_sorted_by_confidence_desc(audit):
    wisdom_base.add_lesson(text="low", source="x", confidence=0.5,
                            tags=[], author="t")
    wisdom_base.add_lesson(text="high", source="x", confidence=0.9,
                            tags=[], author="t")
    txt = audit.render_text()
    high_pos = txt.index("high")
    low_pos  = txt.index("low")
    assert high_pos < low_pos
