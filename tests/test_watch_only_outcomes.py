import json
import subprocess
import sys
from pathlib import Path

from scripts.build_watch_only_outcomes import build_outcomes, write_outputs


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows))


def test_watch_only_outcomes_builds_late_and_opening_range_artifacts(tmp_path):
    data = tmp_path

    write_jsonl(data / "late_daily_ideas_2026-05-08.jsonl", [
        {
            "ticker": "LATE",
            "watch_only": True,
            "source": "news",
            "generated_at_et": "2026-05-08T12:00:00-04:00",
            "watch_buy_price": 10.0,
            "watch_stop_loss": 9.5,
            "watch_take_profit": 11.0,
            "day_high": 11.2,
            "day_low": 9.8,
            "current_price": 10.8,
            "paper_trading_enabled": False,
            "live_trading_enabled": False,
        }
    ])

    write_jsonl(data / "opening_range_observations_2026-05-08.jsonl", [
        {
            "ticker": "ORNG",
            "watch_only": True,
            "source": "intraday_monitor",
            "scanner": "opening_range",
            "ts": "2026-05-08T14:00:00+00:00",
            "entry_observe": 20.0,
            "stop_loss_observe": 19.0,
            "take_profit_observe": 22.0,
            "price": 20.0,
            "mode": "monitoring_only",
        }
    ])

    write_jsonl(data / "opening_range_bars" / "2026-05-08" / "ORNG.jsonl", [
        {
            "ticker": "ORNG",
            "watch_only": True,
            "ts": "2026-05-08T14:01:00+00:00",
            "open": 20.0,
            "high": 21.0,
            "low": 19.8,
            "close": 20.5,
        },
        {
            "ticker": "ORNG",
            "watch_only": True,
            "ts": "2026-05-08T14:02:00+00:00",
            "open": 20.5,
            "high": 22.2,
            "low": 20.4,
            "close": 22.0,
        },
    ])

    outcomes, summary = build_outcomes("2026-05-08", data_dir=data)
    assert summary["watch_only"] is True
    assert summary["official_pick_stats_mutated"] is False
    assert summary["paper_trading_enabled"] is False
    assert summary["live_trading_enabled"] is False
    assert summary["n_outcomes"] == 2

    late = next(o for o in outcomes if o["ticker"] == "LATE")
    assert late["observation_type"] == "late_daily_watch_only"
    assert late["tp_hit"] is True
    assert late["sl_hit"] is False
    assert late["which_hit_first"] == "tp"
    assert late["data_sufficiency_status"] == "range_only_no_intraday_sequence"
    assert late["end_of_window_return_pct"] is None
    assert late["end_of_window_note"] == "unavailable_for_late_range_only_artifact"

    opening = next(o for o in outcomes if o["ticker"] == "ORNG")
    assert opening["observation_type"] == "opening_range_watch_only"
    assert opening["tp_hit"] is True
    assert opening["which_hit_first"] == "tp"
    assert opening["data_sufficiency_status"] == "bar_sequence_available"

    jsonl_path, md_path = write_outputs("2026-05-08", outcomes, summary, data_dir=data)
    assert jsonl_path.exists()
    assert md_path.exists()
    md = md_path.read_text()
    assert "Watch-Only Outcome Report" in md
    assert "Not official picks" in md
    assert "end_return=**n/a**" in md

    assert not (data / "picks_log.csv").exists()
    assert not (data / "signal_journal.jsonl").exists()
    assert not (data / "learning_journal.jsonl").exists()


def test_watch_only_late_range_reports_unknown_order_when_tp_and_sl_inside_range(tmp_path):
    data = tmp_path
    write_jsonl(data / "late_daily_ideas_2026-05-08.jsonl", [
        {
            "ticker": "BOTH",
            "watch_only": True,
            "watch_buy_price": 10.0,
            "watch_stop_loss": 9.5,
            "watch_take_profit": 11.0,
            "day_high": 11.2,
            "day_low": 9.4,
            "current_price": 10.2,
        }
    ])
    write_jsonl(data / "opening_range_observations_2026-05-08.jsonl", [])

    outcomes, summary = build_outcomes("2026-05-08", data_dir=data)
    assert summary["n_outcomes"] == 1
    assert outcomes[0]["tp_hit"] is True
    assert outcomes[0]["sl_hit"] is True
    assert outcomes[0]["which_hit_first"] == "unknown_same_day_range_only"
    assert outcomes[0]["status"] == "tp_and_sl_inside_range_order_unknown"

