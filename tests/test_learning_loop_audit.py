"""Regression tests for the 2026-10-29 self-learning audit.

Each test pins one of the root causes that kept the weekly/monthly agent
from learning anything for six months:

  1. nightly_conductor passed the calibration REPORT (not rows) to
     weight_proposer.propose -> crashed every night.
  2. parallel_scorer ignored config.yaml SL/TP multipliers -> every swing
     pick ran at R:R 1.25 (needs 44% win rate to break even; realized 36%).
  3. Learning reports windowed by pick_date, so a 7-day window held ~1
     closed swing -> "Need more data" forever.  src/outcome_window is now
     the single source of truth (closed+verified, by evaluated_on).
  4. main.py brain block read p["news"] (a LIST) as a dict -> every pick
     raised, "Brain analyzed 0/N", brain_* columns 100% empty.
  5. weight_applier "kill" set multipliers to 0.0 — unrevivable.
  6. 68 picks settled "expired" with no price data (lost outcomes) -> the
     backfill re-walks them with the real evaluator and never touches
     verified rows.
"""
from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

import pytest

from src import outcome_window as ow


# ─── outcome_window ──────────────────────────────────────────────────────────

def _row(**kw):
    base = {
        "pick_date": "2026-10-01", "ticker": "AAA", "trade_type": "swing",
        "evaluation_status": "pending", "evaluated_on": "", "r_multiple": "",
        "actual_return_pct": "", "watch_only": "",
    }
    base.update(kw)
    return base


def test_closed_verified_requires_numeric_r():
    assert ow.is_closed_verified(_row(evaluation_status="tp_hit", r_multiple="1.25"))
    assert ow.is_closed_verified(_row(evaluation_status="expired", r_multiple="-0.3"))
    assert ow.is_closed_verified(_row(evaluation_status="day_close", r_multiple="0"))
    assert not ow.is_closed_verified(_row(evaluation_status="expired", r_multiple=""))
    assert not ow.is_closed_verified(_row(evaluation_status="pending"))
    assert not ow.is_closed_verified(_row(evaluation_status="unreachable_entry"))
    assert ow.is_unverified_expired(_row(evaluation_status="expired", r_multiple=""))
    assert not ow.is_unverified_expired(_row(evaluation_status="expired", r_multiple="0.5"))


def test_outcomes_window_uses_evaluated_on_not_pick_date():
    rows = [
        # picked before the window, closed inside it -> counts
        _row(ticker="IN", pick_date="2026-09-20", evaluation_status="sl_hit",
             evaluated_on="2026-10-03", r_multiple="-1"),
        # picked inside the window, still pending -> not an outcome
        _row(ticker="PEND", pick_date="2026-10-02"),
        # closed outside the window -> excluded
        _row(ticker="OLD", pick_date="2026-09-01", evaluation_status="tp_hit",
             evaluated_on="2026-09-15", r_multiple="1.25"),
        # watch-only rows are never learning material
        _row(ticker="WATCH", pick_date="2026-10-01", evaluation_status="tp_hit",
             evaluated_on="2026-10-04", r_multiple="1.25", watch_only="True"),
        # legacy row without evaluated_on falls back to pick_date
        _row(ticker="LEGACY", pick_date="2026-10-05", evaluation_status="expired",
             evaluated_on="", r_multiple="0.2"),
    ]
    start, end = date(2026, 10, 1), date(2026, 10, 7)
    closed = ow.outcomes_in_window(start, end, rows)
    assert [r["ticker"] for r in closed] == ["IN", "LEGACY"]
    picked = ow.picks_in_window(start, end, rows)
    assert [r["ticker"] for r in picked] == ["PEND", "LEGACY"]

    rep = ow.window_report(start, end, rows)
    assert rep["pending_total"] == 1
    assert rep["summary"]["n"] == 2
    assert rep["summary"]["wins"] == 1 and rep["summary"]["losses"] == 1
    assert rep["summary"]["win_rate"] == 0.5
    assert rep["summary"]["by_status"] == {"sl_hit": 1, "expired": 1}


