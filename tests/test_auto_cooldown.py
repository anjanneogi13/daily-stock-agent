"""Tests for src/auto_cooldown.py — Pillar 4."""
import json
from pathlib import Path

import pytest

from src import auto_cooldown as ac
from src import wisdom_base


@pytest.fixture(autouse=True)
def _isolate(tmp_path, monkeypatch):
    """Hermetic kill-list path."""
    kill = tmp_path / "kill.json"
    monkeypatch.setattr(wisdom_base, "KILL", kill)
    yield


def _row(ticker, pick_date, outcome):
    return {"ticker": ticker, "pick_date": pick_date,
            "evaluated_on": pick_date, "outcome": outcome}


def test_no_closed_picks_returns_empty():
    r = ac.scan_and_cool(apply=False)
    assert r["candidates"] == []
    assert r["dry_run"] is True


def test_three_consecutive_losses_triggers_dry_run():
    closed = [_row("XYZ", f"2026-04-{d:02d}", "loss") for d in (10, 11, 12)]
    r = ac.scan_and_cool.__wrapped__ if hasattr(ac.scan_and_cool, "__wrapped__") else None  # noqa
    # Patch load_closed
    import src.auto_cooldown as mod
    mod.load_closed = lambda: closed
    res = ac.scan_and_cool(apply=False)
    assert ("XYZ", 3) in res["candidates"]
    assert "XYZ" in res["newly_cooled"]
    assert res["dry_run"] is True
    # No write happened
    assert wisdom_base.is_killed("XYZ") is None


def test_three_consecutive_losses_apply_writes_kill_list():
    closed = [_row("ABC", f"2026-04-{d:02d}", "loss") for d in (1, 2, 3)]
    import src.auto_cooldown as mod
    mod.load_closed = lambda: closed
    res = ac.scan_and_cool(apply=True)
    assert "ABC" in res["newly_cooled"]
    entry = wisdom_base.is_killed("ABC")
    assert entry is not None
    assert "auto-cooldown" in entry["reason"]
    assert entry["source"] == "auto_cooldown"


def test_win_breaks_streak():
    # Loss, loss, WIN, loss, loss → trailing = 2, no cool
    closed = [
        _row("DEF", "2026-04-01", "loss"),
        _row("DEF", "2026-04-02", "loss"),
        _row("DEF", "2026-04-03", "win"),
        _row("DEF", "2026-04-04", "loss"),
        _row("DEF", "2026-04-05", "loss"),
    ]
    import src.auto_cooldown as mod
    mod.load_closed = lambda: closed
    res = ac.scan_and_cool(apply=True)
    assert "DEF" not in res["newly_cooled"]
    assert wisdom_base.is_killed("DEF") is None


def test_already_cooled_marked_separately():
    closed = [_row("GHI", f"2026-04-{d:02d}", "loss") for d in (1, 2, 3)]
    import src.auto_cooldown as mod
    mod.load_closed = lambda: closed
    # Pre-add to kill list
    wisdom_base.add_to_kill_list("GHI", reason="prev", cool_off_days=10)
    res = ac.scan_and_cool(apply=True)
    assert "GHI" in res["already_cooled"]
    assert "GHI" not in res["newly_cooled"]


def test_threshold_configurable():
    closed = [_row("JKL", f"2026-04-{d:02d}", "loss") for d in (1, 2)]
    import src.auto_cooldown as mod
    mod.load_closed = lambda: closed
    res = ac.scan_and_cool(apply=True, threshold=2)
    assert "JKL" in res["newly_cooled"]


def test_format_summary_handles_empty():
    out = ac.format_summary({"candidates": [], "newly_cooled": [],
                              "already_cooled": [], "dry_run": True})
    assert "No tickers" in out


def test_format_summary_lists_cooled_with_counts():
    out = ac.format_summary({
        "candidates": [("MNO", 4)], "newly_cooled": ["MNO"],
        "already_cooled": [], "dry_run": False,
    })
    assert "MNO" in out and "4L" in out and "APPLIED" in out
