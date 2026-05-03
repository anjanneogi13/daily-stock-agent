"""Pillar 3 Phase 1: per-pattern × per-regime stats."""
import csv
import json
import pytest
from pathlib import Path

from src import pattern_stats as ps


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    pat = tmp_path / "patterns.jsonl"
    pks = tmp_path / "picks.csv"
    out = tmp_path / "stats.json"
    monkeypatch.setattr(ps, "PATTERNS_LOG", pat)
    monkeypatch.setattr(ps, "PICKS_LOG",    pks)
    monkeypatch.setattr(ps, "STATS",        out)
    return pat, pks, out


def _seed_picks(p, rows):
    with p.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["ticker","pick_date","r_multiple"])
        w.writeheader()
        for r in rows: w.writerow(r)


def _seed_patterns(p, recs):
    with p.open("w") as f:
        for r in recs:
            f.write(json.dumps(r) + "\n")


def test_build_stats_empty(isolated):
    assert ps.build_stats() == {}


def test_build_stats_aggregates_by_pattern_and_regime(isolated):
    pat, pks, _ = isolated
    _seed_patterns(pat, [
        {"ticker":"A","date":"2026-05-03","pattern":"breakout_20","regime":"bull"},
        {"ticker":"B","date":"2026-05-03","pattern":"breakout_20","regime":"bull"},
        {"ticker":"C","date":"2026-05-03","pattern":"breakout_20","regime":"chop"},
    ])
    _seed_picks(pks, [
        {"ticker":"A","pick_date":"2026-05-03","r_multiple":"2.0"},
        {"ticker":"B","pick_date":"2026-05-03","r_multiple":"-1.0"},
        {"ticker":"C","pick_date":"2026-05-03","r_multiple":"0.5"},
    ])
    stats = ps.build_stats()
    assert "breakout_20" in stats
    bull = stats["breakout_20"]["bull"]
    assert bull["n"] == 2
    assert bull["wins"] == 1
    assert bull["win_rate"] == 0.5
    chop = stats["breakout_20"]["chop"]
    assert chop["n"] == 1
    assert chop["wins"] == 1


def test_build_stats_skips_patterns_with_no_pick(isolated):
    pat, pks, _ = isolated
    _seed_patterns(pat, [
        {"ticker":"NOTRADED","date":"2026-05-03","pattern":"breakout_20","regime":"bull"},
    ])
    _seed_picks(pks, [])
    assert ps.build_stats() == {}


def test_save_and_load_roundtrip(isolated):
    _, _, out = isolated
    stats = {"x": {"bull": {"n": 5, "wins": 3, "win_rate": 0.6}}}
    ps.save(stats)
    assert out.exists()
    loaded = ps.load()
    assert loaded == stats


def test_load_returns_empty_when_missing(isolated):
    assert ps.load() == {}


def test_build_stats_handles_missing_regime(isolated):
    pat, pks, _ = isolated
    _seed_patterns(pat, [
        {"ticker":"A","date":"2026-05-03","pattern":"x"},  # no regime
    ])
    _seed_picks(pks, [
        {"ticker":"A","pick_date":"2026-05-03","r_multiple":"1.0"},
    ])
    stats = ps.build_stats()
    assert "unknown" in stats["x"]