def test_summarize_win_is_r_positive_not_status():
    closed = [
        _row(evaluation_status="expired", r_multiple="0.4"),
        _row(evaluation_status="expired", r_multiple="-0.4"),
        _row(evaluation_status="day_close", r_multiple="0"),
    ]
    s = ow.summarize(closed)
    assert (s["wins"], s["losses"], s["flats"]) == (1, 1, 1)
    assert s["total_r"] == 0.0


# ─── nightly conductor: rows (not report) reach the proposer ────────────────

def test_calibration_propose_passes_rows_and_min_n(tmp_path, monkeypatch):
    from src import nightly_conductor as nc
    from src import weight_proposer as wp

    log = tmp_path / "picks_log.csv"
    fields = ["pick_date", "ticker", "score", "trade_type", "evaluation_status",
              "r_multiple", "watch_only", "regime", "sector", "tag"]
    with log.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for i in range(30):
            w.writerow({"pick_date": "2026-10-01", "ticker": f"T{i}", "score": "0.75",
                        "trade_type": "swing", "evaluation_status": "tp_hit",
                        "r_multiple": "1.0", "watch_only": "", "regime": "bull",
                        "sector": "Tech", "tag": ""})
        # watch-only + unverified rows must be filtered out
        w.writerow({"pick_date": "2026-10-01", "ticker": "W", "score": "0.9",
                    "trade_type": "swing", "evaluation_status": "tp_hit",
                    "r_multiple": "3.0", "watch_only": "True", "regime": "bull",
                    "sector": "Tech", "tag": ""})
        w.writerow({"pick_date": "2026-10-01", "ticker": "U", "score": "0.9",
                    "trade_type": "swing", "evaluation_status": "expired",
                    "r_multiple": "", "watch_only": "", "regime": "bull",
                    "sector": "Tech", "tag": ""})
    monkeypatch.setattr(nc, "PICKS_LOG", log)

    seen = {}
    def fake_propose(rows, run_id, min_n=30):
        seen["rows"] = rows
        seen["min_n"] = min_n
        return []
    monkeypatch.setattr(wp, "propose", fake_propose)
    monkeypatch.setattr(wp, "write_proposals", lambda props, path=None: len(props))

    res = nc._step_calibration_propose()
    assert "skipped" not in res, res
    assert isinstance(seen["rows"], list) and all(isinstance(r, dict) for r in seen["rows"])
    assert len(seen["rows"]) == 30 == res["closed_rows"]
    assert seen["min_n"] == nc.LIVE_PROPOSAL_MIN_N


# ─── parallel_scorer honours config SL/TP ───────────────────────────────────

def test_plan_overrides_read_config_multipliers():
    from src.parallel_scorer import _plan_overrides
    cfg = {"risk": {"risk_per_trade_pct": 1.0, "stop_loss_atr_mult": 1.5,
                    "take_profit_atr_mult": 3.0}}
    assert _plan_overrides(cfg, "swing") == {"risk_pct": 0.01, "atr_mult_sl": 1.5,
                                             "atr_mult_tp": 3.0}
    # swing_trading block wins when present
    cfg["swing_trading"] = {"atr_mult_sl": 2.0, "atr_mult_tp": 5.0}
    assert _plan_overrides(cfg, "swing")["atr_mult_tp"] == 5.0
    # day trades keep their own tight multipliers inside atr_trade_plan
    assert "atr_mult_sl" not in _plan_overrides(cfg, "day")
    # already-fractional risk is accepted as is; empty config -> only the 1% risk default
    assert _plan_overrides({"risk": {"risk_per_trade_pct": 0.02}}, "swing")["risk_pct"] == 0.02
    assert _plan_overrides({}, "swing") == {"risk_pct": 0.01}


def test_live_config_gives_swing_rr_of_two():
    import yaml
    from src.parallel_scorer import _plan_overrides
    from src.risk_manager import atr_trade_plan
    cfg = yaml.safe_load(Path("config.yaml").read_text())
    plan = atr_trade_plan(100.0, 2.0, 10_000, trade_type="swing", **_plan_overrides(cfg, "swing"))
    assert plan["risk_reward"] >= 2.0


# ─── main.py brain inputs / risk_reward ─────────────────────────────────────

