"""T49 / Pillar 3 Layer 6: pattern_layer (probability engine hook + auto-enable)."""
import json
import pandas as pd
import pytest
from pathlib import Path

from src import pattern_layer as pl
from src import pattern_stats as ps
from src import learning_journal as lj


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    out = tmp_path / "stats.json"
    monkeypatch.setattr(ps, "STATS", out)
    monkeypatch.setattr(lj, "JOURNAL", tmp_path / "learning_journal.jsonl")
    return out


def _breakout_df():
    closes = [10]*20 + [12]
    return pd.DataFrame({
        "Open":closes,"High":closes,"Low":closes,"Close":closes,
        "Volume":[1000]*21})


def test_pattern_multiplier_neutral_when_no_stats(isolated):
    mult, matches = pl.pattern_multiplier("X", regime="bull",
                                           df=_breakout_df())
    assert mult == 1.0


def test_pattern_multiplier_boosts_on_positive_edge(isolated):
    ps.save({"breakout_20": {"bull": {"n": 30, "wins": 22, "win_rate": 0.73, "mean_r": 0.8}}})
    mult, q = pl.pattern_multiplier("X", regime="bull", df=_breakout_df())
    assert mult > 1.0
    assert mult <= 1.0 + pl.MAX_BOOST + 1e-6
    assert any(m["pattern"] == "breakout_20" for m in q)


def test_pattern_multiplier_penalizes_on_negative_edge(isolated):
    ps.save({"breakout_20": {"bull": {"n": 30, "wins": 5, "win_rate": 0.17, "mean_r": -0.6}}})
    mult, q = pl.pattern_multiplier("X", regime="bull", df=_breakout_df())
    assert mult < 1.0
    assert mult >= 1.0 - pl.MAX_BOOST - 1e-6


def test_pattern_multiplier_ignores_low_sample(isolated):
    ps.save({"breakout_20": {"bull": {"n": 5, "wins": 5, "win_rate": 1.0, "mean_r": 2.0}}})
    mult, _ = pl.pattern_multiplier("X", regime="bull", df=_breakout_df())
    assert mult == 1.0


def test_disable_then_enable_pattern(isolated):
    pl.disable_pattern("breakout_20")
    s = ps.load()
    assert s["_disabled"]["breakout_20"] is True
    pl.enable_pattern("breakout_20")
    s = ps.load()
    assert "breakout_20" not in s.get("_disabled", {})


def test_disabled_pattern_yields_neutral_multiplier(isolated):
    ps.save({"breakout_20": {"bull": {"n": 30, "wins": 22, "win_rate": 0.73, "mean_r": 0.8}}})
    pl.disable_pattern("breakout_20")
    mult, _ = pl.pattern_multiplier("X", regime="bull", df=_breakout_df())
    assert mult == 1.0


def test_auto_enable_disable_kills_negative_edge(isolated):
    ps.save({
        "bad_pattern":  {"bull": {"n": 40, "wins": 5, "win_rate": 0.13, "mean_r": -0.5}},
        "good_pattern": {"bull": {"n": 40, "wins": 30, "win_rate": 0.75, "mean_r": 0.6}},
    })
    res = pl.auto_enable_disable()
    assert "bad_pattern" in res["disabled"]
    assert "good_pattern" not in res["disabled"]


def test_auto_enable_disable_reactivates_on_recovery(isolated):
    # Pre-disable a pattern, then update its stats to be good, run auto-loop
    ps.save({
        "recovered": {"bull": {"n": 40, "wins": 30, "win_rate": 0.75, "mean_r": 0.6}},
        "_disabled": {"recovered": True},
    })
    res = pl.auto_enable_disable()
    assert "recovered" in res["reactivated"]


def test_auto_enable_disable_respects_min_n(isolated):
    ps.save({
        "small_sample": {"bull": {"n": 10, "wins": 1, "win_rate": 0.1, "mean_r": -0.9}},
    })
    res = pl.auto_enable_disable(min_n=30)
    assert res["disabled"] == []
