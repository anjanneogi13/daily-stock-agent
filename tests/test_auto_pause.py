"""Tests for Pillar 4 prep — auto_pause observe-mode."""
import sys
from pathlib import Path
from datetime import datetime, timedelta
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.auto_pause import (
    consecutive_losses, rolling_r, rolling_win_rate,
    compute_score, classify, format_summary,
)


def _row(status, r_mult, days_ago=0):
    d = datetime.now() - timedelta(days=days_ago)
    return {
        "evaluation_status": status,
        "r_multiple": str(r_mult),
        "evaluated_on": d.strftime("%Y-%m-%d"),
        "_evaluated_dt": d,
    }


def test_consecutive_losses_zero():
    assert consecutive_losses([]) == 0


def test_consecutive_losses_streak():
    rows = [_row("tp_hit", 1.5, 10), _row("sl_hit", -1, 5),
            _row("sl_hit", -1, 3), _row("sl_hit", -1, 1)]
    assert consecutive_losses(rows) == 3


def test_consecutive_loss_broken_by_win():
    rows = [_row("sl_hit", -1, 5), _row("sl_hit", -1, 3), _row("tp_hit", 1.5, 1)]
    assert consecutive_losses(rows) == 0


def test_rolling_r_sums_window():
    rows = [_row("tp_hit", 1.5, 5),
            _row("sl_hit", -1.0, 3),
            _row("sl_hit", -1.0, 100)]  # outside window
    assert rolling_r(rows, days=14) == 0.5


def test_rolling_win_rate():
    rows = [_row("tp_hit", 1.5, 5), _row("sl_hit", -1, 3)]
    assert rolling_win_rate(rows, days=14) == 0.5


def test_classify_thresholds():
    assert "GREEN" in classify(0)
    assert "ELEVATED" in classify(4)
    assert "AMBER" in classify(6)
    assert "RED" in classify(9)


def test_compute_score_clean():
    """1 win, no streak — should be GREEN."""
    rows = [_row("tp_hit", 1.5, 5)]
    r = compute_score(rows)
    assert r["score"] <= 2
    assert "GREEN" in r["level"]
    assert r["would_pause"] is False


def test_compute_score_crisis_red():
    """Build a real crisis: 6 consecutive losses, big drawdown."""
    rows = [_row("sl_hit", -1.5, days) for days in [12, 10, 8, 6, 4, 2]]
    r = compute_score(rows)
    assert r["score"] >= 7  # streak(4) + dd(4) capped at 10
    assert r["would_pause"] is True


def test_format_summary_shows_reasons():
    rows = [_row("sl_hit", -1, days) for days in [6, 4, 2]]
    r = compute_score(rows)
    text = format_summary(r)
    assert "PAUSE SIGNAL" in text
    assert any("loss" in line.lower() for line in text.split("\n"))


def test_observe_mode_never_enforces():
    """v0.1 must always have enforced=False."""
    rows = [_row("sl_hit", -2, days) for days in range(1, 8)]
    r = compute_score(rows)
    assert r["enforced"] is False


# ════════════════════════════════════════════════════════════════
# Pillar 5 group pause — get_paused_set (shipped Sep 2026; main.py
# had imported it since May 2026 while it didn't exist)
# ════════════════════════════════════════════════════════════════
import csv as _csv
from datetime import datetime as _dt

from src import auto_pause as ap


def _write_log(path, rows):
    with path.open("w", newline="") as f:
        w = _csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def _closed_row(**o):
    base = {
        "ticker": "X", "tag": "QUALITY", "trade_type": "swing",
        "watch_only": "", "pick_date": "2026-04-25",
        "evaluated_on": "2026-04-28", "evaluation_status": "tp_hit",
        "actual_return_pct": "1.0", "r_multiple": "1.0",
    }
    base.update(o)
    return base


def test_get_paused_set_missing_log(tmp_path, monkeypatch):
    monkeypatch.setattr(ap, "PICKS_LOG", tmp_path / "missing.csv")
    assert ap.get_paused_set("tag") == {}


def test_zero_win_rule_triggers_at_5(tmp_path, monkeypatch):
    log = tmp_path / "p.csv"
    rows = [_closed_row(tag="SEMI", evaluation_status="sl_hit",
                        evaluated_on=f"2026-04-2{i}", r_multiple="-1.0",
                        actual_return_pct="-3.0") for i in range(1, 6)]
    _write_log(log, rows)
    monkeypatch.setattr(ap, "PICKS_LOG", log)
    paused = ap.get_paused_set("tag", today=_dt(2026, 4, 30))
    assert paused.get("SEMI", "").startswith("zero_win 0/5")


