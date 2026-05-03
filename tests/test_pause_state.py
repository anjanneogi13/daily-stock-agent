"""Tests for src/pause_state.py — Pillar 4 enforce-mode."""
import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from src import pause_state as ps


@pytest.fixture(autouse=True)
def _isolate(tmp_path, monkeypatch):
    """Redirect config + state paths to tmp so tests are hermetic."""
    cfg = tmp_path / "config" / "auto_pause.json"
    cfg.parent.mkdir(parents=True)
    cfg.write_text(json.dumps({"enforced": False, "pause_threshold": 8, "pause_days": 3}))

    state = tmp_path / "data" / "pause_state.json"
    state.parent.mkdir(parents=True)

    monkeypatch.setattr(ps, "CONFIG_PATH", cfg)
    monkeypatch.setattr(ps, "STATE_PATH", state)
    yield


def test_default_not_paused():
    r = ps.is_paused()
    assert r["paused"] is False
    assert r["days_remaining"] == 0


def test_observe_mode_never_triggers():
    # Config has enforced=false
    triggered = ps.maybe_auto_pause({"score": 10, "reasons": ["crisis"]})
    assert triggered is None
    assert ps.is_paused()["paused"] is False


def test_enforce_mode_triggers_above_threshold(monkeypatch):
    # Flip enforce ON
    cfg = ps.load_config()
    cfg["enforced"] = True
    ps.CONFIG_PATH.write_text(json.dumps(cfg))

    triggered = ps.maybe_auto_pause({"score": 9, "reasons": ["RED 30d WR"]})
    assert triggered is not None
    assert ps.is_paused()["paused"] is True


def test_enforce_mode_below_threshold_no_trigger():
    cfg = ps.load_config()
    cfg["enforced"] = True
    ps.CONFIG_PATH.write_text(json.dumps(cfg))

    triggered = ps.maybe_auto_pause({"score": 7, "reasons": ["AMBER"]})
    assert triggered is None
    assert ps.is_paused()["paused"] is False


def test_pause_expires_auto_clears():
    yesterday = datetime.now() - timedelta(days=2)
    ps.STATE_PATH.write_text(json.dumps({
        "active": True,
        "since": (yesterday - timedelta(days=3)).strftime("%Y-%m-%d"),
        "until": yesterday.strftime("%Y-%m-%d"),
        "score": 9, "reason": ["test"], "manual": False,
    }))
    r = ps.is_paused()
    assert r["paused"] is False
    # Should have auto-cleared the file
    assert not ps.STATE_PATH.exists()


def test_clear_state_idempotent():
    ps.clear_state()  # No file
    ps.trigger_pause(score=9, reasons=["x"], days=2)
    ps.clear_state()
    assert not ps.STATE_PATH.exists()


def test_trigger_pause_sets_until_correctly():
    today = datetime(2026, 5, 3)
    state = ps.trigger_pause(score=8, reasons=["a", "b"], days=3, today=today)
    assert state["until"] == "2026-05-06"
    assert state["since"] == "2026-05-03"
    assert state["active"] is True


def test_does_not_extend_existing_pause():
    cfg = ps.load_config()
    cfg["enforced"] = True
    ps.CONFIG_PATH.write_text(json.dumps(cfg))

    first = ps.trigger_pause(score=9, reasons=["first"], days=3)
    # Try to auto-trigger again with higher score
    second = ps.maybe_auto_pause({"score": 10, "reasons": ["worse"]})
    assert second is None  # Refuses to extend
    cur = ps.is_paused()
    assert cur["until"] == first["until"]


def test_format_pause_alert_contains_key_info():
    ps.trigger_pause(score=9, reasons=["RED 30d WR", "RED drawdown"], days=3)
    state = ps.is_paused()
    alert = ps.format_pause_alert(state)
    assert "PAUSED" in alert
    assert "9" in alert
    assert "RED" in alert
    assert "scripts/unpause.py" in alert


def test_config_missing_returns_safe_defaults(tmp_path, monkeypatch):
    monkeypatch.setattr(ps, "CONFIG_PATH", tmp_path / "missing.json")
    cfg = ps.load_config()
    assert cfg["enforced"] is False
    assert cfg["pause_threshold"] == 8
