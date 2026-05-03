"""Tests for scripts/backfill_signal_journal.py."""
from __future__ import annotations
import csv
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src import signal_journal as sj
import importlib.util

spec = importlib.util.spec_from_file_location(
    "backfill", Path(__file__).parent.parent / "scripts" / "backfill_signal_journal.py")
backfill = importlib.util.module_from_spec(spec)
spec.loader.exec_module(backfill)


def _write_csv(p: Path, rows: list[dict]) -> None:
    cols = list(rows[0].keys())
    with p.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow(r)


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    csv_p = tmp_path / "picks_log.csv"
    jrn   = tmp_path / "signal_journal.jsonl"
    monkeypatch.setattr(backfill, "PICKS_LOG", csv_p)
    monkeypatch.setattr(sj, "JOURNAL", jrn)
    return csv_p, jrn


def _make_row(ticker="X", date="2026-04-28", status="sl_hit",
              r=-1.0, ret=-2.0, score=0.85):
    return {
        "pick_date": date, "ticker": ticker, "tag": "SEMI",
        "trade_type": "swing", "score": str(score),
        "days_to_earnings": "5", "evaluation_status": status,
        "evaluated_on": date, "r_multiple": str(r),
        "actual_return_pct": str(ret),
    }


def test_outcome_status_mapping():
    assert backfill._outcome_status("sl_hit")  == "loss"
    assert backfill._outcome_status("tp_hit")  == "win"
    assert backfill._outcome_status("max_hold")== "neutral"
    assert backfill._outcome_status("")        == "neutral"


def test_backfill_writes_records(isolated):
    csv_p, jrn = isolated
    _write_csv(csv_p, [
        _make_row("AAA", status="tp_hit", r=2.0, ret=4.0),
        _make_row("BBB", status="sl_hit", r=-1.0, ret=-2.0),
    ])
    rc = backfill.main([])
    assert rc == 0
    assert jrn.exists()
    lines = jrn.read_text().strip().splitlines()
    assert len(lines) == 2
    rec = json.loads(lines[0])
    assert rec["ticker"] == "AAA"
    assert rec["outcome"] == "win"
    assert rec["r_multiple"] == 2.0


def test_backfill_skips_open_picks(isolated):
    csv_p, jrn = isolated
    _write_csv(csv_p, [
        _make_row("OPEN", status="", r=0, ret=0),
        _make_row("CLOSED", status="tp_hit", r=2.0, ret=4.0),
    ])
    backfill.main([])
    lines = jrn.read_text().strip().splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["ticker"] == "CLOSED"


def test_backfill_idempotent(isolated):
    csv_p, jrn = isolated
    _write_csv(csv_p, [_make_row("AAA", status="tp_hit", r=2.0, ret=4.0)])
    backfill.main([])
    backfill.main([])  # second run
    lines = jrn.read_text().strip().splitlines()
    assert len(lines) == 1  # not duplicated


def test_backfill_dry_run_no_write(isolated, capsys):
    csv_p, jrn = isolated
    _write_csv(csv_p, [_make_row("AAA", status="tp_hit", r=2.0, ret=4.0)])
    rc = backfill.main(["--dry-run"])
    assert rc == 0
    assert not jrn.exists()
    assert "DRY-RUN" in capsys.readouterr().out


def test_backfill_handles_missing_csv(isolated, capsys):
    csv_p, jrn = isolated
    rc = backfill.main([])
    assert rc == 1


def test_backfill_handles_no_closed_picks(isolated, capsys):
    csv_p, jrn = isolated
    _write_csv(csv_p, [_make_row("OPEN", status="")])
    rc = backfill.main([])
    assert rc == 0
    assert "nothing to do" in capsys.readouterr().out


def test_backfill_handles_bad_numerics(isolated):
    csv_p, jrn = isolated
    row = _make_row("X", status="tp_hit")
    row["r_multiple"] = "not-a-number"
    row["actual_return_pct"] = ""
    _write_csv(csv_p, [row])
    backfill.main([])
    rec = json.loads(jrn.read_text().strip())
    assert rec["r_multiple"] is None
    assert rec["actual_return_pct"] is None
