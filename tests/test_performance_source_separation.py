import csv
from datetime import datetime
from pathlib import Path

from src.performance_source_separation import (
    LAYMAN_PERFORMANCE_SOURCE_NOTE,
    filter_official_performance_rows,
    is_watch_only_row,
)


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = sorted({k for row in rows for k in row})
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def closed_row(ticker, *, watch_only=False, pnl=100, status="tp_hit", pick_date=None, evaluated_on=None):
    pick_date = pick_date or datetime.now().strftime("%Y-%m-%d")
    evaluated_on = evaluated_on or datetime.now().strftime("%Y-%m-%d")
    return {
        "ticker": ticker,
        "pick_date": pick_date,
        "evaluated_on": evaluated_on,
        "status": "CLOSED",
        "evaluation_status": status,
        "trade_type": "day",
        "entry": "10",
        "stop_loss": "9",
        "exit_price": "11" if pnl >= 0 else "9",
        "actual_return_pct": "10" if pnl >= 0 else "-10",
        "pnl_dollar": str(pnl),
        "watch_only": "true" if watch_only else "false",
    }


def test_source_helper_identifies_watch_only_rows():
    assert is_watch_only_row({"watch_only": True}) is True
    assert is_watch_only_row({"watch_only": "true"}) is True
    assert is_watch_only_row({"watch_only": "1"}) is True
    assert is_watch_only_row({"watch_only": "false"}) is False
    rows = [{"watch_only": "true"}, {"watch_only": "false"}, {}]
    assert filter_official_performance_rows(rows) == [{"watch_only": "false"}, {}]


def test_performance_tracker_excludes_watch_only_rows(tmp_path, monkeypatch):
    import src.performance_tracker as tracker

    picks = tmp_path / "picks_log.csv"
    write_csv(picks, [
        closed_row("OFFWIN", watch_only=False, pnl=100, status="tp_hit"),
        closed_row("OFFLOSS", watch_only=False, pnl=-50, status="sl_hit"),
        closed_row("WATCH", watch_only=True, pnl=9999, status="tp_hit"),
    ])

    monkeypatch.setattr(tracker, "PICKS_LOG", picks)
    metrics = tracker.compute_segmented_metrics()

    assert metrics["source_separation"]["excluded_watch_only_rows"] == 1
    assert metrics["overall"]["n_trades"] == 2
    assert metrics["overall"]["wins"] == 1
    assert metrics["overall"]["losses"] == 1
    assert metrics["overall"]["best_ticker"] == "OFFWIN"


def test_layman_weekly_filters_watch_only_and_discloses_source(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    write_csv(Path("data/picks_log.csv"), [
        closed_row("OFFICIAL", watch_only=False, pnl=100),
        closed_row("WATCH", watch_only=True, pnl=9999),
    ])

    import scripts.send_layman_weekly as weekly

    outcomes = weekly._last_week_outcomes()
    assert [row["ticker"] for row in outcomes] == ["OFFICIAL"]

    msg = weekly.build_message(outcomes)
    assert LAYMAN_PERFORMANCE_SOURCE_NOTE in msg
    assert "Excludes watch-only late ideas" in msg
    assert "WATCH" not in msg


def test_layman_monthly_evening_yearly_disclose_source():
    import scripts.send_layman_monthly as monthly
    import scripts.send_layman_evening as evening
    import scripts.send_layman_yearly as yearly

    monthly_msg = monthly.build_message([closed_row("M", watch_only=False, pnl=10)])
    evening_msg = evening.build_message([closed_row("E", watch_only=False, pnl=10)])
    assert LAYMAN_PERFORMANCE_SOURCE_NOTE in monthly_msg
    assert LAYMAN_PERFORMANCE_SOURCE_NOTE in evening_msg

    no_year_msg = yearly.build_message(1999)
    assert LAYMAN_PERFORMANCE_SOURCE_NOTE in no_year_msg

def test_weekly_report_card_discloses_source_separation():
    from scripts.weekly_report_card import format_report
    from src.performance_source_separation import PERFORMANCE_SOURCE_NOTE

    metrics = {
        "source_separation": {"excluded_watch_only_rows": 2},
        "overall": {
            "n_trades": 2,
            "wins": 1,
            "losses": 1,
            "win_rate": 50.0,
            "avg_r": 0.25,
            "sharpe": 0.0,
            "max_dd_pct": 1.0,
            "profit_factor": 1.2,
            "expectancy_r": 0.25,
            "best_ticker": "GOOD",
            "best_trade_r": 1.0,
            "worst_ticker": "BAD",
            "worst_trade_r": -1.0,
        },
        "last_7_days": {
            "n_trades": 1,
            "wins": 1,
            "losses": 0,
            "win_rate": 100.0,
            "avg_r": 1.0,
            "total_return_pct": 5.0,
        },
        "day_trades": {"n_trades": 1, "win_rate": 100.0, "avg_r": 1.0},
        "swing_trades": {"n_trades": 1, "win_rate": 0.0, "avg_r": -1.0},
    }

    report = format_report(metrics)

    assert PERFORMANCE_SOURCE_NOTE in report
    assert "Watch-only rows excluded: 2" in report
    assert "watch-only late ideas" in report
