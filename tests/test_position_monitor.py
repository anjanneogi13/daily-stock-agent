"""Tests for position_monitor."""
import csv
from datetime import date
from pathlib import Path
import pytest
from src import position_monitor


@pytest.fixture
def tmp_picks_log(tmp_path, monkeypatch):
    log = tmp_path / "picks_log.csv"
    monkeypatch.setattr(position_monitor, "PICKS_LOG", log)
    return log


def _write(log: Path, rows: list[dict]):
    if not rows:
        log.write_text("")
        return
    with log.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def test_no_log_returns_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(position_monitor, "PICKS_LOG", tmp_path / "missing.csv")
    assert position_monitor.scan_open_positions() == []


def test_pending_within_budget_no_alert(tmp_picks_log):
    _write(tmp_picks_log, [{
        "ticker": "AAPL", "pick_date": "2026-05-01",
        "trade_type": "swing", "entry": "100.0",
        "evaluation_status": "pending",
    }])
    alerts = position_monitor.scan_open_positions(today=date(2026, 5, 5))
    assert alerts == []  # 4d < 10d swing budget


def test_swing_overdue(tmp_picks_log):
    _write(tmp_picks_log, [{
        "ticker": "NVDA", "pick_date": "2026-04-20",
        "trade_type": "swing", "entry": "105.5",
        "evaluation_status": "pending",
    }])
    alerts = position_monitor.scan_open_positions(today=date(2026, 5, 2))
    assert len(alerts) == 1
    assert alerts[0]["severity"] == "over"
    assert alerts[0]["days_open"] == 12
    assert "NVDA" in alerts[0]["message"]


def test_day_trade_overdue_immediately(tmp_picks_log):
    _write(tmp_picks_log, [{
        "ticker": "TSLA", "pick_date": "2026-05-01",
        "trade_type": "day", "entry": "300.0",
        "evaluation_status": "pending",
    }])
    alerts = position_monitor.scan_open_positions(today=date(2026, 5, 2))
    assert len(alerts) == 1
    assert alerts[0]["severity"] == "over"


def test_near_max_hold(tmp_picks_log):
    _write(tmp_picks_log, [{
        "ticker": "AMD", "pick_date": "2026-04-23",
        "trade_type": "swing", "entry": "120.0",
        "evaluation_status": "pending",
    }])
    # swing max=10, today is 9 days after → severity=near
    alerts = position_monitor.scan_open_positions(today=date(2026, 5, 2))
    assert len(alerts) == 1
    assert alerts[0]["severity"] == "near"


def test_closed_positions_ignored(tmp_picks_log):
    _write(tmp_picks_log, [{
        "ticker": "OLD", "pick_date": "2026-01-01",
        "trade_type": "swing", "entry": "10.0",
        "evaluation_status": "tp_hit",
    }])
    assert position_monitor.scan_open_positions(today=date(2026, 5, 2)) == []


def test_unknown_trade_type_uses_default(tmp_picks_log):
    _write(tmp_picks_log, [{
        "ticker": "XYZ", "pick_date": "2026-04-15",
        "trade_type": "", "entry": "50.0",
        "evaluation_status": "pending",
    }])
    # default 14d, 17 days elapsed → over
    alerts = position_monitor.scan_open_positions(today=date(2026, 5, 2))
    assert len(alerts) == 1
    assert alerts[0]["max_hold"] == 14


def test_format_telegram_summary_empty():
    assert position_monitor.format_telegram_summary([]) == ""


def test_format_telegram_summary_mix():
    alerts = [
        {"severity": "over", "ticker": "A", "message": "msg-a", "days_open": 12, "max_hold": 10},
        {"severity": "near", "ticker": "B", "message": "msg-b", "days_open": 9, "max_hold": 10},
    ]
    out = position_monitor.format_telegram_summary(alerts)
    assert "POSITION MONITOR" in out
    assert "1 OVERDUE" in out
    assert "1 APPROACHING" in out
    assert "msg-a" in out and "msg-b" in out


def test_sort_most_overdue_first(tmp_picks_log):
    _write(tmp_picks_log, [
        {"ticker": "A", "pick_date": "2026-04-30", "trade_type": "swing",
         "entry": "1.0", "evaluation_status": "pending"},
        {"ticker": "B", "pick_date": "2026-04-15", "trade_type": "swing",
         "entry": "1.0", "evaluation_status": "pending"},
    ])
    alerts = position_monitor.scan_open_positions(today=date(2026, 5, 2))
    # B is +7 over (17-10), A is -3 (2-10) → only B is over
    assert len(alerts) == 1
    assert alerts[0]["ticker"] == "B"
