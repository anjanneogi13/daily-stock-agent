"""
Regression tests for the 2026-10-29 full-repo audit (wave 2).

Each test pins one root cause that kept the agent from learning or from
picking well:

  * the pytest suite itself wrote live data files (scripts ran on import)
  * auto_cooldown re-wrote the same lesson every evaluator run (2,542 copies)
  * lesson GC aged out the seed (book:/backtester) lessons and never
    reported what it removed
  * archived/fixture proposals were still eligible for weight application
  * weight proposals were generated for factors nothing applies at pick time
  * pick-time factor inputs (rsi/atr/adx/ext50/sector) were never logged, so
    calibration could only learn on `score`
  * the pattern engine indexed Title-case columns on a lowercase frame → 0
    matches on every nightly scan since it shipped
  * pattern matches were never persisted with the pick date, so pattern
    stats could never join an outcome
  * no evidence-based quality gate existed between "scored" and "official"
  * sector_bonus defaults silently re-enabled a disabled +30% multiplier
  * brain state (wisdom, patterns) was gitignored and evaporated after CI
"""
from __future__ import annotations

import csv
import importlib
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

REPO = Path(__file__).resolve().parent.parent


# ──────────────────────────────────────────────────────────────────────
# 1. Importing flat scripts must not write live artifacts
# ──────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("module", ["scripts.weekend_reflection", "scripts.monthly_xray"])
def test_report_scripts_do_nothing_on_import(module, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    sys.modules.pop(module, None)
    mod = importlib.import_module(module)
    assert callable(getattr(mod, "main", None)), f"{module} must expose main()"
    assert not (tmp_path / "data").exists(), (
        f"importing {module} wrote files under cwd/data — the suite was "
        "polluting the live learning directory"
    )


# ──────────────────────────────────────────────────────────────────────
# 2. Wisdom base: idempotent automated lessons + GC behaviour
# ──────────────────────────────────────────────────────────────────────
@pytest.fixture
def wisdom_tmp(tmp_path, monkeypatch):
    from src import wisdom_base, lesson_gc
    lessons = tmp_path / "lessons.jsonl"
    monkeypatch.setattr(wisdom_base, "LESSONS", lessons)
    monkeypatch.setattr(wisdom_base, "KILL", tmp_path / "kill_list.json")
    monkeypatch.setattr(wisdom_base, "PATTERNS", tmp_path / "patterns.jsonl")
    monkeypatch.setattr(lesson_gc, "LESSONS", lessons)
    return lessons


def _lesson(text, days_ago=0, source="manual", conf=0.7, tags=None, active=True):
    ts = (datetime.now() - timedelta(days=days_ago)).isoformat(timespec="seconds")
    return {"ts": ts, "text": text, "source": source, "confidence": conf,
            "tags": tags or [], "author": "test", "active": active}


def _write_jsonl(path, rows):
    with path.open("w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


def test_has_recent_lesson_matches_source_tag_window(wisdom_tmp):
    from src import wisdom_base
    _write_jsonl(wisdom_tmp, [
        _lesson("ABC cooled", days_ago=2, source="auto_cooldown", tags=["cooldown", "ABC"]),
        _lesson("old XYZ", days_ago=40, source="auto_cooldown", tags=["cooldown", "XYZ"]),
        _lesson("inactive", days_ago=1, source="auto_cooldown", tags=["cooldown", "DEF"], active=False),
    ])
    assert wisdom_base.has_recent_lesson("auto_cooldown", "abc", within_days=10)
    assert not wisdom_base.has_recent_lesson("auto_cooldown", "XYZ", within_days=10)
    assert not wisdom_base.has_recent_lesson("auto_cooldown", "DEF", within_days=10)
    assert not wisdom_base.has_recent_lesson("manual", "ABC", within_days=10)


def test_auto_cooldown_writes_one_lesson_per_window(wisdom_tmp, monkeypatch):
    from src import auto_cooldown, wisdom_base
    monkeypatch.setattr(auto_cooldown, "find_candidates", lambda threshold=3: [("ABC", 3)])
    auto_cooldown.scan_and_cool(apply=True, cool_off_days=14)
    # Second evaluator run on the same day: ticker already cooled → no new lesson
    auto_cooldown.scan_and_cool(apply=True, cool_off_days=14)
    # Simulate the cooldown expiring but the lesson still being fresh
    kill = json.loads((wisdom_tmp.parent / "kill_list.json").read_text())
    for k in kill if isinstance(kill, list) else kill.get("entries", []):
        k["until"] = (datetime.now() - timedelta(days=1)).date().isoformat()
        k["expires"] = k["until"]
    (wisdom_tmp.parent / "kill_list.json").write_text(json.dumps(kill))
    auto_cooldown.scan_and_cool(apply=True, cool_off_days=14)
    rows = [json.loads(l) for l in wisdom_tmp.read_text().splitlines() if l.strip()]
    cool_rows = [r for r in rows if r.get("source") == "auto_cooldown"]
    assert len(cool_rows) == 1, f"expected one cooldown lesson, got {len(cool_rows)}"


def test_gc_duplicates_keeps_earliest_copy(wisdom_tmp):
    from src import lesson_gc
    _write_jsonl(wisdom_tmp, [
        _lesson("same text", days_ago=5, source="auto_cooldown"),
        _lesson("same text", days_ago=4, source="auto_cooldown"),
        _lesson("same text", days_ago=3, source="auto_cooldown"),
        _lesson("same text", days_ago=3, source="manual"),      # different source → kept
        _lesson("other", days_ago=1, source="auto_cooldown"),
    ])
    n, removed = lesson_gc.gc_duplicates()
    assert n == 2
    rows = [json.loads(l) for l in wisdom_tmp.read_text().splitlines()]
    active = [r for r in rows if r.get("active", True)]
    assert len(active) == 3
    assert all(r.get("deactivated_reason") == "duplicate" for r in removed)


def test_gc_stale_protects_seed_sources(wisdom_tmp):
    from src import lesson_gc
    _write_jsonl(wisdom_tmp, [
        _lesson("book lesson", days_ago=400, source="book:trading-in-the-zone", conf=0.85),
        _lesson("backtest lesson", days_ago=400, source="backtester", conf=0.80),
        _lesson("stale manual", days_ago=400, source="manual", conf=0.50),
    ])
    n, removed = lesson_gc.gc_stale()
    assert n == 1
    assert removed[0]["text"] == "stale manual"


def test_nightly_lesson_gc_step_reports_counts(monkeypatch):
    from src import nightly_conductor as nc, lesson_gc
    monkeypatch.setattr(lesson_gc, "gc_stale", lambda *a, **k: (3, [{}, {}, {}]))
    monkeypatch.setattr(lesson_gc, "gc_duplicates", lambda *a, **k: (2, [{}, {}]))
    res = nc._step_lesson_gc()
    assert res == {"gc_removed": 3, "gc_duplicates": 2}


# ──────────────────────────────────────────────────────────────────────
# 3. Weight proposals: archived rows skipped, only pick-time factors proposed
# ──────────────────────────────────────────────────────────────────────
def test_read_proposals_skips_archived(tmp_path):
    from src import weight_proposer as wp
    path = tmp_path / "proposals.jsonl"
    _write_jsonl(path, [
        {"id": "a", "factor": "score", "applied": False},
        {"id": "b", "factor": "score", "applied": False, "archived": True},
        {"id": "c", "factor": "score", "applied": True},
    ])
    ids = {r["id"] for r in wp.read_proposals(path=path, only_unapplied=True)}
    assert ids == {"a"}
    assert len(wp.read_proposals(path=path)) == 3


def test_propose_only_pick_time_factors():
    from src import weight_proposer as wp
    from src.learned_weights import PICK_TIME_FACTORS
    rows = []
    # 40 closed rows: strong sector effect AND strong rvol effect
    for i in range(40):
        sector = "Energy" if i % 2 else "Technology"
        r = 1.0 if sector == "Technology" else -1.0
        rows.append({
            "ticker": f"T{i}", "pick_date": "2026-06-01", "score": "0.72",
            "rsi": "55", "atr": "2.0", "adx": "25", "vol_ratio": "1.5" if r > 0 else "0.5",
            "dist_sma50_pct": "2.0", "sector": sector, "trade_type": "swing",
            "evaluation_status": "tp_hit" if r > 0 else "sl_hit",
            "r_multiple": str(r), "entry": "100", "stop_loss": "98", "take_profit": "104",
        })
    props = wp.propose(rows, run_id="t", min_n=5)
    factors = {p.factor for p in props}
    assert factors, "expected at least one proposal from a strong rvol split"
    assert factors <= set(PICK_TIME_FACTORS), f"non pick-time factors proposed: {factors}"
    assert "sector" not in factors and "trade_type" not in factors


# ──────────────────────────────────────────────────────────────────────
# 4. Pick-time factor inputs reach picks_log.csv
# ──────────────────────────────────────────────────────────────────────
def test_pick_factor_inputs_and_quality_gate_label():
    import main
    out = main._pick_factor_inputs({"rsi_14": 61.234, "atr_14": 3.14159, "adx": 27.77,
                                    "sma_50": 100.0, "close": 105.0})
    assert out == {"rsi": 61.23, "atr": 3.1416, "adx": 27.77, "dist_sma50_pct": 5.0}
    blank = main._pick_factor_inputs({})
    assert blank == {"rsi": "", "atr": "", "adx": "", "dist_sma50_pct": ""}
    assert main._quality_gate_label({"pass": True, "mode": "enforce", "reasons": []}) == "pass"
    assert main._quality_gate_label({"pass": False, "mode": "observe",
                                     "reasons": ["final score 0.650 < 0.70"]}) \
        == "observe:fail(final score 0.650 < 0.70)"
    assert main._quality_gate_label(None) == ""


def test_pick_logger_writes_factor_and_pattern_columns(tmp_path, monkeypatch):
    from src import pick_logger as pl
    log = tmp_path / "picks_log.csv"
    monkeypatch.setattr(pl, "LOG_PATH", log)
    for col in ("rsi", "atr", "adx", "dist_sma50_pct", "sector", "learned_mult",
                "learned_factors", "pattern_matches", "pattern_mult", "quality_gate"):
        assert col in pl.FIELDS
    pick = {
        "ticker": "ABC", "score": 0.81, "trade_type": "swing",
        "entry": 100.0, "stop_loss": 97.0, "take_profit": 106.0,
        "rsi": 58.1, "atr": 2.5, "adx": 24.0, "dist_sma50_pct": 3.2, "sector": "Technology",
        "learned_mult": 1.0, "learned_factors": "",
        "pattern_matches": "breakout,hhhl", "pattern_mult": 1.0, "quality_gate": "pass",
    }
    n = pl.log_picks([pick], {"regime": "bull"}, None)
    assert n == 1
    with log.open() as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 1
    row = rows[0]
    assert row["rsi"] == "58.1" and row["adx"] == "24.0" and row["sector"] == "Technology"
    assert row["dist_sma50_pct"] == "3.2"
    assert row["pattern_matches"] == "breakout,hhhl" and row["quality_gate"] == "pass"


# ──────────────────────────────────────────────────────────────────────
# 5. Pattern engine: lowercase OHLCV frames + pick-time persistence
# ──────────────────────────────────────────────────────────────────────
def _ohlcv(n=63, seed=0, title_case=True):
    rng = np.random.default_rng(seed)
    rets = rng.normal(0.002, 0.015, n)
    close = 100 * np.exp(np.cumsum(rets))
    high = close * (1 + np.abs(rng.normal(0, 0.008, n)))
    low = close * (1 - np.abs(rng.normal(0, 0.008, n)))
    open_ = np.r_[close[0], close[:-1]]
    vol = rng.integers(1_000_000, 5_000_000, n).astype(float)
    df = pd.DataFrame({"Open": open_, "High": high, "Low": low, "Close": close, "Volume": vol},
                      index=pd.date_range("2026-07-01", periods=n, freq="B"))
    if not title_case:
        df.columns = [c.lower() for c in df.columns]
    return df


def test_scan_ticker_accepts_lowercase_columns_like_data_fetcher():
    from src.pattern_engine import scan_ticker
    # Find a seed where at least one detector fires on the Title-case frame
    for seed in range(40):
        title = scan_ticker("T", df=_ohlcv(seed=seed), regime="bull")
        if title:
            break
    assert title, "no detector fired on 40 synthetic series — detectors broken?"
    lower = scan_ticker("T", df=_ohlcv(seed=seed, title_case=False), regime="bull")
    assert [m["pattern"] for m in lower] == [m["pattern"] for m in title], (
        "data_fetcher.fetch_ohlcv() lowercases columns; the detectors must "
        "still fire (they silently returned 0 matches for the engine's whole life)"
    )


def test_persist_pick_time_matches_joins_with_pick_outcomes(tmp_path):
    from src.pattern_engine import persist_pick_time_matches
    from src import pattern_stats as ps
    patterns = tmp_path / "patterns.jsonl"
    picks = [
        {"ticker": "abc", "scores": {"pattern_matches": "breakout,hhhl", "pattern_multiplier": 1.0}},
        {"ticker": "DEF", "scores": {"pattern_matches": ""}},
        {"ticker": "GHI", "scores": {}},
    ]
    n = persist_pick_time_matches(picks, pick_date="2026-06-01", regime="bull", path=patterns)
    assert n == 2
    rows = [json.loads(l) for l in patterns.read_text().splitlines()]
    assert {r["ticker"] for r in rows} == {"ABC"}
    assert all(r["date"] == "2026-06-01" and r["source"] == "pick_time" for r in rows)
    # build_stats joins on (ticker, pick_date) → the pick's own outcome now counts
    picks_log = tmp_path / "picks_log.csv"
    with picks_log.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["ticker", "pick_date", "r_multiple"])
        w.writeheader()
        w.writerow({"ticker": "ABC", "pick_date": "2026-06-01", "r_multiple": "1.5"})
    stats = ps.build_stats(patterns_path=patterns, picks_path=picks_log)
    assert stats["breakout"]["bull"]["n"] == 1
    assert stats["hhhl"]["bull"]["mean_r"] == 1.5
    assert persist_pick_time_matches([], pick_date="2026-06-01", path=patterns) == 0


# ──────────────────────────────────────────────────────────────────────
# 6. Quality gate (src/quality_gate.py) + config wiring
# ──────────────────────────────────────────────────────────────────────
def test_quality_gate_defaults_and_env_override():
    from src import quality_gate as qg
    eff = qg.resolve_config({}, env={})
    assert eff == {"enabled": True, "mode": "enforce", "min_final_score": 0.70, "min_rvol": 0.8}
    eff = qg.resolve_config({"quality_gate": {"mode": "observe", "min_rvol": "0.9"}}, env={})
    assert eff["mode"] == "observe" and eff["min_rvol"] == 0.9
    eff = qg.resolve_config({"quality_gate": {"mode": "enforce"}}, env={"QUALITY_GATE_MODE": "off"})
    assert eff["mode"] == "off"
    eff = qg.resolve_config({"quality_gate": {"enabled": False}}, env={"QUALITY_GATE_MODE": "enforce"})
    assert eff["mode"] == "off", "enabled: false must win over an env override"
    eff = qg.resolve_config({"quality_gate": {"mode": "bogus", "min_final_score": "nan"}}, env={})
    assert eff["mode"] == "enforce" and eff["min_final_score"] == 0.70


def test_quality_gate_enforce_drops_losing_buckets_only():
    from src import quality_gate as qg
    picks = [
        {"ticker": "GOOD", "scores": {"composite": 0.75, "vol_ratio": 1.2}},
        {"ticker": "LOWSCORE", "scores": {"composite": 0.65, "vol_ratio": 1.2}},
        {"ticker": "LOWRVOL", "scores": {"composite": 0.80, "vol_ratio": 0.5}},
        {"ticker": "NORVOL", "scores": {"composite": 0.80, "vol_ratio": None}},
        {"ticker": "SIGRVOL", "scores": {"composite": 0.80}, "signals": {"vol_ratio": 0.3}},
        {"ticker": "NOSCORE", "scores": {}},
    ]
    passed, rejected, eff = qg.apply_quality_gate(picks, {"quality_gate": {}}, env={})
    assert [p["ticker"] for p in passed] == ["GOOD", "NORVOL"]
    by = {r["ticker"]: r for r in rejected}
    assert set(by) == {"LOWSCORE", "LOWRVOL", "SIGRVOL", "NOSCORE"}
    assert all(r["rejection_stage"] == "quality_gate" for r in rejected)
    assert "final score 0.650 < 0.70" in by["LOWSCORE"]["reason"]
    assert "rvol 0.50 < 0.80" in by["LOWRVOL"]["reason"]
    assert picks[0]["scores"]["quality_gate"] == {"pass": True, "mode": "enforce", "reasons": []}
    assert picks[1]["scores"]["quality_gate"]["pass"] is False


def test_quality_gate_observe_annotates_but_keeps_everything():
    from src import quality_gate as qg
    picks = [{"ticker": "A", "scores": {"composite": 0.5, "vol_ratio": 0.2}}]
    passed, rejected, eff = qg.apply_quality_gate(picks, {"quality_gate": {"mode": "observe"}}, env={})
    assert len(passed) == 1 and rejected == [] and eff["mode"] == "observe"
    assert picks[0]["scores"]["quality_gate"]["pass"] is False
    assert len(picks[0]["scores"]["quality_gate"]["reasons"]) == 2


def test_live_config_enforces_quality_gate_with_evidence_thresholds():
    cfg = yaml.safe_load((REPO / "config.yaml").read_text())
    gate = cfg.get("quality_gate")
    assert gate and gate["enabled"] is True and gate["mode"] == "enforce"
    assert gate["min_final_score"] == 0.70 and gate["min_rvol"] == 0.8
    # The gate must sit above output.min_score, otherwise it is a no-op
    assert gate["min_final_score"] > cfg["output"]["min_score"]


def test_main_wires_quality_gate_before_top_n_trim():
    src = (REPO / "main.py").read_text()
    gate_at = src.index("from src.quality_gate import apply_quality_gate")
    trim_at = src.index('top = capped[: cfg["output"]["top_n_picks"]]')
    assert gate_at < trim_at, "quality gate must run before the final top-N trim"
    assert "_earnings_dropped.extend(_quality_dropped)" in src, (
        "quality-gate rejections must flow into the no-pick / rejection reports"
    )


# ──────────────────────────────────────────────────────────────────────
# 7. Sector boost defaults are neutral
# ──────────────────────────────────────────────────────────────────────
def test_sector_bonus_defaults_are_neutral():
    from src.scorer import sector_bonus
    from src.semiconductors import is_semi
    semi = next(t for t in ("NVDA", "AMD", "AVGO", "TSM", "INTC", "MU") if is_semi(t))
    assert sector_bonus(semi, {})["multiplier"] == 1.0, (
        "a missing sector: block must not re-enable the disabled +30% SEMI/AI boost"
    )
    assert sector_bonus(semi, {"semi_boost": 1.10, "ai_boost": 0.0})["multiplier"] == 1.10


# ──────────────────────────────────────────────────────────────────────
# 8. Brain state persists across CI runs
# ──────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("path", [
    "data/wisdom/lessons.jsonl", "data/wisdom/kill_list.json",
    "data/wisdom/patterns.jsonl", "data/patterns.jsonl", "data/pattern_stats.json",
])
def test_brain_state_files_are_not_gitignored(path):
    # --no-index: test the PATTERNS, not index membership. Before 2026-10-29
    # `data/` (directory pattern) made every `!data/...` negation a no-op and
    # tracked files only looked un-ignored because they were in the index.
    try:
        proc = subprocess.run(["git", "check-ignore", "-q", "--no-index", path], cwd=REPO,
                              capture_output=True, timeout=20)
    except (OSError, subprocess.TimeoutExpired):
        pytest.skip("git not available")
    if proc.returncode not in (0, 1):
        pytest.skip(f"git check-ignore unavailable: {proc.stderr.decode()[:80]}")
    assert proc.returncode == 1, f"{path} is gitignored — brain state would evaporate after CI"