def test_watch_only_outcomes_script_runs_directly(tmp_path):
    write_jsonl(tmp_path / "late_daily_ideas_2026-05-08.jsonl", [
        {
            "ticker": "CLI",
            "watch_only": True,
            "watch_buy_price": 10.0,
            "watch_stop_loss": 9.5,
            "watch_take_profit": 11.0,
            "day_high": 10.8,
            "day_low": 9.8,
            "current_price": 10.4,
        }
    ])
    write_jsonl(tmp_path / "opening_range_observations_2026-05-08.jsonl", [])

    result = subprocess.run(
        [
            sys.executable,
            "scripts/build_watch_only_outcomes.py",
            "--date",
            "2026-05-08",
            "--data-dir",
            str(tmp_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "[watch-only-outcomes] wrote" in result.stdout
    assert (tmp_path / "watch_only_outcomes_2026-05-08.jsonl").exists()
    assert (tmp_path / "watch_only_outcome_report_2026-05-08.md").exists()

def test_opening_range_outcome_marks_no_forward_bars_after_observation(tmp_path):
    data = tmp_path
    write_jsonl(data / "late_daily_ideas_2026-05-08.jsonl", [])
    write_jsonl(data / "opening_range_observations_2026-05-08.jsonl", [
        {
            "ticker": "LATEBAR",
            "watch_only": True,
            "source": "intraday_monitor",
            "scanner": "opening_range",
            "ts": "2026-05-08T15:00:00+00:00",
            "entry_observe": 20.0,
            "stop_loss_observe": 19.0,
            "take_profit_observe": 22.0,
            "price": 20.0,
            "mode": "monitoring_only",
        }
    ])
    write_jsonl(data / "opening_range_bars" / "2026-05-08" / "LATEBAR.jsonl", [
        {
            "ticker": "LATEBAR",
            "watch_only": True,
            "ts": "2026-05-08T14:00:00+00:00",
            "open": 20.0,
            "high": 21.0,
            "low": 19.8,
            "close": 20.5,
        }
    ])

    outcomes, summary = build_outcomes("2026-05-08", data_dir=data)

    assert summary["n_outcomes"] == 1
    assert outcomes[0]["status"] == "missing_bar_data"
    assert outcomes[0]["data_sufficiency_status"] == "bar_sequence_available_no_forward_bars_after_observation"
    assert outcomes[0]["max_favorable_excursion_pct"] is None
    assert outcomes[0]["max_adverse_excursion_pct"] is None

def test_opening_range_quality_marks_no_forward_bars_data_insufficient(tmp_path):
    data = tmp_path
    write_jsonl(data / "late_daily_ideas_2026-05-08.jsonl", [])
    write_jsonl(data / "opening_range_observations_2026-05-08.jsonl", [
        {
            "ticker": "ORNOFWD",
            "watch_only": True,
            "source": "intraday_monitor",
            "scanner": "opening_range",
            "ts": "2026-05-08T14:10:00+00:00",
            "entry_observe": 101.0,
            "stop_loss_observe": 99.0,
            "take_profit_observe": 104.0,
            "price": 101.0,
            "opening_range_high": 100.0,
            "opening_range_low": 98.0,
            "opening_range_width_pct": 2.0,
            "opening_range_volume": 6000,
            "breakout_pct": 1.0,
            "mode": "monitoring_only",
        }
    ])
    write_jsonl(data / "opening_range_bars" / "2026-05-08" / "ORNOFWD.jsonl", [
        {"ticker": "ORNOFWD", "watch_only": True, "ts": "2026-05-08T14:00:00+00:00", "open": 100.0, "high": 101.0, "low": 99.5, "close": 100.5, "volume": 1000},
        {"ticker": "ORNOFWD", "watch_only": True, "ts": "2026-05-08T14:05:00+00:00", "open": 100.5, "high": 101.2, "low": 100.0, "close": 101.0, "volume": 1000},
    ])

    outcomes, _summary = build_outcomes("2026-05-08", data_dir=data)
    out = outcomes[0]

    assert out["data_sufficiency_status"] == "bar_sequence_available_no_forward_bars_after_observation"
    assert out["opening_range_quality_status"] == "data_insufficient_no_forward_bars"
    assert out["breakout_retest_status"] == "not_evaluable_no_forward_bars"
    assert out["volume_confirmation_status"] == "not_evaluable_no_forward_bars"
    assert out["sustained_breakout"] is None
    assert out["false_breakout"] is None
    assert "no_forward_bars_after_observation" in out["opening_range_quality_flags"]


def test_opening_range_quality_marks_sustained_breakout_tp_first(tmp_path):
    data = tmp_path
    write_jsonl(data / "late_daily_ideas_2026-05-08.jsonl", [])
    write_jsonl(data / "opening_range_observations_2026-05-08.jsonl", [
        {
            "ticker": "ORWIN",
            "watch_only": True,
            "source": "intraday_monitor",
            "scanner": "opening_range",
            "ts": "2026-05-08T14:00:00+00:00",
            "entry_observe": 101.0,
            "stop_loss_observe": 99.0,
            "take_profit_observe": 104.0,
            "price": 101.0,
            "opening_range_high": 100.0,
            "opening_range_low": 98.0,
            "opening_range_width_pct": 2.0,
            "opening_range_volume": 6000,
            "breakout_pct": 1.0,
            "mode": "monitoring_only",
        }
    ])
    write_jsonl(data / "opening_range_bars" / "2026-05-08" / "ORWIN.jsonl", [
        {"ticker": "ORWIN", "watch_only": True, "ts": "2026-05-08T14:05:00+00:00", "open": 101.0, "high": 102.0, "low": 100.5, "close": 101.5, "volume": 1500},
        {"ticker": "ORWIN", "watch_only": True, "ts": "2026-05-08T14:10:00+00:00", "open": 101.5, "high": 104.5, "low": 101.2, "close": 104.0, "volume": 1300},
    ])

    outcomes, _summary = build_outcomes("2026-05-08", data_dir=data)
    out = outcomes[0]

    assert out["status"] == "tp_hit"
    assert out["which_hit_first"] == "tp"
    assert out["opening_range_quality_status"] == "sustained_breakout_tp_hit"
    assert out["sustained_breakout"] is True
    assert out["false_breakout"] is False
    assert out["breakout_retest_status"] == "held_above_opening_range_high"
    assert out["volume_confirmation_status"] == "confirmed"
    assert out["volume_confirmation_ratio"] == 1.5
    assert "tp_hit_before_stop" in out["opening_range_quality_flags"]


def test_opening_range_quality_marks_false_breakout_sl_first(tmp_path):
    data = tmp_path
    write_jsonl(data / "late_daily_ideas_2026-05-08.jsonl", [])
    write_jsonl(data / "opening_range_observations_2026-05-08.jsonl", [
        {
            "ticker": "ORFAIL",
            "watch_only": True,
            "source": "intraday_monitor",
            "scanner": "opening_range",
            "ts": "2026-05-08T14:00:00+00:00",
            "entry_observe": 101.0,
            "stop_loss_observe": 99.0,
            "take_profit_observe": 104.0,
            "price": 101.0,
            "opening_range_high": 100.0,
            "opening_range_low": 98.0,
            "opening_range_width_pct": 1.0,
            "opening_range_volume": 6000,
            "breakout_pct": 2.2,
            "mode": "monitoring_only",
        }
    ])
    write_jsonl(data / "opening_range_bars" / "2026-05-08" / "ORFAIL.jsonl", [
        {"ticker": "ORFAIL", "watch_only": True, "ts": "2026-05-08T14:05:00+00:00", "open": 101.0, "high": 101.2, "low": 98.8, "close": 99.0, "volume": 500},
        {"ticker": "ORFAIL", "watch_only": True, "ts": "2026-05-08T14:10:00+00:00", "open": 99.0, "high": 100.0, "low": 98.5, "close": 99.5, "volume": 600},
    ])

    outcomes, _summary = build_outcomes("2026-05-08", data_dir=data)
    out = outcomes[0]

    assert out["status"] == "sl_hit"
    assert out["which_hit_first"] == "sl"
    assert out["opening_range_quality_status"] == "false_breakout_stop_hit"
    assert out["sustained_breakout"] is False
    assert out["false_breakout"] is True
    assert out["overextended_at_observation"] is True
    assert out["volume_confirmation_status"] == "weak"
    assert "stop_hit_before_target" in out["opening_range_quality_flags"]
    assert "overextended_at_observation" in out["opening_range_quality_flags"]
