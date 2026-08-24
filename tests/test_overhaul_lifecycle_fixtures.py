"""Aug-2026 lifecycle fixture tests — Clusters B/C/F end-to-end via the
intraday monitor.

The canonical MRNA bug: TP touched at 09:35 on 2026-08-19 but the position
was printed all day at corrupt prices ($117–$174) and never booked. These
tests replay that shape: TP touch books the win exactly once, monitoring
stops, carryovers are covered with provenance, and corrupt prints are
quarantined instead of consumed.
"""
import csv
import sys
from pathlib import Path
from unittest.mock import patch

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

COLS = ["pick_date", "pick_time", "ticker", "company", "tag", "trade_type",
        "watch_only", "score", "multiplier", "entry", "stop_loss",
        "take_profit", "risk_reward", "qty", "regime", "evaluation_status",
        "evaluated_on", "exit_price", "actual_return_pct", "r_multiple",
        "current_sl", "current_tp", "original_sl", "peak_price",
        "peak_rsi", "trail_active", "tp_raises", "sl_tightens"]


def _make_csv(tmp_path, rows):
    data = tmp_path / "data"
    data.mkdir(exist_ok=True)
    csv_path = data / "picks_log.csv"
    with csv_path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in COLS})
    return csv_path


def _mrna(status="pending", pick_date="2026-08-19"):
    return {"pick_date": pick_date, "ticker": "MRNA", "company": "Moderna",
            "trade_type": "swing", "watch_only": "true", "entry": 62.96,
            "stop_loss": 60.70, "take_profit": 66.72, "qty": 15,
            "evaluation_status": status, "original_sl": 60.70,
            "current_sl": 60.70, "current_tp": 66.72, "peak_price": 62.96}


def _read(csv_path, ticker):
    with csv_path.open() as f:
        for r in csv.DictReader(f):
            if r["ticker"] == ticker:
                return r
    return None


def _setup(csv_path, tmp_path, today="2026-08-19"):
    import importlib, intraday_monitor
    importlib.reload(intraday_monitor)
    intraday_monitor.TODAY = today
    intraday_monitor.PICKS_CSV = csv_path
    intraday_monitor.ALERTS_FILE = tmp_path / "data" / "alerts.json"
    return intraday_monitor


def _quote(price):
    return [
        patch("intraday_monitor.get_live_quote",
              return_value={"price": price, "vol_ratio": 1.0, "rsi": 55}),
        patch("intraday_monitor.fetch_recent_news", return_value=[]),
    ]


def test_mrna_tp_touch_books_win_once_and_monitoring_stops(tmp_path, monkeypatch):
    csv_path = _make_csv(tmp_path, [_mrna()])
    monkeypatch.chdir(tmp_path)
    mod = _setup(csv_path, tmp_path)
    patches = _quote(66.80)  # sane TP touch (+6.1% vs entry — passes gate)
    for p in patches: p.start()
    try:
        picks = mod.load_todays_picks()
        assert [p_["ticker"] for p_ in picks] == ["MRNA"]
        mod.monitor_existing_picks(picks, set())
    finally:
        for p in patches: p.stop()

    row = _read(csv_path, "MRNA")
    assert row["evaluation_status"] == "tp_hit"
    assert row["evaluated_on"] == "2026-08-19"
    assert float(row["exit_price"]) == 66.72  # booked at TP level

    # terminal ⇒ leaves the monitored set: never printed or re-closed again
    mod2 = _setup(csv_path, tmp_path)
    assert mod2.load_todays_picks() == []


def test_mrna_corrupt_prints_hold_state_and_quarantine(tmp_path, monkeypatch):
    csv_path = _make_csv(tmp_path, [_mrna()])
    monkeypatch.chdir(tmp_path)
    mod = _setup(csv_path, tmp_path)
    patches = _quote(174.0)  # the corrupt Aug-19 print (+176%)
    for p in patches: p.start()
    try:
        picks = mod.load_todays_picks()
        alerts = mod.monitor_existing_picks(picks, set())
    finally:
        for p in patches: p.stop()

    row = _read(csv_path, "MRNA")
    assert row["evaluation_status"] == "pending"  # state held, no fake TP
    assert row["exit_price"] == ""
    q = list((tmp_path / "data").glob("quote_quarantine_*.jsonl"))
    assert q and "MRNA" in q[0].read_text()
    assert any(f[0] == "quote_quarantined"
               for a in alerts for f in a.get("flags", []))


