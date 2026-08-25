"""Regression tests for the Aug 17–23 2026 overhaul (§7 + Clusters B–F).

Covers: canonical trade-state projections, price-sanity quarantine (the MRNA
$117–$174 corrupt prints), strict daily report scoping (no CDNS…BZH stale
block, flats ≠ losses), weekly/daily/hypothesis reconciliation, orphan
reconciliation idempotency (ANL closed exactly once), and the write-once
terminal guard.
"""
import csv
from datetime import date
from pathlib import Path

import pytest

from src import trade_state as ts
from src import price_sanity as ps


# ─── helpers ─────────────────────────────────────────────────────
def row(ticker="TST", pick_date="2026-08-19", status="pending", *,
        trade_type="swing", watch_only="false", entry="100", exit_price="",
        ret="", evaluated_on="", qty="10", **extra):
    r = {
        "ticker": ticker, "pick_date": pick_date, "trade_type": trade_type,
        "watch_only": watch_only, "entry": entry, "qty": qty,
        "evaluation_status": status, "evaluated_on": evaluated_on,
        "exit_price": exit_price, "actual_return_pct": ret,
    }
    r.update(extra)
    return r


def write_ledger(path: Path, rows):
    fieldnames = sorted({k for r in rows for k in r})
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


# ─── trade_state: canonical states & taxonomy ────────────────────
def test_legacy_statuses_project_to_canonical_states():
    assert ts.state_of(row(status="pending")) == ts.STATE_OPEN
    assert ts.state_of(row(status="tp_hit")) == ts.STATE_CLOSED_TP_WIN
    assert ts.state_of(row(status="sl_hit")) == ts.STATE_CLOSED_SL_LOSS
    assert ts.state_of(row(status="day_close")) == ts.STATE_CLOSED_TIME_EXIT
    assert ts.state_of(row(status="expired")) == ts.STATE_EXPIRED_OVERDUE
    assert ts.state_of(row(status="unreachable_entry")) == ts.STATE_NO_TRADE


def test_flat_time_exit_is_not_a_loss():
    flat = row(status="day_close", ret="0.0", exit_price="100")
    assert ts.classify_outcome(flat) == ts.OUTCOME_FLAT
    s = ts.summarize([flat])
    assert s["losses"] == 0 and s["flats"] == 1


def test_win_loss_classification_by_realized_return():
    assert ts.classify_outcome(row(status="day_close", ret="1.2", exit_price="101.2")) == ts.OUTCOME_WIN
    assert ts.classify_outcome(row(status="tp_hit", ret="5.97", exit_price="66.72")) == ts.OUTCOME_WIN
    assert ts.classify_outcome(row(status="sl_hit", ret="-2.7", exit_price="97.3")) == ts.OUTCOME_LOSS
    assert ts.classify_outcome(row(status="unreachable_entry")) == ts.OUTCOME_NO_TRADE
    # terminal with no exit data → honest UNVERIFIED, not a fabricated loss
    assert ts.classify_outcome(row(status="expired")) == ts.OUTCOME_UNVERIFIED


def test_strict_daily_scoping_excludes_other_days():
    rows = [
        row("A", status="sl_hit", evaluated_on="2026-08-18", ret="-1"),
        row("B", status="tp_hit", evaluated_on="2026-08-19", ret="5"),
        row("C", status="pending"),
    ]
    closed = ts.closed_on(rows, "2026-08-19")
    assert [r["ticker"] for r in closed] == ["B"]


def test_daily_sum_equals_range_reconciliation():
    rows = [
        row("A", status="sl_hit", evaluated_on="2026-08-18", ret="-1"),
        row("B", status="tp_hit", evaluated_on="2026-08-19", ret="5"),
        row("C", status="day_close", evaluated_on="2026-08-20", ret="0"),
    ]
    recon = ts.reconcile_counts(rows, "2026-08-17", "2026-08-21")
    assert recon["consistent"], recon