def test_zero_win_rule_needs_min_n(tmp_path, monkeypatch):
    log = tmp_path / "p.csv"
    rows = [_closed_row(tag="SEMI", evaluation_status="sl_hit",
                        evaluated_on=f"2026-04-2{i}", r_multiple="-1.0",
                        actual_return_pct="-3.0") for i in range(1, 4)]
    _write_log(log, rows)
    monkeypatch.setattr(ap, "PICKS_LOG", log)
    # n=3 < MIN_N_FOR_ZERO_WIN but 3x sl_hit tail → loss_streak fires instead
    paused = ap.get_paused_set("tag", today=_dt(2026, 4, 30))
    assert "loss_streak" in paused.get("SEMI", "")


def test_loss_streak_broken_by_win(tmp_path, monkeypatch):
    log = tmp_path / "p.csv"
    rows = [
        _closed_row(evaluated_on="2026-04-21", evaluation_status="sl_hit", r_multiple="-1.0"),
        _closed_row(evaluated_on="2026-04-22", evaluation_status="sl_hit", r_multiple="-1.0"),
        _closed_row(evaluated_on="2026-04-23", evaluation_status="tp_hit", r_multiple="1.5"),
    ]
    _write_log(log, rows)
    monkeypatch.setattr(ap, "PICKS_LOG", log)
    assert ap.get_paused_set("tag", today=_dt(2026, 4, 30)) == {}


def test_neg_r_rule(tmp_path, monkeypatch):
    log = tmp_path / "p.csv"
    # Mixed outcomes (no zero_win, no streak) but massively negative total R
    rows = [
        _closed_row(evaluated_on="2026-04-20", evaluation_status="tp_hit", r_multiple="0.5"),
        _closed_row(evaluated_on="2026-04-21", evaluation_status="sl_hit", r_multiple="-2.0"),
        _closed_row(evaluated_on="2026-04-22", evaluation_status="sl_hit", r_multiple="-2.0"),
        _closed_row(evaluated_on="2026-04-23", evaluation_status="expired", r_multiple="-2.0"),
    ]
    _write_log(log, rows)
    monkeypatch.setattr(ap, "PICKS_LOG", log)
    paused = ap.get_paused_set("tag", today=_dt(2026, 4, 30))
    assert "neg_R" in paused.get("QUALITY", "")


def test_watch_only_rows_never_count(tmp_path, monkeypatch):
    log = tmp_path / "p.csv"
    rows = [_closed_row(tag="SEMI", evaluation_status="sl_hit", watch_only="true",
                        evaluated_on=f"2026-04-2{i}", r_multiple="-1.0",
                        actual_return_pct="-3.0") for i in range(1, 6)]
    _write_log(log, rows)
    monkeypatch.setattr(ap, "PICKS_LOG", log)
    assert ap.get_paused_set("tag", today=_dt(2026, 4, 30)) == {}


def test_empty_group_key_never_pausable(tmp_path, monkeypatch):
    log = tmp_path / "p.csv"
    rows = [_closed_row(tag="", evaluation_status="sl_hit",
                        evaluated_on=f"2026-04-2{i}", r_multiple="-1.0",
                        actual_return_pct="-3.0") for i in range(1, 6)]
    _write_log(log, rows)
    monkeypatch.setattr(ap, "PICKS_LOG", log)
    assert ap.get_paused_set("tag", today=_dt(2026, 4, 30)) == {}


def test_old_closes_outside_lookback_ignored(tmp_path, monkeypatch):
    log = tmp_path / "p.csv"
    rows = [_closed_row(tag="SEMI", evaluation_status="sl_hit",
                        evaluated_on="2026-01-05", r_multiple="-1.0",
                        actual_return_pct="-3.0") for _ in range(5)]
    _write_log(log, rows)
    monkeypatch.setattr(ap, "PICKS_LOG", log)
    assert ap.get_paused_set("tag", lookback_days=30, today=_dt(2026, 4, 30)) == {}


def test_is_group_paused_pair(tmp_path, monkeypatch):
    log = tmp_path / "p.csv"
    rows = [_closed_row(tag="SEMI", evaluation_status="sl_hit",
                        evaluated_on=f"2026-04-2{i}", r_multiple="-1.0",
                        actual_return_pct="-3.0") for i in range(1, 6)]
    _write_log(log, rows)
    monkeypatch.setattr(ap, "PICKS_LOG", log)
    blocked, reason = ap.is_group_paused("tag", "SEMI", today=_dt(2026, 4, 30))
    assert blocked and "zero_win" in reason
    ok, none_reason = ap.is_group_paused("tag", "QUALITY", today=_dt(2026, 4, 30))
    assert not ok and none_reason is None


def test_main_py_import_contract():
    """main.py:1087 imports get_paused_set — this must never break again."""
    from src.auto_pause import get_paused_set  # noqa: F401
