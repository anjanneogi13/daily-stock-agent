"""T45: weekly footer renders Pillar 5 self-awareness block."""
from __future__ import annotations
import json
from datetime import datetime, timedelta

from src import signal_journal as sj


def test_weekly_renders_pillar5_block(tmp_path, monkeypatch):
    p = tmp_path / "j.jsonl"
    monkeypatch.setattr(sj, "JOURNAL", p)
    today = datetime.now().date().isoformat()
    with p.open("w") as f:
        for i in range(5):
            f.write(json.dumps({
                "ticker":f"X{i}","pick_date":today,"evaluated_on":today,
                "outcome":"win" if i%2 else "loss",
                "r_multiple": 2.0 if i%2 else -1.0,
                "signals":{"trade_type":"swing"}}) + "\n")
    from src.weekly_review import build_report, format_telegram
    text = format_telegram(build_report())
    assert "Self-awareness (Pillar 5)" in text
    assert "30d edge" in text


def test_weekly_safe_when_pillar5_breaks(monkeypatch):
    import src.self_awareness as sa
    def boom(*a, **k): raise RuntimeError("simulated")
    monkeypatch.setattr(sa, "rolling_window", boom)
    from src.weekly_review import build_report, format_telegram
    text = format_telegram(build_report())
    assert "Recommended action" in text