def test_position_identity_and_provenance():
    r = row("FTH", pick_date="2026-08-17", watch_only="true")
    assert ts.position_id(r) == "FTH|2026-08-17|watch_only"
    label = ts.provenance_label(r, today="2026-08-18")
    assert "2026-08-17" in label and "carryover" in label


def test_ages_recomputed_not_incremented():
    r = row("ANL", pick_date="2026-08-03")
    assert ts.days_open(r, today=date(2026, 8, 17)) == 14
    assert ts.days_open(r, today=date(2026, 8, 17)) == 14  # idempotent


# ─── price_sanity: the MRNA corrupt prints ───────────────────────
def test_mrna_corrupt_prints_quarantined():
    # entry 62.96; corrupt prints 117–174 must be rejected
    for bad in (117.0, 150.0, 174.0):
        v = ps.validate_quote(bad, 62.96)
        assert not v["ok"], f"corrupt print {bad} accepted"
        assert v["reason"] == ps.REASON_IMPLAUSIBLE_MOVE
    # the genuine TP touch is sane and passes
    assert ps.validate_quote(66.72, 62.96)["ok"]


def test_split_like_move_flagged_with_suspected_action():
    v = ps.validate_quote(50.0, 100.0)   # exact 2:1 split shape
    assert not v["ok"]
    assert "split" in (v["suspected_action"] or "")


def test_corroborated_large_move_allowed():
    v = ps.validate_quote(130.0, 100.0, corroborating_price=130.5)
    assert v["ok"] and v["reason"] == ps.REASON_CORROBORATED


def test_non_positive_and_no_reference():
    assert not ps.validate_quote(0, 100.0)["ok"]
    assert not ps.validate_quote(-5, 100.0)["ok"]
    assert ps.validate_quote(100.0, None)["ok"]  # no reference → cannot judge


def test_plausible_bar_rejects_corrupt_bars():
    assert ps.plausible_bar(100.0, 105.0, 98.0)
    assert not ps.plausible_bar(62.96, 174.0, 117.0)


def test_quarantine_log_written(tmp_path):
    v = ps.validate_quote(174.0, 62.96)
    ps.log_quarantine("MRNA", 174.0, 62.96, v, context="unit", data_dir=tmp_path)
    files = list(tmp_path.glob("quote_quarantine_*.jsonl"))
    assert files and "MRNA" in files[0].read_text()


# ─── write-once terminal guard (§7) ──────────────────────────────
def test_terminal_close_is_write_once(tmp_path, monkeypatch):
    import src.picks_csv as pc
    ledger = tmp_path / "picks_log.csv"
    write_ledger(ledger, [row("MRNA", status="tp_hit", evaluated_on="2026-08-19",
                              exit_price="66.72", ret="5.97")])
    monkeypatch.setattr(pc, "LOG_PATH", ledger)
    ok = pc.update_pick_row("2026-08-19", "MRNA",
                            {"evaluation_status": "sl_hit", "exit_price": "60.7"})
    assert ok is False
    with ledger.open() as f:
        r = next(csv.DictReader(f))
    assert r["evaluation_status"] == "tp_hit" and r["exit_price"] == "66.72"


# ─── evening report: strict scoping, buckets, no stale block ─────
@pytest.fixture
def aug19_ledger(tmp_path, monkeypatch):
    """Aug-19 shape: MRNA TP win (watch-only), one official SL loss closed
    the day before, and the legacy stale block settled as UNVERIFIED expiry."""
    rows = [
        row("MRNA", pick_date="2026-08-19", status="tp_hit", watch_only="true",
            entry="62.96", exit_price="66.72", ret="5.97", evaluated_on="2026-08-19"),
        row("SOFI", pick_date="2026-08-17", status="sl_hit", watch_only="false",
            entry="18.29", exit_price="17.8", ret="-2.68", evaluated_on="2026-08-18"),
        row("ADI", pick_date="2026-08-19", status="day_close", watch_only="false",
            entry="376.63", exit_price="376.7", ret="0.02", evaluated_on="2026-08-19"),
        # legacy stale block, settled once with deterministic dates
        row("CDNS", pick_date="2026-04-28", status="expired", evaluated_on="2026-05-08"),
        row("BZH", pick_date="2026-04-29", status="expired", evaluated_on="2026-05-09"),
        row("GDS", pick_date="2026-08-20", status="pending"),
    ]
    monkeypatch.chdir(tmp_path)
    write_ledger(Path("data/picks_log.csv"), rows)
    monkeypatch.setenv("PICK_DATE", "2026-08-19")
    return rows