def test_brain_news_inputs_handle_list_shaped_news():
    import main
    # live shape: p["news"] is a list of articles, classified signal lives in news_signal
    assert main._brain_news_inputs({"news": [{"title": "x"}]}) == (0.0, "neutral")
    assert main._brain_news_inputs({"news": [], "news_signal": {"tradeable_score": 0.7,
                                                                "sentiment": "bullish"}}) == (0.7, "bullish")
    assert main._brain_news_inputs({"news": {"tradeable_score": 0.4,
                                             "sentiment": "positive"}}) == (0.4, "positive")
    assert main._brain_news_inputs({}) == (0.0, "neutral")


def test_plan_risk_reward_is_recomputed_not_fabricated():
    import main
    assert main._plan_risk_reward({"entry": 100, "stop_loss": 97, "take_profit": 106}) == 2.0
    assert main._plan_risk_reward({"entry": 100, "stop_loss": 96, "take_profit": 105}) == 1.25
    assert main._plan_risk_reward({"entry": 100, "stop_loss": 100, "take_profit": 106}) == 0.0
    assert main._plan_risk_reward({}) == 0.0


# ─── backfill of unverified expired rows ────────────────────────────────────

def test_backfill_only_touches_unverified_rows_and_restores_unfetchable(tmp_path, monkeypatch):
    import importlib
    import pandas as pd
    from src import pick_evaluator as pe
    bf = importlib.import_module("scripts.backfill_unverified_outcomes")

    log = tmp_path / "picks_log.csv"
    fields = ["pick_date", "ticker", "trade_type", "entry", "stop_loss", "take_profit",
              "evaluation_status", "evaluated_on", "exit_price", "actual_return_pct",
              "r_multiple", "watch_only"]
    rows = [
        # verified outcome -> must never change
        dict(pick_date="2026-06-01", ticker="KEEP", trade_type="swing", entry="100",
             stop_loss="96", take_profit="105", evaluation_status="sl_hit",
             evaluated_on="2026-06-03", exit_price="96", actual_return_pct="-4.0",
             r_multiple="-1.0", watch_only=""),
        # unverified expired, data available -> re-walked (TP on day 2)
        dict(pick_date="2026-06-01", ticker="FIX", trade_type="swing", entry="100",
             stop_loss="96", take_profit="105", evaluation_status="expired",
             evaluated_on="2026-06-15", exit_price="", actual_return_pct="",
             r_multiple="", watch_only=""),
        # unverified expired, no data -> restored exactly as it was
        dict(pick_date="2026-06-01", ticker="NODATA", trade_type="swing", entry="50",
             stop_loss="48", take_profit="55", evaluation_status="expired",
             evaluated_on="2026-06-15", exit_price="", actual_return_pct="",
             r_multiple="", watch_only=""),
        # watch-only unverified -> skipped by default
        dict(pick_date="2026-06-01", ticker="WATCH", trade_type="swing", entry="50",
             stop_loss="48", take_profit="55", evaluation_status="expired",
             evaluated_on="2026-06-15", exit_price="", actual_return_pct="",
             r_multiple="", watch_only="True"),
    ]
    with log.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    monkeypatch.setattr(pe, "LOG_PATH", log)
    monkeypatch.setattr(bf, "AUDIT_DIR", tmp_path / "learning")

    def fake_ohlc(ticker, start):
        if ticker != "FIX":
            return pd.DataFrame()
        idx = pd.to_datetime(["2026-06-01", "2026-06-02"])
        return pd.DataFrame({"Open": [100.0, 101.0], "High": [101.0, 106.0],
                             "Low": [99.0, 100.5], "Close": [100.5, 105.5]}, index=idx)
    monkeypatch.setattr(pe, "_fetch_ohlc", fake_ohlc)
    monkeypatch.setattr(pe, "_add_spy_alpha", lambda row, d, r: "")
    monkeypatch.setattr(pe, "_add_sector_alpha", lambda row, d, r: "")
    monkeypatch.setattr(pe, "_ensure_sector_benchmark_anchor", lambda row: ("", None))
    journal_calls = []
    monkeypatch.setattr(pe, "_journal_attach", lambda **kw: journal_calls.append(kw) or True)

    # dry run: nothing written, journal untouched
    rep = bf.run(apply=False)
    assert rep["candidates"] == 2 and rep["repaired"] == 1 and rep["still_unverified"] == 1
    assert journal_calls == []
    after = {r["ticker"]: r for r in csv.DictReader(log.open())}
    assert after["FIX"]["evaluation_status"] == "expired" and after["FIX"]["r_multiple"] == ""

    # apply: FIX repaired, KEEP/NODATA/WATCH byte-identical
    rep = bf.run(apply=True)
    assert rep["repaired"] == 1
    after = {r["ticker"]: r for r in csv.DictReader(log.open())}
    assert after["FIX"]["evaluation_status"] == "tp_hit"
    assert float(after["FIX"]["r_multiple"]) == pytest.approx(1.25)
    assert after["FIX"]["evaluated_on"] == "2026-06-02"
    for t in ("KEEP", "NODATA", "WATCH"):
        assert {k: after[t][k] for k in fields} == next(r for r in rows if r["ticker"] == t)
    assert journal_calls and journal_calls[0]["ticker"] == "FIX"
    assert (tmp_path / "learning").exists()

    # idempotent: second apply finds nothing
    rep = bf.run(apply=True)
    assert rep["candidates"] == 1 and rep["repaired"] == 0  # only NODATA remains