def test_carryover_is_monitored_with_provenance(tmp_path, monkeypatch):
    """Aug-18 shape: TTMI picked 2026-08-17 must still be monitored the next
    day, labeled as a carryover, and closable against its own pick_date row."""
    ttmi = {"pick_date": "2026-08-17", "ticker": "TTMI", "company": "TTM",
            "trade_type": "swing", "watch_only": "true", "entry": 140.0,
            "stop_loss": 132.52, "take_profit": 152.46, "qty": 5,
            "evaluation_status": "pending", "original_sl": 132.52,
            "current_sl": 132.52, "current_tp": 152.46, "peak_price": 140.0}
    csv_path = _make_csv(tmp_path, [ttmi])
    monkeypatch.chdir(tmp_path)
    mod = _setup(csv_path, tmp_path, today="2026-08-18")
    patches = _quote(131.90)  # SL touch, sane (−5.8%)
    for p in patches: p.start()
    try:
        picks = mod.load_todays_picks()
        assert len(picks) == 1
        assert picks[0]["pick_date"] == "2026-08-17"
        assert "carryover" in picks[0]["provenance"]
        mod.monitor_existing_picks(picks, set())
    finally:
        for p in patches: p.stop()

    row = _read(csv_path, "TTMI")
    assert row["evaluation_status"] == "sl_hit"   # close reached the 08-17 row
    assert row["evaluated_on"] == "2026-08-18"    # closed on the carryover day


def test_position_past_horizon_leaves_monitored_set(tmp_path, monkeypatch):
    """ANL shape: a swing 14+ days old is no longer the monitor's job (the
    evaluator/reconciler settles it) — it must not be printed forever."""
    anl = {"pick_date": "2026-08-03", "ticker": "ANL", "company": "ANL",
           "trade_type": "swing", "watch_only": "false", "entry": 13.0,
           "stop_loss": 12.0, "take_profit": 15.0, "qty": 10,
           "evaluation_status": "pending", "original_sl": 12.0,
           "current_sl": 12.0, "current_tp": 15.0, "peak_price": 13.0}
    csv_path = _make_csv(tmp_path, [anl])
    monkeypatch.chdir(tmp_path)
    mod = _setup(csv_path, tmp_path, today="2026-08-19")
    assert mod.load_todays_picks() == []


def test_intraday_workflow_persists_ledger():
    """Root cause #1: the intraday workflow must commit picks_log.csv or
    every intraday close is silently lost at run end."""
    wf = (REPO / ".github" / "workflows" / "intraday_monitor.yml").read_text()
    assert "data/picks_log.csv" in wf
    assert "quote_quarantine" in wf


def test_pick_schema_gate_blocks_actionable_shaped_but_empty():
    from src.pick_schema import enforce_pick_schema, validate_pick
    # Aug-17 failure shape: official pick with no levels
    empty = {"ticker": "FTH", "watch_only": False, "trade_type": "swing"}
    ok, problems = validate_pick(empty)
    assert not ok and problems
    out = enforce_pick_schema([empty])[0]
    assert out["watch_only"] is True
    assert "schema_incomplete" in out["watch_only_reason"]

    # Aug-20 reference shape passes untouched
    good = {"ticker": "WEAV", "watch_only": False, "trade_type": "day",
            "entry": 7.31, "stop_loss": 6.98, "take_profit": 7.86,
            "qty": 68, "score": 12.4}
    assert validate_pick(good) == (True, [])
    assert enforce_pick_schema([good])[0].get("watch_only") is False

    # watch-only must carry a specific reason
    wo = {"ticker": "NVDA", "watch_only": True, "watch_only_reason": ""}
    out = enforce_pick_schema([wo])[0]
    assert out["watch_only_reason"]
