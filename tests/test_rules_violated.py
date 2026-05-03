"""B6: rules violated on losers (weekly post-mortem)."""
from __future__ import annotations
import pytest

from src import wisdom_base as wb
from src import weekly_review as wr


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    p = tmp_path / "lessons.jsonl"
    monkeypatch.setattr(wb, "LESSONS", p)
    wb.add_lesson("Never average down.", source="book:liv",
                  confidence=0.95, triggers=["drawdown_pct>3"])
    return p


def test_rules_violated_on_losers_fires(isolated):
    losers = [
        {"ticker":"X","r_multiple":-1.0,"actual_return_pct":-5.0,
         "regime":"bull","trade_type":"swing"},
        {"ticker":"Y","r_multiple":-1.0,"actual_return_pct":-1.0,  # <3% — won't fire
         "regime":"bull","trade_type":"swing"},
    ]
    out = wr.rules_violated_on_losers(losers)
    assert len(out) == 1
    assert "X" in out[0]
    assert "average down" in out[0]


def test_rules_violated_skips_winners(isolated):
    out = wr.rules_violated_on_losers([
        {"ticker":"W","r_multiple":2.0,"actual_return_pct":4.0},
    ])
    assert out == []


def test_rules_violated_handles_empty(isolated):
    assert wr.rules_violated_on_losers([]) == []
    assert wr.rules_violated_on_losers(None) == []


def test_rules_violated_handles_bad_data(isolated):
    out = wr.rules_violated_on_losers([
        {"ticker":"BAD","r_multiple":"NaN"},
    ])
    assert out == []
