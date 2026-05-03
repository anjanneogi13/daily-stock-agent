"""T50: Nightly conductor — orchestrator + step isolation tests."""
import json
import pytest
from pathlib import Path

from src import nightly_conductor as nc


def test_step_wraps_success():
    summary = {"steps": {}}
    nc._step("ok_step", lambda: {"value": 42}, summary)
    assert summary["steps"]["ok_step"]["ok"] is True
    assert summary["steps"]["ok_step"]["result"] == {"value": 42}


def test_step_isolates_exception():
    summary = {"steps": {}}
    def boom(): raise ValueError("synthetic")
    nc._step("bad_step", boom, summary)
    assert summary["steps"]["bad_step"]["ok"] is False
    assert "ValueError" in summary["steps"]["bad_step"]["error"]


def test_step_handles_none_return():
    summary = {"steps": {}}
    nc._step("noop", lambda: None, summary)
    assert summary["steps"]["noop"]["ok"] is True
    assert summary["steps"]["noop"]["result"] == {}


def test_format_summary_text_basic():
    summary = {
        "ts": "2026-05-03T23:00:00",
        "ok_count": 2, "fail_count": 1,
        "steps": {
            "a": {"ok": True,  "result": {"x": 1}},
            "b": {"ok": True,  "result": {}},
            "c": {"ok": False, "error": "BoomError: oops"},
        },
    }
    text = nc.format_summary_text(summary)
    assert "Nightly Brain Run" in text
    assert "✅ 2 ok" in text
    assert "❌ 1 failed" in text
    assert "BoomError" in text


def test_load_universe_for_scan_empty(monkeypatch, tmp_path):
    monkeypatch.setattr(nc, "WATCHLIST_PATH", tmp_path / "wl.json")
    monkeypatch.setattr(nc, "PICKS_LOG", tmp_path / "p.csv")
    assert nc._load_universe_for_scan() == []


def test_load_universe_for_scan_picks_only(monkeypatch, tmp_path):
    p = tmp_path / "p.csv"
    p.write_text("ticker,pick_date\nAAPL,2026-05-01\nNVDA,2026-05-02\n")
    monkeypatch.setattr(nc, "WATCHLIST_PATH", tmp_path / "missing.json")
    monkeypatch.setattr(nc, "PICKS_LOG", p)
    res = nc._load_universe_for_scan()
    assert "AAPL" in res
    assert "NVDA" in res


def test_run_nightly_executes_all_steps_with_isolation(monkeypatch, tmp_path):
    """Even if every real step fails, conductor must produce a summary."""
    # Force each step to raise — verify isolation
    monkeypatch.setattr(nc, "_step_pattern_scan",        lambda *a,**k: (_ for _ in ()).throw(RuntimeError("x")))
    monkeypatch.setattr(nc, "_step_pattern_stats",       lambda: (_ for _ in ()).throw(RuntimeError("x")))
    monkeypatch.setattr(nc, "_step_pattern_auto_enable_disable", lambda: (_ for _ in ()).throw(RuntimeError("x")))
    monkeypatch.setattr(nc, "_step_calibration_propose", lambda: (_ for _ in ()).throw(RuntimeError("x")))
    monkeypatch.setattr(nc, "_step_weight_apply",        lambda: (_ for _ in ()).throw(RuntimeError("x")))
    monkeypatch.setattr(nc, "_step_auto_promote",        lambda: (_ for _ in ()).throw(RuntimeError("x")))
    monkeypatch.setattr(nc, "_step_lesson_gc",           lambda: (_ for _ in ()).throw(RuntimeError("x")))
    summary = nc.run_nightly()
    assert summary["fail_count"] == 7
    assert summary["ok_count"] == 0
    # All 7 steps appear in summary
    assert len(summary["steps"]) == 7
