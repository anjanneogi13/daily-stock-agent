"""Tests for auto_pause module."""
import csv
from datetime import date
from pathlib import Path
import pytest
from src import auto_pause as ap


@pytest.fixture
def tmp_log(tmp_path, monkeypatch):
    log = tmp_path / "picks_log.csv"
    monkeypatch.setattr(ap, "PICKS_LOG", log)
    return log


def _write(log: Path, rows: list[dict]):
    with log.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def _pick(**o):
    base = {
        "ticker": "X", "tag": "QUALITY", "trade_type": "swing", "regime": "bull",
        "pick_date": "2026-04-25", "evaluated_on": "2026-04-28",
        "evaluation_status": "tp_hit",
        "actual_return_pct": "1.0", "r_multiple": "1.0",
    }
    base.update(o)
    return base


def test_no_log_returns_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(ap, "PICKS_LOG", tmp_path / "missing.csv")
    assert ap.get_paused_set("tag") == {}


def test_zero_win_rule_triggers_at_5(tmp_log):
    rows = [_pick(tag="SEMI", evaluation_status="sl_hit",
                  evaluated_on=f"2026-04-2{i}", r_multiple="-1.0",
                  actual_return_pct="-3.0") for i in range(1, 6)]
    _write(tmp_log, rows)
    paused = ap.get_paused_set("tag", today=date(2026, 4, 30))
    assert "SEMI" in paused
    # Either zero_win (5 losses, 0 wins) OR loss_streak (3+ in a row) is correct
    assert any(k in paused["SEMI"] for k in ("zero_win", "loss_streak"))


def test_no_pause_when_below_all_thresholds(tmp_log):
    """4 picks, no 3-streak, total_R > -5 → no rule fires."""
    rows = [
        _pick(tag="SEMI", evaluation_status="sl_hit", evaluated_on="2026-04-21", r_multiple="-1.0"),
        _pick(tag="SEMI", evaluation_status="expired", evaluated_on="2026-04-22",
              r_multiple="-0.5", actual_return_pct="-1.0"),
        _pick(tag="SEMI", evaluation_status="sl_hit", evaluated_on="2026-04-23", r_multiple="-1.0"),
        _pick(tag="SEMI", evaluation_status="expired", evaluated_on="2026-04-24",
              r_multiple="-0.5", actual_return_pct="-1.0"),
    ]
    _write(tmp_log, rows)
    paused = ap.get_paused_set("tag", today=date(2026, 4, 30))
    assert "SEMI" not in paused


def test_loss_streak_triggers_pause(tmp_log):
    rows = [
        _pick(tag="AI", evaluation_status="tp_hit", evaluated_on="2026-04-20", r_multiple="1.5"),
        _pick(tag="AI", evaluation_status="sl_hit", evaluated_on="2026-04-25", r_multiple="-1.0"),
        _pick(tag="AI", evaluation_status="sl_hit", evaluated_on="2026-04-26", r_multiple="-1.0"),
        _pick(tag="AI", evaluation_status="sl_hit", evaluated_on="2026-04-27", r_multiple="-1.0"),
    ]
    _write(tmp_log, rows)
    paused = ap.get_paused_set("tag", today=date(2026, 4, 30))
    assert "AI" in paused
    assert "loss_streak" in paused["AI"]


def test_loss_streak_broken_by_recent_win(tmp_log):
    rows = [
        _pick(tag="AI", evaluation_status="sl_hit", evaluated_on="2026-04-25", r_multiple="-1.0"),
        _pick(tag="AI", evaluation_status="sl_hit", evaluated_on="2026-04-26", r_multiple="-1.0"),
        _pick(tag="AI", evaluation_status="tp_hit", evaluated_on="2026-04-27", r_multiple="1.5"),
    ]
    _write(tmp_log, rows)
    assert ap.get_paused_set("tag", today=date(2026, 4, 30)) == {}


def test_neg_r_or_streak_fires_on_4_losses(tmp_log):
    """4 consecutive sl_hit @ -1.5R → BOTH loss_streak and neg_R apply.
    Either is acceptable; just verify the group IS paused."""
    rows = [_pick(tag="BIO", evaluation_status="sl_hit",
                  evaluated_on=f"2026-04-2{i}", r_multiple="-1.5",
                  actual_return_pct="-4.0") for i in range(1, 5)]
    _write(tmp_log, rows)
    paused = ap.get_paused_set("tag", today=date(2026, 4, 30))
    assert "BIO" in paused
    assert any(k in paused["BIO"] for k in ("loss_streak", "neg_R", "zero_win"))


def test_lookback_window_excludes_old_data(tmp_log):
    rows = [_pick(tag="SEMI", evaluation_status="sl_hit",
                  evaluated_on=f"2026-01-0{i}", r_multiple="-1.0")
            for i in range(1, 6)]
    _write(tmp_log, rows)
    assert ap.get_paused_set("tag", today=date(2026, 4, 30)) == {}


def test_is_paused_convenience(tmp_log):
    rows = [_pick(tag="SEMI", evaluation_status="sl_hit",
                  evaluated_on=f"2026-04-2{i}", r_multiple="-1.0")
            for i in range(1, 6)]
    _write(tmp_log, rows)
    blocked, reason = ap.is_paused("tag", "SEMI", today=date(2026, 4, 30))
    assert blocked is True and reason is not None
    blocked2, _ = ap.is_paused("tag", "QUALITY", today=date(2026, 4, 30))
    assert blocked2 is False


def test_is_paused_handles_empty_value(tmp_log):
    _write(tmp_log, [_pick()])
    blocked, _ = ap.is_paused("tag", "")
    assert blocked is False


def test_format_summary_no_pauses(tmp_log):
    _write(tmp_log, [_pick()])
    out = ap.format_paused_summary(today=date(2026, 4, 30))
    assert "no groups currently paused" in out


def test_format_summary_with_pauses(tmp_log):
    rows = [_pick(tag="SEMI", evaluation_status="sl_hit",
                  evaluated_on=f"2026-04-2{i}", r_multiple="-1.0")
            for i in range(1, 6)]
    _write(tmp_log, rows)
    out = ap.format_paused_summary(today=date(2026, 4, 30))
    assert "SEMI" in out and "❌" in out
