"""Test that Pillar 1 status block renders into weekly Telegram."""
from __future__ import annotations
import json
from pathlib import Path
import pytest

from src import signal_journal as sj


def test_weekly_renders_pillar1_block_when_journal_present(tmp_path, monkeypatch):
    j = tmp_path / "j.jsonl"
    j.write_text(
        json.dumps({"ticker":"A","pick_date":"2026-04-28",
                    "outcome":"win","r_multiple":2.0,
                    "signals":{"trade_type":"swing"}}) + "\n" +
        json.dumps({"ticker":"B","pick_date":"2026-04-28",
                    "outcome":"loss","r_multiple":-1.0,
                    "signals":{"trade_type":"swing"}}) + "\n"
    )
    monkeypatch.setattr(sj, "JOURNAL", j)

    from src.weekly_review import build_report, format_telegram
    text = format_telegram(build_report())
    assert "Probability engine (Pillar 1)" in text
    assert "Hypothesis journal" in text


def test_weekly_safe_when_pillar1_modules_break(monkeypatch):
    """If auto_pause raises, weekly still ships."""
    import src.auto_pause as ap
    def boom(*a, **k): raise RuntimeError("simulated")
    monkeypatch.setattr(ap, "compute_score", boom)

    from src.weekly_review import build_report, format_telegram
    text = format_telegram(build_report())
    assert "Weekly Self-Assessment" in text
    assert "Recommended action" in text
