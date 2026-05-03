"""Tests for src/weight_proposer (T39)."""
from __future__ import annotations
import csv
import json
from pathlib import Path

import pytest

from src import weight_proposer as wp
from src import calibration as cal


def _write_picks(dir_: Path, rows: list[dict]) -> Path:
    dir_.mkdir(parents=True, exist_ok=True)
    p = dir_ / "picks.csv"
    cols = list(rows[0].keys())
    with p.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    return p


@pytest.fixture
def isolated_proposals(tmp_path: Path, monkeypatch):
    fake = tmp_path / "weight_proposals.jsonl"
    monkeypatch.setattr(wp, "PROPOSALS", fake)
    return fake


def _make_row(score=0.8, rsi=50, atr=2.0, entry=100, r=0.5,
              tt="swing", ret=2.0, pd_="2025-01-15", st="max_hold"):
    return {
        "ticker":"X","trade_type":tt,"score":score,"rsi":rsi,"atr":atr,
        "entry":entry,"stop_loss":entry*0.98,"take_profit":entry*1.04,
        "exit_status":st,"exit_price":entry*(1+ret/100),"days_held":5,
        "r_multiple":r,"return_pct":ret,"pick_date":pd_,"exit_date":pd_,
    }


# ───────────────── classification + math ─────────────────

def test_classify_boost():
    assert wp._classify(0.20, 0.55) == "boost"

def test_classify_penalize():
    assert wp._classify(-0.15, 0.40) == "penalize"

def test_classify_kill():
    assert wp._classify(-0.40, 0.30) == "kill"

def test_classify_kill_requires_low_winrate():
    # bias bad enough but win_rate decent → only penalize, not kill
    assert wp._classify(-0.40, 0.50) == "penalize"

def test_classify_neutral_returns_none():
    assert wp._classify(0.05, 0.50) is None
    assert wp._classify(-0.05, 0.50) is None

def test_delta_pct_capped_positive():
    # bias 0.50 × 25 = 12.5 → capped at +5
    assert wp._delta_pct(0.50, "boost") == 5.0

def test_delta_pct_capped_negative():
    assert wp._delta_pct(-0.50, "penalize") == -5.0

def test_delta_pct_kill_always_minus_cap():
    assert wp._delta_pct(-0.10, "kill") == -5.0
    assert wp._delta_pct(-0.99, "kill") == -5.0

def test_confidence_scales_with_n():
    assert wp._confidence(0) == 0.0
    assert wp._confidence(25) == round((25/100)**0.5, 3)  # 0.5
    assert wp._confidence(100) == 1.0
    assert wp._confidence(500) == 1.0  # capped


# ───────────────── propose() integration ─────────────────

def test_propose_empty_returns_empty():
    assert wp.propose([], "run_x") == []

def test_propose_neutral_data_no_proposals():
    rows = [_make_row(r=0.05) for _ in range(50)]  # all near-zero R
    assert wp.propose(rows, "neut") == []

def test_propose_detects_bad_bucket():
    # 40 rows with rsi<30 and very negative R → kill
    bad = [_make_row(rsi=20, r=-0.6) for _ in range(40)]
    # 60 baseline winners to lift overall mean
    good = [_make_row(rsi=55, r=0.6) for _ in range(60)]
    props = wp.propose(bad + good, "run")
    by_bucket = {p.bucket: p for p in props}
    assert "rsi_oversold(<30)" in by_bucket
    assert by_bucket["rsi_oversold(<30)"].action in ("kill", "penalize")

def test_propose_detects_good_bucket():
    great = [_make_row(score=0.95, r=1.5) for _ in range(35)]
    avg   = [_make_row(score=0.75, r=0.0) for _ in range(80)]
    props = wp.propose(great + avg, "r")
    boosts = [p for p in props if p.action == "boost"]
    assert any(p.bucket == "score_>=0.85" for p in boosts)

def test_propose_skips_low_n_buckets():
    # only 10 oversold picks — below default min_n=30
    bad = [_make_row(rsi=20, r=-1.0) for _ in range(10)]
    good = [_make_row(rsi=55, r=0.5) for _ in range(60)]
    props = wp.propose(bad + good, "r")
    assert all(p.bucket != "rsi_oversold(<30)" for p in props)

