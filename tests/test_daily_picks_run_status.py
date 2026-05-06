import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from scripts.record_daily_picks_run_status import (
    append_record,
    build_record,
    status_path,
    today_picks_count,
)


def test_status_path_uses_daily_jsonl_name(tmp_path):
    assert status_path("2026-05-06", data_dir=tmp_path) == tmp_path / "daily_picks_run_status_2026-05-06.jsonl"


def test_build_record_is_monitoring_only_and_safe(monkeypatch):
    monkeypatch.setenv("GITHUB_RUN_ID", "123")
    record = build_record(
        event="guard_passed",
        result="should_run",
        reason="within premarket window",
        picks_logged=2,
        telegram_sent="success",
        now=datetime(2026, 5, 6, 8, 35, tzinfo=ZoneInfo("America/New_York")),
    )

    assert record["date"] == "2026-05-06"
    assert record["mode"] == "monitoring_only"
    assert record["paper_trading_enabled"] is False
    assert record["live_trading_enabled"] is False
    assert record["picks_logged"] == 2
    assert record["telegram_sent"] is True
    assert record["github"]["run_id"] == "123"


def test_append_record_writes_jsonl(tmp_path):
    record = build_record(
        event="watchdog_checked",
        result="missing_picks",
        reason="no rows before cutoff",
        picks_logged=0,
        workflow="watchdog",
        now=datetime(2026, 5, 6, 9, 18, tzinfo=ZoneInfo("America/New_York")),
    )

    out = append_record(record, data_dir=tmp_path)

    rows = [json.loads(line) for line in out.read_text().splitlines()]
    assert len(rows) == 1
    assert rows[0]["workflow"] == "watchdog"
    assert rows[0]["event"] == "watchdog_checked"
    assert rows[0]["result"] == "missing_picks"


def test_today_picks_count_counts_csv_rows_for_date(tmp_path):
    csv_path = tmp_path / "picks_log.csv"
    csv_path.write_text(
        "pick_date,ticker\n"
        "2026-05-06,AAPL\n"
        "2026-05-06,NVDA\n"
        "2026-05-05,TSM\n"
    )

    assert today_picks_count("2026-05-06", csv_path) == 2
    assert today_picks_count("2026-05-04", csv_path) == 0