def test_workflows_commit_wisdom_and_pattern_state():
    nightly = (REPO / ".github/workflows/nightly_brain.yml").read_text()
    for p in ("data/wisdom/lessons.jsonl", "data/wisdom/kill_list.json",
              "data/wisdom/patterns.jsonl", "data/patterns.jsonl", "data/pattern_stats.json"):
        assert p in nightly, f"nightly_brain.yml does not persist {p}"
    evaluate = (REPO / ".github/workflows/evaluate.yml").read_text()
    assert "data/wisdom/kill_list.json" in evaluate and "data/wisdom/lessons.jsonl" in evaluate, (
        "evaluate.yml runs auto_cooldown(apply=True); its kills/lessons must be committed"
    )
    daily = (REPO / ".github/workflows/daily-picks.yml").read_text()
    assert daily.count("data/patterns.jsonl") >= 2, (
        "daily-picks.yml must commit pick-time pattern matches in both commit steps"
    )


def test_tracked_lessons_have_no_fixture_spam():
    rows = [json.loads(l) for l in (REPO / "data/wisdom/lessons.jsonl").read_text().splitlines()
            if l.strip()]
    active = [r for r in rows if r.get("active", True)]
    cooldown = [r for r in active if r.get("source") == "auto_cooldown"]
    # One cooldown lesson per (ticker, window) at most; never thousands.
    assert len(cooldown) <= 50, f"{len(cooldown)} auto_cooldown lessons — dedupe guard regressed"
    dup = {}
    for r in active:
        dup[(r.get("source"), (r.get("text") or "").strip())] = \
            dup.get((r.get("source"), (r.get("text") or "").strip()), 0) + 1
    assert max(dup.values()) == 1, "duplicate active lessons in tracked lessons.jsonl"


def test_tracked_weight_proposals_have_no_fixture_rows():
    path = REPO / "data/weight_proposals.jsonl"
    rows = [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
    for r in rows:
        assert r.get("run_id") not in {"r", "tr", "test"}, f"pytest fixture row in live proposals: {r}"
        assert r.get("applied") or r.get("archived"), (
            "live proposals must be either applied or archived; unapplied rows "
            "from pre-audit calibration are not trustworthy"
        )
