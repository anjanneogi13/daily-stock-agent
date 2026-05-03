"""Tests for src/calibration (T37+T38)."""
from __future__ import annotations
import csv
import json
from pathlib import Path

import pytest

from src import calibration as cal


# ───────────────── fixtures ─────────────────

def _write_picks(dir_: Path, rows: list[dict]) -> Path:
    dir_.mkdir(parents=True, exist_ok=True)
    p = dir_ / "picks.csv"
    if not rows:
        p.write_text("ticker\n")
        return p
    cols = list(rows[0].keys())
    with p.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    return p


@pytest.fixture
def fake_run(tmp_path: Path):
    run = tmp_path / "results" / "run_001"
    rows = [
        # 4 winners, 2 losers, mixed factors
        {"ticker":"AAA","trade_type":"swing","score":0.9,"rsi":45,"atr":2.0,"entry":100,
         "stop_loss":98,"take_profit":104,"exit_status":"tp_hit","exit_price":104,
         "days_held":5,"r_multiple":2.0,"return_pct":4.0,"pick_date":"2025-01-05","exit_date":"2025-01-10"},
        {"ticker":"BBB","trade_type":"swing","score":0.6,"rsi":55,"atr":3.0,"entry":50,
         "stop_loss":48,"take_profit":54,"exit_status":"sl_hit","exit_price":48,
         "days_held":2,"r_multiple":-1.0,"return_pct":-4.0,"pick_date":"2025-01-06","exit_date":"2025-01-08"},
        {"ticker":"CCC","trade_type":"swing","score":0.8,"rsi":35,"atr":4.0,"entry":200,
         "stop_loss":196,"take_profit":208,"exit_status":"max_hold","exit_price":205,
         "days_held":10,"r_multiple":1.25,"return_pct":2.5,"pick_date":"2025-02-01","exit_date":"2025-02-15"},
        {"ticker":"DDD","trade_type":"day","score":0.95,"rsi":75,"atr":5.0,"entry":300,
         "stop_loss":290,"take_profit":320,"exit_status":"tp_hit","exit_price":320,
         "days_held":1,"r_multiple":2.0,"return_pct":6.7,"pick_date":"2025-02-02","exit_date":"2025-02-03"},
        {"ticker":"EEE","trade_type":"swing","score":0.55,"rsi":25,"atr":1.0,"entry":80,
         "stop_loss":78,"take_profit":84,"exit_status":"sl_hit","exit_price":78,
         "days_held":3,"r_multiple":-1.0,"return_pct":-2.5,"pick_date":"2025-03-10","exit_date":"2025-03-13"},
        {"ticker":"FFF","trade_type":"swing","score":0.88,"rsi":60,"atr":2.5,"entry":150,
         "stop_loss":147,"take_profit":156,"exit_status":"max_hold","exit_price":154,
         "days_held":12,"r_multiple":1.33,"return_pct":2.7,"pick_date":"2025-03-15","exit_date":"2025-03-27"},
    ]
    _write_picks(run, rows)
    return run


# ───────────────── load + structure ─────────────────

def test_list_runs_empty(tmp_path: Path):
    assert cal.list_runs(tmp_path / "noexist") == []

def test_latest_run(tmp_path: Path):
    (tmp_path / "a").mkdir(); (tmp_path / "b").mkdir()
    assert cal.latest_run(tmp_path).name == "b"

def test_load_picks_coerces_floats(fake_run):
    rows = cal.load_picks(fake_run)
    assert len(rows) == 6
    assert isinstance(rows[0]["score"], float)
    assert isinstance(rows[0]["r_multiple"], float)
    assert rows[0]["ticker"] == "AAA"

