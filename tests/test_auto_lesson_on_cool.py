"""T22: auto_cooldown should also write a lesson when it cools a ticker."""
from datetime import datetime, timedelta
import pytest

from src import wisdom_base, auto_cooldown


def _losing_closed(ticker: str, n: int):
    """n consecutive CLOSED losing trades for ticker (newest last)."""
    base = datetime(2026, 4, 1)
    return [{
        "pick_date":         (base + timedelta(days=i)).date().isoformat(),
        "ticker":            ticker,
        "trade_type":        "swing",
        "evaluation_status": "CLOSED",
        "evaluated_on":      (base + timedelta(days=i + 5)).date().isoformat(),
        "r_multiple":        -1.0,
        "actual_return_pct": -5.0,
        "outcome":           "loss",
    } for i in range(n)]


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(wisdom_base, "LESSONS",  tmp_path / "lessons.jsonl")
    monkeypatch.setattr(wisdom_base, "PATTERNS", tmp_path / "patterns.jsonl")
    monkeypatch.setattr(wisdom_base, "KILL",     tmp_path / "kill.json")
    yield


def _patch_closed(monkeypatch, closed):
    monkeypatch.setattr(auto_cooldown, "load_closed", lambda: closed)


def test_apply_writes_lesson(isolated, monkeypatch):
    _patch_closed(monkeypatch, _losing_closed("BURN", 3))
    res = auto_cooldown.scan_and_cool(apply=True, threshold=3, cool_off_days=14)
    assert "BURN" in res["newly_cooled"]

    lessons = wisdom_base.load_active_lessons(min_confidence=0.0)
    burn = [L for L in lessons if "BURN" in L.get("text", "")]
    assert len(burn) == 1
    L = burn[0]
    assert L["source"] == "auto_cooldown"
    assert "cooldown" in L["tags"]
    assert "BURN" in L["tags"]
    assert 0.5 < L["confidence"] < 0.9


def test_dry_run_writes_no_lesson(isolated, monkeypatch):
    _patch_closed(monkeypatch, _losing_closed("DRY", 3))
    auto_cooldown.scan_and_cool(apply=False, threshold=3, cool_off_days=14)
    lessons = wisdom_base.load_active_lessons(min_confidence=0.0)
    assert not any("DRY" in L.get("text", "") for L in lessons), \
        "dry-run must not mutate wisdom"


def test_already_cooled_writes_no_duplicate_lesson(isolated, monkeypatch):
    _patch_closed(monkeypatch, _losing_closed("REPEAT", 3))
    auto_cooldown.scan_and_cool(apply=True, threshold=3, cool_off_days=14)
    auto_cooldown.scan_and_cool(apply=True, threshold=3, cool_off_days=14)
    lessons = wisdom_base.load_active_lessons(min_confidence=0.0)
    repeat = [L for L in lessons if "REPEAT" in L.get("text", "")]
    assert len(repeat) == 1, f"expected 1 lesson, got {len(repeat)}"
