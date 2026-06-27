"""T44: weekly footer renders Pillar 4 brain-learning summary."""
from __future__ import annotations
import json

from src import learning_journal as lj


def test_weekly_renders_pillar4_block_when_journal_present(tmp_path, monkeypatch):
    p = tmp_path / "lj.jsonl"
    monkeypatch.setattr(lj, "JOURNAL", p)
    lj.log("lesson_added", text="x")
    lj.log("pattern_promoted", text="y")

    from src.weekly_review import build_report, format_telegram
    text = format_telegram(build_report())
    assert "Config/journal activity this week" in text
    assert "lessons" in text or "patterns" in text


def test_weekly_safe_when_pillar4_modules_break(monkeypatch):
    import src.weight_applier as wa
    def boom(*a, **k): raise RuntimeError("simulated")
    monkeypatch.setattr(wa, "history_summary", boom)
    from src.weekly_review import build_report, format_telegram
    text = format_telegram(build_report())
    assert "Recommended action" in text
