"""Tests for strategy_breakdown."""
import csv
from pathlib import Path
import pytest
from src import strategy_breakdown as sb


@pytest.fixture
def tmp_log(tmp_path, monkeypatch):
    log = tmp_path / "picks_log.csv"
    monkeypatch.setattr(sb, "PICKS_LOG", log)
    return log


def _write(log: Path, rows: list[dict]):
    if not rows:
        log.write_text("")
        return
    with log.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def _pick(**overrides):
    base = {
        "ticker": "AAPL", "trade_type": "swing", "tag": "QUALITY",
        "regime": "bull", "evaluation_status": "tp_hit",
        "actual_return_pct": "2.0", "r_multiple": "1.5",
        "alpha_pct": "1.2",
    }
    base.update(overrides)
    return base


def test_no_log_returns_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(sb, "PICKS_LOG", tmp_path / "missing.csv")
    assert sb.breakdown_by("trade_type") == []


def test_pending_rows_excluded(tmp_log):
    _write(tmp_log, [_pick(evaluation_status="pending", actual_return_pct="")])
    assert sb.breakdown_by("trade_type") == []


def test_basic_grouping(tmp_log):
    _write(tmp_log, [
        _pick(trade_type="swing", evaluation_status="tp_hit", r_multiple="2.0", actual_return_pct="5.0"),
        _pick(trade_type="swing", evaluation_status="sl_hit", r_multiple="-1.0", actual_return_pct="-3.0"),
        _pick(trade_type="day", evaluation_status="sl_hit", r_multiple="-1.0", actual_return_pct="-1.5"),
    ])
    rows = sb.breakdown_by("trade_type")
    by_group = {r["group"]: r for r in rows}
    assert by_group["swing"]["n"] == 2
    assert by_group["swing"]["wins"] == 1
    assert by_group["swing"]["win_rate"] == 0.5
    assert by_group["swing"]["total_r"] == 1.0
    assert by_group["day"]["n"] == 1
    assert by_group["day"]["win_rate"] == 0.0


def test_tag_breakdown_isolates_losers(tmp_log):
    """Reproduces the SEMI/AI -7R observation."""
    _write(tmp_log, [
        _pick(tag="SEMI / AI", evaluation_status="sl_hit", r_multiple="-1.0", actual_return_pct="-5.0"),
        _pick(tag="SEMI / AI", evaluation_status="sl_hit", r_multiple="-1.0", actual_return_pct="-5.0"),
        _pick(tag="QUALITY", evaluation_status="tp_hit", r_multiple="1.5", actual_return_pct="3.0"),
    ])
    rows = sb.breakdown_by("tag")
    by_g = {r["group"]: r for r in rows}
    assert by_g["SEMI / AI"]["win_rate"] == 0.0
    assert by_g["SEMI / AI"]["total_r"] == -2.0
    assert by_g["QUALITY"]["win_rate"] == 1.0


def test_alpha_averaging(tmp_log):
    _write(tmp_log, [
        _pick(alpha_pct="-3.0"),
        _pick(alpha_pct="1.0"),
    ])
    rows = sb.breakdown_by("trade_type")
    assert rows[0]["avg_alpha_pct"] == -1.0


def test_missing_alpha_handled(tmp_log):
    _write(tmp_log, [_pick(alpha_pct="")])
    rows = sb.breakdown_by("trade_type")
    assert rows[0]["avg_alpha_pct"] is None


def test_unknown_group_label(tmp_log):
    _write(tmp_log, [_pick(regime="")])
    rows = sb.breakdown_by("regime")
    assert rows[0]["group"] == "unknown"


def test_format_text_no_data():
    out = sb.format_breakdown_text("trade_type", [])
    assert "no closed picks" in out


def test_format_text_has_columns():
    rows = [{
        "group": "swing", "n": 2, "wins": 1, "losses": 1,
        "win_rate": 0.5, "avg_return_pct": 1.0,
        "avg_r": 0.25, "total_r": 0.5, "avg_alpha_pct": 0.3,
    }]
    out = sb.format_breakdown_text("trade_type", rows)
    assert "swing" in out and "50%" in out and "0.50" in out


def test_sort_by_count_then_total_r(tmp_log):
    _write(tmp_log, [
        _pick(trade_type="day"),
        _pick(trade_type="swing"),
        _pick(trade_type="swing"),
    ])
    rows = sb.breakdown_by("trade_type")
    assert rows[0]["group"] == "swing"  # n=2 first
    assert rows[1]["group"] == "day"