def test_evening_report_scopes_strictly_and_buckets_correctly(aug19_ledger):
    import importlib
    import scripts.send_layman_evening as ev
    importlib.reload(ev)
    outcomes = ev._today_outcomes()
    research = ev._today_research_outcomes()
    # official today = ADI flat only; SOFI closed yesterday; stale block absent
    assert [r["ticker"] for r in outcomes] == ["ADI"]
    assert [r["ticker"] for r in research] == ["MRNA"]
    msg = ev.build_message(outcomes, research)
    assert "CDNS" not in msg and "BZH" not in msg and "SOFI" not in msg
    assert "0 wins · 0 losses · 1 flat" in msg
    assert "MRNA" in msg and "Watch-only research outcomes" in msg


def test_weekly_and_daily_views_reconcile(aug19_ledger, monkeypatch):
    """§7: summed strict-daily counts == weekly-window counts."""
    rows = ts.load_ledger()
    recon = ts.reconcile_counts(rows, "2026-08-17", "2026-08-21")
    assert recon["consistent"], recon
    week = ts.closed_between(rows, "2026-08-17", "2026-08-21")
    daily_sum = sum(len(ts.closed_on(rows, f"2026-08-{d:02d}")) for d in range(17, 22))
    assert len(week) == daily_sum == 3  # SOFI, MRNA, ADI


# ─── reconcile_ledger: orphans settled exactly once ──────────────
def test_reconcile_ledger_idempotent_and_deterministic(tmp_path, monkeypatch):
    import src.picks_csv as pc
    import scripts.reconcile_ledger as rl
    ledger = tmp_path / "data" / "picks_log.csv"
    write_ledger(ledger, [
        row("ANL", pick_date="2026-08-03", status="pending", trade_type="swing"),
        row("GDS", pick_date="2026-08-20", status="pending", trade_type="swing"),
    ])
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(pc, "LOG_PATH", ledger)

    orphans = rl.find_orphans(ts.load_ledger(), today=date(2026, 8, 24))
    assert [o[0]["ticker"] for o in orphans] == ["ANL"]
    horizon = orphans[0][1]
    assert horizon.isoformat() == "2026-08-13"  # pick_date + 10d, never "today"

    assert pc.update_pick_row("2026-08-03", "ANL", {
        "evaluation_status": "expired", "evaluated_on": horizon.isoformat()}) is True
    # second pass: nothing left, and the row cannot be re-closed
    assert rl.find_orphans(ts.load_ledger(), today=date(2026, 8, 24)) == []
    assert pc.update_pick_row("2026-08-03", "ANL", {
        "evaluation_status": "expired", "evaluated_on": "2026-08-24"}) is False
    anl = [r for r in ts.load_ledger() if r["ticker"] == "ANL"]
    assert len(anl) == 1 and anl[0]["evaluated_on"] == "2026-08-13"


def test_committed_ledger_has_no_open_orphans_before_evidence_window():
    """The real data/picks_log.csv one-time reconciliation stays settled:
    no pre-Aug-17 row may ever be open again (no stale-block resurrection)."""
    rows = ts.load_ledger()
    legacy_open = [r for r in rows
                   if (r.get("pick_date") or "") < "2026-08-17" and not ts.is_terminal(r)]
    assert legacy_open == [], [f"{r['ticker']} {r['pick_date']}" for r in legacy_open]
    anl = [r for r in rows if r.get("ticker") == "ANL"]
    assert anl and all(ts.is_terminal(r) for r in anl)