def test_load_picks_handles_missing_csv(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        cal.load_picks(tmp_path / "nope")

def test_load_picks_handles_blank_numeric(tmp_path: Path):
    p = tmp_path / "r"
    p.mkdir()
    (p / "picks.csv").write_text("ticker,score,r_multiple\nXXX,,\n")
    rows = cal.load_picks(p)
    assert rows[0]["score"] is None
    assert rows[0]["r_multiple"] is None


# ───────────────── bucketing helpers ─────────────────

def test_rsi_buckets():
    assert cal._rsi_bucket(None) == "rsi_na"
    assert cal._rsi_bucket(20) == "rsi_oversold(<30)"
    assert cal._rsi_bucket(40) == "rsi_30-50"
    assert cal._rsi_bucket(60) == "rsi_50-70"
    assert cal._rsi_bucket(80) == "rsi_overbought(>=70)"

def test_score_buckets():
    assert cal._score_bucket(0.4) == "score_<0.5"
    assert cal._score_bucket(0.6) == "score_0.5-0.7"
    assert cal._score_bucket(0.8) == "score_0.7-0.85"
    assert cal._score_bucket(0.9) == "score_>=0.85"
    assert cal._score_bucket(None) == "score_na"

def test_atr_buckets():
    assert cal._atr_bucket(None, 100) == "atrpct_na"
    assert cal._atr_bucket(2, 0) == "atrpct_na"
    assert cal._atr_bucket(1, 100) == "atrpct_<1.5"   # 1%
    assert cal._atr_bucket(2, 100) == "atrpct_1.5-3"  # 2%
    assert cal._atr_bucket(4, 100) == "atrpct_3-5"    # 4%
    assert cal._atr_bucket(6, 100) == "atrpct_>=5"    # 6%

def test_month_bucket():
    assert cal._month_bucket("2025-03-15") == "2025-03"
    assert cal._month_bucket(None) == "date_na"
    assert cal._month_bucket("") == "date_na"


# ───────────────── attribute_by + reports ─────────────────

def test_is_win():
    assert cal._is_win({"r_multiple": 1.0}) is True
    assert cal._is_win({"r_multiple": -0.5}) is False
    assert cal._is_win({"r_multiple": 0}) is False
    assert cal._is_win({"r_multiple": None}) is False

def test_attribute_by_basic(fake_run):
    rows = cal.load_picks(fake_run)
    stats = cal.attribute_by(rows, lambda r: r["trade_type"], min_n=1)
    by_name = {s.bucket: s for s in stats}
    assert "swing" in by_name and "day" in by_name
    assert by_name["swing"].n == 5
    assert by_name["day"].n == 1
    assert by_name["day"].win_rate == 1.0

def test_attribute_by_min_n_drops_small_buckets(fake_run):
    rows = cal.load_picks(fake_run)
    stats = cal.attribute_by(rows, lambda r: r["trade_type"], min_n=5)
    names = {s.bucket for s in stats}
    assert "swing" in names
    assert "day" not in names  # only 1 row

def test_per_factor_report_keys(fake_run):
    rows = cal.load_picks(fake_run)
    rep = cal.per_factor_report(rows, min_n=1)
    assert set(rep.keys()) == {"trade_type", "rsi", "score", "atrpct", "exit_status"}
    # every entry is a list of dicts with required cols
    for table in rep.values():
        for row in table:
            assert {"bucket","n","wins","win_rate","mean_r","total_r","mean_return_pct"} <= row.keys()

def test_per_timeframe_chronological(fake_run):
    rows = cal.load_picks(fake_run)
    rep = cal.per_timeframe_report(rows, min_n=1)
    months = [r["bucket"] for r in rep]
    assert months == sorted(months)  # chronological
    assert "2025-01" in months and "2025-03" in months


def test_overall_summary_math(fake_run):
    rows = cal.load_picks(fake_run)
    s = cal.overall_summary(rows)
    assert s["n"] == 6
    assert s["wins"] == 4   # AAA, CCC, DDD, FFF
    assert s["win_rate"] == round(4/6, 3)
    # total R = 2 + (-1) + 1.25 + 2 + (-1) + 1.33 = 4.58
    assert abs(s["total_r"] - 4.58) < 0.01

def test_overall_summary_empty():
    s = cal.overall_summary([])
    assert s["n"] == 0
    assert s["win_rate"] == 0.0


# ───────────────── CLI ─────────────────

def test_cli_summary_runs(fake_run, tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(cal, "RESULTS_ROOT", fake_run.parent)
    rc = cal.main(["summary", "--run", fake_run.name, "--min-n", "1"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "trade_type" in out
    assert "swing" in out

def test_cli_factors_json(fake_run, monkeypatch, capsys):
    monkeypatch.setattr(cal, "RESULTS_ROOT", fake_run.parent)
    rc = cal.main(["factors", "--run", fake_run.name, "--min-n", "1", "--json"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert "trade_type" in payload

def test_cli_timeframes_runs(fake_run, monkeypatch, capsys):
    monkeypatch.setattr(cal, "RESULTS_ROOT", fake_run.parent)
    rc = cal.main(["timeframes", "--run", fake_run.name, "--min-n", "1"])
    assert rc == 0
    assert "2025-01" in capsys.readouterr().out

def test_cli_unknown_run_exits(monkeypatch):
    monkeypatch.setattr(cal, "RESULTS_ROOT", Path("/nonexistent"))
    with pytest.raises(SystemExit):
        cal.main(["summary", "--run", "ghost"])
