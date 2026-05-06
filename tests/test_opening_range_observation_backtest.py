import json
import subprocess
from pathlib import Path

from scripts.backtest_opening_range_observations import (
    candidate_bar_paths,
    evaluate_observation_outcome,
    format_report,
    observation_date,
    summarize_outcomes,
)


def obs(**kw):
    base = {
        "ts": "2026-05-06T13:45:00+00:00",
        "ticker": "NET",
        "scanner": "opening_range",
        "mode": "monitoring_only",
        "watch_only": True,
        "price": 101.6,
        "entry_observe": 101.6,
        "stop_loss_observe": 99.7,
        "take_profit_observe": 104.45,
    }
    base.update(kw)
    return base


def bar(ts, high, low, close):
    return {"ts": ts, "high": high, "low": low, "close": close}


def write_jsonl(path: Path, rows: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")


def test_observation_date_and_candidate_paths():
    paths = candidate_bar_paths(obs(ticker="net"), bars_dir=Path("bars"))
    assert observation_date(obs()) == "2026-05-06"
    assert paths == [
        Path("bars/2026-05-06/NET.jsonl"),
        Path("bars/NET_2026-05-06.jsonl"),
    ]


def test_evaluate_observation_tp_hit():
    result = evaluate_observation_outcome(obs(), [
        bar("2026-05-06T13:50:00+00:00", high=102.0, low=101.0, close=101.8),
        bar("2026-05-06T13:55:00+00:00", high=104.6, low=102.0, close=104.5),
    ])
    assert result["status"] == "tp_hit"
    assert result["evaluated"] is True
    assert result["exit_price"] == 104.45
    assert result["r_multiple"] > 0


def test_evaluate_observation_sl_hit_conservative_same_bar():
    result = evaluate_observation_outcome(obs(), [
        bar("2026-05-06T13:50:00+00:00", high=105.0, low=99.0, close=104.0),
    ])
    assert result["status"] == "sl_hit"
    assert result["evaluated"] is True
    assert result["exit_price"] == 99.7
    assert result["r_multiple"] == -1.0


def test_evaluate_observation_timeout_uses_last_close():
    result = evaluate_observation_outcome(obs(), [
        bar("2026-05-06T13:50:00+00:00", high=102.0, low=100.5, close=101.9),
        bar("2026-05-06T14:00:00+00:00", high=102.3, low=100.8, close=102.0),
    ])
    assert result["status"] == "timeout"
    assert result["evaluated"] is True
    assert result["exit_price"] == 102.0


def test_evaluate_observation_missing_bars():
    result = evaluate_observation_outcome(obs(), [])
    assert result["status"] == "missing_bar_data"
    assert result["evaluated"] is False


def test_summarize_outcomes_never_marks_ready_for_paper_trading():
    summary = summarize_outcomes([
        {"ticker": "NET", "status": "tp_hit", "evaluated": True, "r_multiple": 1.5},
        {"ticker": "AAPL", "status": "sl_hit", "evaluated": True, "r_multiple": -1.0},
        {"ticker": "MSFT", "status": "missing_bar_data", "evaluated": False},
    ])
    assert summary["n_observations"] == 3
    assert summary["n_evaluated"] == 2
    assert summary["status_counts"] == {
        "missing_bar_data": 1,
        "sl_hit": 1,
        "tp_hit": 1,
    }
    assert summary["paper_trading_enabled"] is False
    assert summary["ready_for_paper_trading"] is False
    assert summary["sample_too_small"] is True


def test_format_report_mentions_read_only_and_paper_disabled():
    report = format_report(summarize_outcomes([]))
    assert "OPENING-RANGE OBSERVATION BACKTEST" in report
    assert "Read-only" in report
    assert "Paper trading: DISABLED" in report


def test_cli_json_evaluates_fixture_files(tmp_path):
    obs_path = tmp_path / "opening_range_observations_2026-05-06.jsonl"
    bars_path = tmp_path / "bars" / "2026-05-06" / "NET.jsonl"
    write_jsonl(obs_path, [obs()])
    write_jsonl(bars_path, [
        bar("2026-05-06T13:50:00+00:00", high=104.7, low=101.0, close=104.5),
    ])

    out = subprocess.check_output([
        "python",
        "scripts/backtest_opening_range_observations.py",
        "--observations",
        str(tmp_path / "opening_range_observations_*.jsonl"),
        "--bars-dir",
        str(tmp_path / "bars"),
        "--json",
    ], text=True)

    data = json.loads(out)
    assert data["n_observations"] == 1
    assert data["n_evaluated"] == 1
    assert data["status_counts"] == {"tp_hit": 1}
    assert data["ready_for_paper_trading"] is False


def test_cli_human_report_handles_no_observations(tmp_path):
    out = subprocess.check_output([
        "python",
        "scripts/backtest_opening_range_observations.py",
        "--observations",
        str(tmp_path / "missing_*.jsonl"),
    ], text=True)
    assert "Observations:          0" in out
    assert "Paper trading: DISABLED" in out
