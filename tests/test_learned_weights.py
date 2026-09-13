"""Tests for src/learned_weights.py — the learning-loop consumer.

This module is what makes nightly learning actually change picks; before
it existed, config/weights.json was written but never read (Sep 2026 fix).
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

from src import learned_weights as lw


@pytest.fixture
def weights_file(tmp_path, monkeypatch):
    """Point both weight paths at tmp and reset the mtime cache."""
    runtime = tmp_path / "weights_runtime.json"
    config = tmp_path / "weights.json"
    monkeypatch.setattr(lw, "RUNTIME_WEIGHTS", runtime)
    monkeypatch.setattr(lw, "CONFIG_WEIGHTS", config)
    monkeypatch.setattr(lw, "_cache", {"key": None, "factors": None})

    def write(factors, target="runtime"):
        path = runtime if target == "runtime" else config
        path.write_text(json.dumps({"factors": factors}))
        return path

    return write


SIG = {"rsi_14": 55.0, "atr_14": 2.0, "close": 100.0}  # rsi_50-70, atrpct_1.5-3


def test_neutral_when_no_files(tmp_path, monkeypatch):
    monkeypatch.setattr(lw, "RUNTIME_WEIGHTS", tmp_path / "missing1.json")
    monkeypatch.setattr(lw, "CONFIG_WEIGHTS", tmp_path / "missing2.json")
    monkeypatch.setattr(lw, "_cache", {"key": None, "factors": None})
    assert lw.learned_multiplier(SIG, 0.75) == (1.0, {})


def test_neutral_on_corrupt_json(weights_file, tmp_path, monkeypatch):
    (tmp_path / "weights_runtime.json").write_text("{not json")
    assert lw.learned_multiplier(SIG, 0.75) == (1.0, {})


def test_applies_matching_buckets(weights_file):
    weights_file({
        "rsi": {"rsi_50-70": 1.05},
        "score": {"score_0.7-0.85": 1.06},
        "atrpct": {"atrpct_1.5-3": 0.98},
    })
    total, applied = lw.learned_multiplier(SIG, 0.75)
    assert total == round(1.05 * 1.06 * 0.98, 4)
    assert applied == {
        "rsi=rsi_50-70": 1.05,
        "score=score_0.7-0.85": 1.06,
        "atrpct=atrpct_1.5-3": 0.98,
    }


def test_total_clamped_to_ceiling(weights_file):
    weights_file({
        "rsi": {"rsi_50-70": 1.5},
        "score": {"score_0.7-0.85": 1.5},
    })
    total, _ = lw.learned_multiplier(SIG, 0.75)
    assert total == lw.MULT_CEIL


def test_killed_bucket_floors_not_zeroes(weights_file):
    """A 0.0 (killed) bucket must dampen to the floor, never zero a pick."""
    weights_file({"rsi": {"rsi_50-70": 0.0}})
    total, applied = lw.learned_multiplier(SIG, 0.75)
    assert total == lw.MULT_FLOOR
    assert applied["rsi=rsi_50-70"] == 0.0


def test_na_buckets_skipped(weights_file):
    weights_file({"rsi": {"rsi_na": 0.5}, "atrpct": {"atrpct_na": 0.5}})
    total, applied = lw.learned_multiplier({"rsi_14": None, "atr_14": None, "close": None}, 0.75)
    assert total == 1.0
    assert applied == {}


def test_falls_back_to_config_weights(weights_file):
    weights_file({"rsi": {"rsi_50-70": 1.1}}, target="config")
    total, applied = lw.learned_multiplier(SIG, 0.75)
    assert applied == {"rsi=rsi_50-70": 1.1}
    assert total == 1.1


def test_runtime_preferred_over_config(weights_file):
    weights_file({"rsi": {"rsi_50-70": 1.10}}, target="runtime")
    weights_file({"rsi": {"rsi_50-70": 0.90}}, target="config")
    total, _ = lw.learned_multiplier(SIG, 0.75)
    assert total == 1.1


def test_string_signal_values_coerced(weights_file):
    weights_file({"rsi": {"rsi_50-70": 1.05}})
    total, _ = lw.learned_multiplier({"rsi_14": "55", "atr_14": "", "close": "100"}, 0.75)
    assert total == 1.05
