"""T44 / Pillar 4: weight_applier."""
from __future__ import annotations
import json
from pathlib import Path

import pytest

from src import weight_applier as wa
from src import weight_proposer as wp


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    weights = tmp_path / "weights.json"
    history = tmp_path / "weight_history.jsonl"
    proposals = tmp_path / "proposals.jsonl"
    monkeypatch.setattr(wa, "WEIGHTS", weights)
    monkeypatch.setattr(wa, "HISTORY", history)
    monkeypatch.setattr(wa, "PROPOSALS", proposals)
    monkeypatch.setattr(wp, "PROPOSALS", proposals)
    return weights, history, proposals


def _make_proposal(factor="rsi", bucket="oversold", action="penalize",
                   delta=3.0, ts="2026-05-03T10:00:00") -> dict:
    return {"ts": ts, "run_id":"r","factor":factor,"bucket":bucket,
            "n":50,"win_rate":0.4,"mean_r":-0.3,"bias_r":-0.3,
            "action":action,"delta_pct":delta,"confidence":0.7,
            "rationale":"test","applied":False}


def _seed_proposals(path, recs):
    with path.open("w") as f:
        for r in recs:
            f.write(json.dumps(r) + "\n")


# ── core apply ──
def test_apply_penalize_decreases_multiplier(isolated):
    weights, history, proposals = isolated
    _seed_proposals(proposals, [_make_proposal(action="penalize", delta=4)])
    res = wa.apply_proposals()
    assert res["applied"] == 1
    w = json.loads(weights.read_text())
    assert w["factors"]["rsi"]["oversold"] == pytest.approx(0.96, rel=1e-2)


def test_apply_boost_increases_multiplier(isolated):
    weights, history, proposals = isolated
    _seed_proposals(proposals, [_make_proposal(action="boost", delta=4)])
    wa.apply_proposals()
    w = json.loads(weights.read_text())
    assert w["factors"]["rsi"]["oversold"] == pytest.approx(1.04, rel=1e-2)


def test_apply_kill_zeroes(isolated):
    weights, history, proposals = isolated
    _seed_proposals(proposals, [_make_proposal(action="kill", delta=0)])
    wa.apply_proposals()
    w = json.loads(weights.read_text())
    assert w["factors"]["rsi"]["oversold"] == 0.0


# ── 5%/wk cap ──
def test_weekly_cap_blocks_overflow(isolated):
    weights, history, proposals = isolated
    _seed_proposals(proposals, [
        _make_proposal(action="penalize", delta=3, ts="2026-05-03T10:00:00"),
        _make_proposal(action="penalize", delta=3, ts="2026-05-03T11:00:00"),
        _make_proposal(action="penalize", delta=3, ts="2026-05-03T12:00:00"),
    ])
    res = wa.apply_proposals()
    # First two together = 6% > 5% cap → 2nd should be capped
    assert res["applied"] == 1
    assert res["skipped_capped"] == 2


def test_cap_resets_next_week(isolated):
    weights, history, proposals = isolated
    _seed_proposals(proposals, [
        _make_proposal(action="penalize", delta=4, ts="2026-04-27T10:00:00"),  # W17
        _make_proposal(action="penalize", delta=4, ts="2026-05-04T10:00:00"),  # W18
    ])
    res = wa.apply_proposals()
    assert res["applied"] == 2  # different ISO weeks


# ── idempotency ──
def test_apply_marks_proposals_and_skips_replays(isolated):
    weights, history, proposals = isolated
    _seed_proposals(proposals, [_make_proposal()])
    wa.apply_proposals()
    res2 = wa.apply_proposals()
    assert res2["applied"] == 0  # already applied


# ── dry-run ──
def test_dry_run_does_not_persist(isolated):
    weights, history, proposals = isolated
    _seed_proposals(proposals, [_make_proposal()])
    res = wa.apply_proposals(dry_run=True)
    assert res["applied"] == 1
    assert not weights.exists()
    assert not history.exists()


# ── history & summary ──
def test_history_records_each_mutation(isolated):
    weights, history, proposals = isolated
    _seed_proposals(proposals, [_make_proposal()])
    wa.apply_proposals()
    lines = history.read_text().strip().splitlines()
    assert len(lines) == 1
    rec = json.loads(lines[0])
    assert rec["factor"] == "rsi"
    assert rec["action"] == "penalize"
    assert "old" in rec and "new" in rec


def test_history_summary_counts_recent(isolated):
    weights, history, proposals = isolated
    _seed_proposals(proposals, [
        _make_proposal(action="boost", delta=2, ts="2026-05-03T10:00:00"),
        _make_proposal(action="kill", delta=0, ts="2026-05-03T11:00:00",
                       factor="atrpct", bucket="high"),
    ])
    wa.apply_proposals()
    s = wa.history_summary(days=30)
    assert s["total"] == 2
    assert s["by_action"]["boost"] == 1
    assert s["by_action"]["kill"] == 1


# ── skip invalid ──
def test_skip_invalid_proposals(isolated):
    weights, history, proposals = isolated
    _seed_proposals(proposals, [
        {"ts":"x","run_id":"r","factor":"","bucket":"","action":"unknown",
         "delta_pct":0,"applied":False},
    ])
    res = wa.apply_proposals()
    assert res["applied"] == 0
    assert res["skipped_invalid"] == 1
