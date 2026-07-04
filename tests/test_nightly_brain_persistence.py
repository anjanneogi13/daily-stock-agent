import json
from datetime import datetime as real_datetime, timezone

from experimental import agent_memoir as am
from src import learning_journal as lj
from src import nightly_conductor as nc


def test_run_nightly_writes_brain_state_meta(monkeypatch, tmp_path):
    meta_path = tmp_path / "brain_state_meta.json"
    monkeypatch.setattr(nc, "BRAIN_STATE_META_PATH", meta_path)
    monkeypatch.setattr(lj, "JOURNAL", tmp_path / "learning_journal.jsonl")
    monkeypatch.setenv("GITHUB_RUN_ID", "run-123")

    monkeypatch.setattr(nc, "_step_pattern_scan", lambda *a, **k: {"tickers_scanned": 0})
    monkeypatch.setattr(nc, "_step_pattern_stats", lambda: {"patterns_with_stats": 0})
    monkeypatch.setattr(nc, "_step_pattern_auto_enable_disable", lambda: {"disabled": [], "reactivated": []})
    monkeypatch.setattr(nc, "_step_calibration_propose", lambda: {"skipped": "only 0 closed picks (need 10)"})
    monkeypatch.setattr(nc, "_step_weight_apply", lambda: {"applied": 0})
    monkeypatch.setattr(nc, "_step_auto_promote", lambda: {"promoted": 0})
    monkeypatch.setattr(nc, "_step_lesson_gc", lambda: {"gc_removed": 0})
    monkeypatch.setattr(nc, "_step_agent_memoir", lambda: {"lifetime_trades": 0, "win_rate": 0.0})

    summary = nc.run_nightly(scan_tickers=[], deep_mode=False)

    assert summary["steps_failed"] == 0
    assert summary["steps_ok"] == 8
    assert meta_path.exists()

    meta = json.loads(meta_path.read_text())
    assert meta["run_id"] == "run-123"
    assert "last_run_utc" in meta
    assert meta["steps_ok"] == 8
    assert meta["steps_failed"] == 0
    assert meta["steps"]["calibration_propose"]["status"] == "skipped"
    assert meta["steps"]["pattern_scan"]["status"] == "ok"


def test_agent_memoir_step_rewrites_json_with_new_last_updated(monkeypatch, tmp_path):
    memoir_path = tmp_path / "agent_memoir.json"
    picks_path = tmp_path / "picks_log.csv"
    journal_path = tmp_path / "learning_journal.jsonl"

    picks_path.write_text(
        "ticker,pick_date,evaluation_status,r_multiple,actual_return_pct,regime,days_to_earnings\n"
        "POWI,2026-04-28,tp_hit,2.0,16.76,bull,12\n"
        "LRCX,2026-04-28,sl_hit,-1.0,-6.85,bull,10\n"
    )
    journal_path.write_text(
        json.dumps({
            "ts": "2026-07-03T00:00:00+00:00",
            "kind": "nightly_brain_run",
        }) + "\n"
    )

    monkeypatch.setattr(am, "MEMOIR_PATH", memoir_path)
    monkeypatch.setattr(am, "PICKS_LOG", picks_path)
    monkeypatch.setattr(am, "LEARNING_JOURNAL", journal_path)

    first_ts = real_datetime(2026, 7, 4, 0, 0, 1, tzinfo=timezone.utc)
    second_ts = real_datetime(2026, 7, 4, 0, 0, 2, tzinfo=timezone.utc)

    class FakeDateTime:
        _values = iter([first_ts, first_ts, second_ts, second_ts])

        @classmethod
        def now(cls, tz=None):
            return next(cls._values)

        @classmethod
        def fromisoformat(cls, value):
            return real_datetime.fromisoformat(value)

    monkeypatch.setattr(am, "datetime", FakeDateTime)

    first_result = nc._step_agent_memoir()
    first_memoir = json.loads(memoir_path.read_text())

    second_result = nc._step_agent_memoir()
    second_memoir = json.loads(memoir_path.read_text())

    assert first_result["lifetime_trades"] == 2
    assert second_result["has_biggest_win"] is True
    assert second_memoir["last_updated"] != first_memoir["last_updated"]
    assert second_memoir["last_updated"] == second_ts.isoformat()
    assert second_memoir["lifetime_stats"]["closed_trades"] == 2
