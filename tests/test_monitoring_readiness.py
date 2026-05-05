"""Bug #21 (2026-05-05): monitoring-readiness dashboard.

The founder decision says paper trading is not allowed until post-floor
performance gates pass by trade type:
  - day trades >60% win rate plus positive expectancy
  - swing trades >66% win rate plus positive expectancy
  - monster / long holder picks >90% win rate plus positive expectancy
"""

import json
import subprocess

from scripts.monitoring_readiness import (
    CLOSED_STATUSES,
    classify_bucket,
    evaluate_bucket,
    run_all,
)


def row(**kw):
    base = {
        "pick_date": "2026-05-05",
        "trade_type": "swing",
        "evaluation_status": "tp_hit",
        "r_multiple": "1.0",
        "is_monster": "false",
    }
    base.update(kw)
    return base


def test_classify_bucket_monster_overrides_trade_type():
    assert classify_bucket(row(is_monster="true", trade_type="day")) == "monster"
    assert classify_bucket(row(monster_score="0.91", trade_type="swing")) == "monster"


def test_classify_bucket_day_and_swing():
    assert classify_bucket(row(trade_type="day")) == "day"
    assert classify_bucket(row(trade_type="swing")) == "swing"
    assert classify_bucket(row(trade_type="")) == "swing"


def test_evaluate_bucket_requires_win_rate_and_positive_expectancy():
    rows = [
        row(evaluation_status="tp_hit", r_multiple="1.0"),
        row(evaluation_status="tp_hit", r_multiple="0.5"),
        row(evaluation_status="sl_hit", r_multiple="-1.0"),
    ]

    result = evaluate_bucket("day", rows, threshold=0.60, min_n=3)

    assert result["bucket"] == "day"
    assert result["n_closed"] == 3
    assert result["wins"] == 2
    assert round(result["win_rate"], 4) == 0.6667
    assert round(result["avg_r"], 4) == 0.1667
    assert result["positive_expectancy"] is True
    assert result["ready"] is True


def test_evaluate_bucket_blocks_negative_expectancy_even_with_high_win_rate():
    rows = [
        row(evaluation_status="tp_hit", r_multiple="0.1"),
        row(evaluation_status="tp_hit", r_multiple="0.1"),
        row(evaluation_status="sl_hit", r_multiple="-1.0"),
    ]

    result = evaluate_bucket("swing", rows, threshold=0.66, min_n=3)

    assert result["win_rate"] > 0.66
    assert result["avg_r"] < 0
    assert result["positive_expectancy"] is False
    assert result["ready"] is False
    assert "avg_r" in " ".join(result["blockers"])


def test_run_all_uses_post_floor_and_trade_type_buckets():
    rows = [
        row(pick_date="2026-05-01", trade_type="day", evaluation_status="tp_hit", r_multiple="5.0"),
        row(pick_date="2026-05-05", trade_type="day", evaluation_status="tp_hit", r_multiple="1.0"),
        row(pick_date="2026-05-05", trade_type="day", evaluation_status="sl_hit", r_multiple="-1.0"),
        row(pick_date="2026-05-05", trade_type="swing", evaluation_status="tp_hit", r_multiple="1.0"),
        row(pick_date="2026-05-05", trade_type="swing", evaluation_status="sl_hit", r_multiple="-1.0"),
        row(pick_date="2026-05-05", trade_type="swing", is_monster="true", evaluation_status="tp_hit", r_multiple="2.0"),
    ]

    results = run_all(rows, floor="2026-05-02", min_n=1)
    by_bucket = {r["bucket"]: r for r in results}

    assert by_bucket["day"]["n_closed"] == 2
    assert by_bucket["swing"]["n_closed"] == 2
    assert by_bucket["monster"]["n_closed"] == 1


def test_cli_json_outputs_three_buckets():
    out = subprocess.check_output(
        ["python", "scripts/monitoring_readiness.py", "--json"],
        text=True,
    )
    data = json.loads(out)
    assert [r["bucket"] for r in data] == ["day", "swing", "monster"]