def test_propose_skips_exit_status_factor():
    rows = [_make_row(st="sl_hit", r=-1.0) for _ in range(40)]
    rows += [_make_row(st="tp_hit", r=2.0) for _ in range(40)]
    props = wp.propose(rows, "r")
    assert all(p.factor != "exit_status" for p in props)

def test_propose_sort_kills_first():
    # construct a kill + a boost
    kills = [_make_row(rsi=20, r=-0.8) for _ in range(40)]
    boosts = [_make_row(score=0.95, r=1.5) for _ in range(40)]
    rest  = [_make_row(rsi=55, r=0.05) for _ in range(80)]
    props = wp.propose(kills + boosts + rest, "r")
    if any(p.action == "kill" for p in props):
        kill_idx = next(i for i, p in enumerate(props) if p.action == "kill")
        boost_idx = next((i for i, p in enumerate(props) if p.action == "boost"), 99)
        assert kill_idx < boost_idx


# ───────────────── persistence ─────────────────

def test_write_proposals_appends(isolated_proposals):
    p1 = wp.Proposal("t","r","f","b1",30,0.5,0.4,0.4,"boost",5.0,0.55,"x")
    p2 = wp.Proposal("t","r","f","b2",30,0.3,-0.4,-0.4,"penalize",-5.0,0.55,"y")
    n = wp.write_proposals([p1, p2])
    assert n == 2
    lines = isolated_proposals.read_text().strip().splitlines()
    assert len(lines) == 2
    rec = json.loads(lines[0])
    assert rec["bucket"] == "b1"
    assert rec["applied"] is False

def test_write_empty_does_nothing(isolated_proposals):
    assert wp.write_proposals([]) == 0
    assert not isolated_proposals.exists()

def test_read_proposals_unapplied_filter(isolated_proposals):
    isolated_proposals.parent.mkdir(parents=True, exist_ok=True)
    isolated_proposals.write_text(
        json.dumps({"bucket":"a","applied":True}) + "\n" +
        json.dumps({"bucket":"b","applied":False}) + "\n"
    )
    all_ = wp.read_proposals()
    assert len(all_) == 2
    unapplied = wp.read_proposals(only_unapplied=True)
    assert len(unapplied) == 1
    assert unapplied[0]["bucket"] == "b"

def test_read_proposals_limit(isolated_proposals):
    isolated_proposals.parent.mkdir(parents=True, exist_ok=True)
    isolated_proposals.write_text(
        "\n".join(json.dumps({"bucket":f"b{i}","applied":False}) for i in range(10)) + "\n"
    )
    rows = wp.read_proposals(limit=3)
    assert len(rows) == 3
    assert rows[-1]["bucket"] == "b9"

def test_read_proposals_missing_file_returns_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(wp, "PROPOSALS", tmp_path / "nope.jsonl")
    assert wp.read_proposals() == []


# ───────────────── CLI ─────────────────

def test_cli_propose_dry_run(tmp_path, isolated_proposals, monkeypatch, capsys):
    run = tmp_path / "results" / "test_run"
    rows = [_make_row(rsi=20, r=-0.8) for _ in range(40)]
    rows += [_make_row(score=0.95, r=1.5) for _ in range(40)]
    rows += [_make_row(rsi=55, r=0.05) for _ in range(80)]
    _write_picks(run, rows)
    monkeypatch.setattr(cal, "RESULTS_ROOT", run.parent)

    rc = wp.main(["propose", "--run", run.name, "--dry-run"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "PROPOSALS" in out
    assert "DRY-RUN" in out
    assert not isolated_proposals.exists()  # nothing persisted

def test_cli_propose_persists(tmp_path, isolated_proposals, monkeypatch, capsys):
    run = tmp_path / "results" / "tr"
    rows = [_make_row(rsi=20, r=-0.8) for _ in range(40)]
    rows += [_make_row(rsi=55, r=0.4) for _ in range(60)]
    _write_picks(run, rows)
    monkeypatch.setattr(cal, "RESULTS_ROOT", run.parent)

    rc = wp.main(["propose", "--run", run.name])
    assert rc == 0
    assert isolated_proposals.exists()
    assert isolated_proposals.read_text().strip() != ""

def test_cli_history_empty(isolated_proposals, capsys):
    rc = wp.main(["history"])
    assert rc == 0
    assert "no proposals yet" in capsys.readouterr().out

def test_cli_review_caught_up(isolated_proposals, capsys):
    rc = wp.main(["review"])
    assert rc == 0
    assert "caught up" in capsys.readouterr().out
