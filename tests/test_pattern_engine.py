"""Pillar 3 Phase 1: orchestrator + persistence."""
import json
import pandas as pd
import pytest
from pathlib import Path

from src import pattern_engine as pe


def _df_breakout():
    closes = [10]*20 + [12]
    return pd.DataFrame({
        "Open": closes, "High": closes, "Low": closes,
        "Close": closes, "Volume": [1000]*21,
    })


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    p = tmp_path / "patterns.jsonl"
    monkeypatch.setattr(pe, "PATTERNS_LOG", p)
    return p


def test_scan_ticker_returns_matches(isolated):
    matches = pe.scan_ticker("TEST", df=_df_breakout(), regime="bull")
    pats = {m["pattern"] for m in matches}
    assert "breakout_20" in pats
    for m in matches:
        assert m["ticker"] == "TEST"
        assert m["regime"] == "bull"
        assert "date" in m
        assert "direction" in m


def test_scan_ticker_handles_empty_df(isolated):
    df = pd.DataFrame()
    assert pe.scan_ticker("X", df=df) == []


def test_scan_ticker_handles_none_df(isolated, monkeypatch):
    monkeypatch.setattr("src.data_fetcher.fetch_ohlcv",
                        lambda *a, **k: None)
    assert pe.scan_ticker("X") == []


def test_persist_appends(isolated):
    pe.persist([{"pattern":"x","ticker":"T","date":"2026-05-03","confidence":0.7}])
    pe.persist([{"pattern":"y","ticker":"T","date":"2026-05-03","confidence":0.6}])
    lines = isolated.read_text().splitlines()
    assert len(lines) == 2


def test_persist_empty_no_write(isolated):
    pe.persist([])
    assert not isolated.exists()


def test_load_recent_filters_by_days(isolated):
    from datetime import date, timedelta
    today = date.today().isoformat()
    old   = (date.today() - timedelta(days=60)).isoformat()
    isolated.write_text(
        json.dumps({"date":today, "pattern":"a"}) + "\n" +
        json.dumps({"date":old,   "pattern":"b"}) + "\n"
    )
    recent = pe.load_recent(days=30)
    assert len(recent) == 1
    assert recent[0]["pattern"] == "a"
