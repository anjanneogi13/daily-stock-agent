import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from scripts.record_daily_picks_run_status import (
    _daily_picks_diagnostics,
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


def test_build_record_can_store_late_ideas_count():
    record = build_record(
        event="late_ideas_generated",
        result="success",
        late_ideas_count=3,
        picks_logged=0,
        now=datetime(2026, 5, 6, 11, 30, tzinfo=ZoneInfo("America/New_York")),
    )

    assert record["late_ideas_count"] == 3
    assert record["official_premarket_pick"] is False


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


def test_daily_picks_diagnostics_reads_no_pick_report(tmp_path):
    (tmp_path / "daily_picks_no_pick_report_2026-05-06.json").write_text(json.dumps({
        "primary_no_pick_cause": "NO_PICK_ALL_FINALISTS_HARD_BLOCKED",
        "secondary_causes": ["YFINANCE_PROVIDER_DEGRADED"],
        "pipeline": {
            "pre_hard_block_pick_count": 2,
            "hard_blocked_count": 2,
            "final_pick_count": 0,
        },
        "diagnostics": {
            "pre_hard_block_candidates": [{"ticker": "AAA"}, {"ticker": "BBB"}],
            "hard_blocked_candidates": [{"ticker": "AAA"}, {"ticker": "BBB"}],
        },
    }))

    diag = _daily_picks_diagnostics("2026-05-06", data_dir=tmp_path)

    assert diag["no_pick_report_path"].endswith("daily_picks_no_pick_report_2026-05-06.json")
    assert diag["candidate_rejections_path"] == ""
    assert diag["primary_no_pick_cause"] == "NO_PICK_ALL_FINALISTS_HARD_BLOCKED"
    assert diag["secondary_causes"] == ["YFINANCE_PROVIDER_DEGRADED"]
    assert diag["pipeline"]["final_pick_count"] == 0
    assert diag["diagnostics_available"] is True
    assert diag["pre_hard_block_candidate_count"] == 2
    assert diag["hard_blocked_candidate_count"] == 2


def test_build_record_can_include_daily_picks_diagnostics(tmp_path):
    (tmp_path / "daily_picks_no_pick_report_2026-05-06.json").write_text(json.dumps({
        "primary_no_pick_cause": "NO_PICK_ALL_FINALISTS_HARD_BLOCKED",
        "pipeline": {
            "pre_hard_block_pick_count": 2,
            "hard_blocked_count": 2,
            "final_pick_count": 0,
        },
    }))

    record = build_record(
        event="agent_completed",
        result="failed",
        reason="main.py failed",
        picks_logged=0,
        include_diagnostics=True,
        data_dir=tmp_path,
        now=datetime(2026, 5, 6, 8, 35, tzinfo=ZoneInfo("America/New_York")),
    )

    diag = record["daily_picks_diagnostics"]
    assert diag["primary_no_pick_cause"] == "NO_PICK_ALL_FINALISTS_HARD_BLOCKED"
    assert diag["diagnostics_available"] is False
    assert diag["pre_hard_block_candidate_count"] == 2
    assert diag["hard_blocked_candidate_count"] == 2
    assert record["paper_trading_enabled"] is False
    assert record["live_trading_enabled"] is False
