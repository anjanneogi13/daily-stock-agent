"""Tests for wisdom_consultant + kill_list integration boundaries.

These exercise the contract the main.py filter relies on:
  - is_killed() returns truthy for cooled tickers
  - consult_before_pick sets wisdom_kill=True path
"""
import pytest
from src import wisdom_base
from src.wisdom_consultant import consult_before_pick


@pytest.fixture(autouse=True)
def _isolate(tmp_path, monkeypatch):
    monkeypatch.setattr(wisdom_base, "KILL", tmp_path / "kill.json")
    monkeypatch.setattr(wisdom_base, "PATTERNS", tmp_path / "patterns.jsonl")
    yield


def test_killed_ticker_yields_kill_in_consult():
    wisdom_base.add_to_kill_list("KILLER", reason="3 consecutive losses",
                                  cool_off_days=14, source="auto_cooldown")
    out = consult_before_pick("KILLER", signals={})
    assert out["kill"] is not None
    assert "KILL LIST" in out["warnings"][0]
    # score_adj stays 0 — kill is informational, drop happens upstream
    assert out["score_adj"] == 0.0


def test_clean_ticker_no_kill():
    out = consult_before_pick("CLEAN", signals={})
    assert out["kill"] is None
    assert out["warnings"] == []


def test_score_adj_capped():
    """Even with many drag patterns, score_adj never exceeds ±0.05."""
    # Add 10 drag patterns matching 'regime=bear'
    for _ in range(10):
        wisdom_base.add_pattern(signal="regime", bucket="bear",
                                 effect="drag", win_rate=0.2, sample_n=15,
                                 p_value=0.04)
    out = consult_before_pick("XYZ", signals={"regime": "bear"})
    assert out["score_adj"] >= -0.05
    assert out["score_adj"] <= 0.05
