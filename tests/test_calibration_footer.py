"""Tests for T40: calibration Telegram footer."""
from __future__ import annotations
import csv
import json
from pathlib import Path

import pytest

from src import calibration as cal
from src import weight_proposer as wp


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


def _row(score=0.8, rsi=50, atr=2.0, entry=100, r=0.4,
         tt="swing", ret=2.0, pd_="2025-01-15", st="max_hold"):
    return {
        "ticker":"X","trade_type":tt,"score":score,"rsi":rsi,"atr":atr,
        "entry":entry,"stop_loss":entry*0.98,"take_profit":entry*1.04,
        "exit_status":st,"exit_price":entry*(1+ret/100),"days_held":5,
        "r_multiple":r,"return_pct":ret,"pick_date":pd_,"exit_date":pd_,
    }


# ───────────────── telegram_footer_lines ─────────────────

def test_footer_no_runs(tmp_path, monkeypatch):
    monkeypatch.setattr(cal, "RESULTS_ROOT", tmp_path / "empty")
    assert cal.telegram_footer_lines() == []

def test_footer_renders_overall_line(tmp_path, monkeypatch):
    run = tmp_path / "results" / "rA"
    rows = [_row(r=0.5) for _ in range(50)]
    _write_picks(run, rows)
    monkeypatch.setattr(cal, "RESULTS_ROOT", run.parent)
    out = cal.telegram_footer_lines(min_n=10)
    assert any("Last run" in line for line in out)
    assert any("rA" in line for line in out)

def test_footer_surfaces_best_and_worst(tmp_path, monkeypatch):
    run = tmp_path / "results" / "rB"
    # huge negative bucket + huge positive bucket
    bad  = [_row(rsi=20, r=-0.8) for _ in range(40)]
    good = [_row(score=0.95, r=1.5) for _ in range(40)]
    avg  = [_row(rsi=55, r=0.05) for _ in range(80)]
    _write_picks(run, bad + good + avg)
    monkeypatch.setattr(cal, "RESULTS_ROOT", run.parent)
    out = cal.telegram_footer_lines(min_n=20)
    joined = "\n".join(out)
    assert "🟢" in joined or "Best edge" in joined
    assert "🔴" in joined or "Worst drag" in joined

def test_footer_silent_when_no_strong_edge(tmp_path, monkeypatch):
    run = tmp_path / "results" / "rC"
    rows = [_row(r=0.05) for _ in range(50)]
    _write_picks(run, rows)
    monkeypatch.setattr(cal, "RESULTS_ROOT", run.parent)
    out = cal.telegram_footer_lines(min_n=10)
    # only the headline "Last run" line — no edge/drag callouts
    assert all("Best edge" not in l and "Worst drag" not in l for l in out)

def test_footer_handles_missing_csv(tmp_path, monkeypatch):
    run = tmp_path / "results" / "rD"
    run.mkdir(parents=True)
    monkeypatch.setattr(cal, "RESULTS_ROOT", run.parent)
    # no picks.csv — should degrade silently
    assert cal.telegram_footer_lines() == []


# ───────────────── open_proposals_summary ─────────────────

def test_proposals_summary_none_when_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(wp, "PROPOSALS", tmp_path / "p.jsonl")
    assert cal.open_proposals_summary() is None

def test_proposals_summary_counts_actions(tmp_path, monkeypatch):
    f = tmp_path / "p.jsonl"
    f.write_text(
        json.dumps({"action":"kill","applied":False}) + "\n" +
        json.dumps({"action":"boost","applied":False}) + "\n" +
        json.dumps({"action":"boost","applied":False}) + "\n" +
        json.dumps({"action":"penalize","applied":False}) + "\n" +
        json.dumps({"action":"boost","applied":True}) + "\n"  # excluded
    )
    monkeypatch.setattr(wp, "PROPOSALS", f)
    line = cal.open_proposals_summary()
    assert line is not None
    assert "4 weight proposals open" in line
    assert "1 kill" in line
    assert "2 boost" in line
    assert "1 penalize" in line

def test_proposals_summary_handles_missing_file(tmp_path, monkeypatch):
    monkeypatch.setattr(wp, "PROPOSALS", tmp_path / "ghost.jsonl")
    assert cal.open_proposals_summary() is None


# ───────────────── integration with weekly_review ─────────────────

def test_weekly_review_includes_calibration_section(tmp_path, monkeypatch):
    """When calibration data exists, the weekly footer block appears."""
    run = tmp_path / "results" / "rE"
    rows = [_row(r=0.5) for _ in range(50)]
    _write_picks(run, rows)
    monkeypatch.setattr(cal, "RESULTS_ROOT", run.parent)

    from src.weekly_review import build_report, format_telegram
    text = format_telegram(build_report())
    assert "Calibration brain" in text
    assert "Last run" in text

def test_weekly_review_safe_when_calibration_broken(monkeypatch):
    """If calibration helpers raise, weekly still renders."""
    import src.weekly_review as wr

    def boom(*a, **k): raise RuntimeError("simulated")
    monkeypatch.setattr(cal, "telegram_footer_lines", boom)
    monkeypatch.setattr(cal, "open_proposals_summary", boom)

    from src.weekly_review import build_report, format_telegram
    text = format_telegram(build_report())
    # weekly should still produce its standard sections
    assert "Weekly Self-Assessment" in text
    assert "Recommended action" in text