# ─── journal outcome sync ───────────────────────────────────────────────────

def test_sync_journal_outcomes_fills_only_open_rows(tmp_path, monkeypatch):
    import importlib
    import json
    from src import signal_journal as sj
    from src import outcome_window as ow
    sync = importlib.import_module("scripts.sync_journal_outcomes")

    journal = tmp_path / "signal_journal.jsonl"
    journal.write_text("\n".join(json.dumps(r) for r in [
        {"pick_date": "2026-10-01", "ticker": "OPEN", "signals": {}, "outcome": None,
         "r_multiple": None, "actual_return_pct": None, "evaluated_on": None},
        {"pick_date": "2026-10-01", "ticker": "DONE", "signals": {}, "outcome": "win",
         "r_multiple": 9.9, "actual_return_pct": 9.9, "evaluated_on": "2026-10-02"},
        {"pick_date": "2026-10-01", "ticker": "PEND", "signals": {}, "outcome": None,
         "r_multiple": None, "actual_return_pct": None, "evaluated_on": None},
    ]) + "\n")
    monkeypatch.setattr(sj, "JOURNAL", journal)

    log = tmp_path / "picks_log.csv"
    fields = ["pick_date", "ticker", "evaluation_status", "evaluated_on",
              "r_multiple", "actual_return_pct", "watch_only"]
    with log.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerow(dict(pick_date="2026-10-01", ticker="OPEN", evaluation_status="sl_hit",
                        evaluated_on="2026-10-03", r_multiple="-1.0",
                        actual_return_pct="-4.0", watch_only=""))
        # picks_log says a different R for DONE — journal already closed, must not change
        w.writerow(dict(pick_date="2026-10-01", ticker="DONE", evaluation_status="tp_hit",
                        evaluated_on="2026-10-03", r_multiple="1.0",
                        actual_return_pct="3.0", watch_only=""))
        w.writerow(dict(pick_date="2026-10-01", ticker="PEND", evaluation_status="pending",
                        evaluated_on="", r_multiple="", actual_return_pct="", watch_only=""))
        # unverified expired -> not an outcome, never attached
        w.writerow(dict(pick_date="2026-10-01", ticker="UNVER", evaluation_status="expired",
                        evaluated_on="2026-10-15", r_multiple="", actual_return_pct="",
                        watch_only=""))
    monkeypatch.setattr(ow, "PICKS_LOG", log)

    rep = sync.run(apply=False)
    assert rep["unsynced"] == 1 and rep["attached"] == 0
    rep = sync.run(apply=True)
    assert rep["attached"] == 1
    rows = {r["ticker"]: r for r in map(json.loads, journal.read_text().splitlines())}
    assert rows["OPEN"]["outcome"] == "loss" and rows["OPEN"]["r_multiple"] == -1.0
    assert rows["OPEN"]["evaluated_on"] == "2026-10-03"
    assert rows["DONE"]["r_multiple"] == 9.9  # untouched
    assert rows["PEND"]["outcome"] is None
    # idempotent
    assert sync.run(apply=True)["unsynced"] == 0
