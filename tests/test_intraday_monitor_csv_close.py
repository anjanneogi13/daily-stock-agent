"""Test that intraday_monitor closes picks in CSV when SL/TP hit.

Bug fixed 2026-05-05: monitor detected SL hits, alerted on Telegram, but
NEVER wrote to picks_log.csv. So the same pick alerted 4× the same day,
and end-of-day evaluator was the only thing that ever closed a pick.
"""
import csv
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))


def _make_picks_csv(tmp_path, rows):
    data = tmp_path / "data"
    data.mkdir()
    csv_path = data / "picks_log.csv"
    cols = ["pick_date", "pick_time", "ticker", "company", "tag", "trade_type",
            "score", "multiplier", "entry", "stop_loss", "take_profit",
            "risk_reward", "qty", "regime", "evaluation_status",
            "evaluated_on", "exit_price", "actual_return_pct", "r_multiple",
            "current_sl", "current_tp", "original_sl", "peak_price",
            "peak_rsi", "trail_active", "tp_raises", "sl_tightens"]
    with csv_path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in cols})
    return csv_path


def _read_row(csv_path, ticker):
    with csv_path.open() as f:
        for r in csv.DictReader(f):
            if r["ticker"] == ticker:
                return r
    return None


def _base_pick(ticker="A", entry=100.0, sl=95.0, tp=110.0, status="pending"):
    return {"pick_date": "2026-05-05", "ticker": ticker, "company": ticker,
            "trade_type": "swing", "entry": entry, "stop_loss": sl,
            "take_profit": tp, "qty": 10, "evaluation_status": status,
            "original_sl": sl, "current_sl": sl, "current_tp": tp,
            "peak_price": entry}


def _setup_module(csv_path, tmp_path):
    """Reload first (so module-level imports run with our path), THEN
    patch. Patching before reload would be undone by the reload's
    re-execution of `from intraday_scanner import get_live_quote`.
    """
    import importlib, intraday_monitor
    importlib.reload(intraday_monitor)
    intraday_monitor.TODAY = "2026-05-05"
    intraday_monitor.PICKS_CSV = csv_path
    intraday_monitor.ALERTS_FILE = tmp_path / "data" / "alerts.json"
    return intraday_monitor


def _patches(price, vol_ratio=1.0, rsi=50):
    """Patch BOTH the monitor's reference AND the original module
    attribute, so reload-followed-by-patch is robust."""
    return [
        patch("intraday_monitor.get_live_quote",
              return_value={"price": price, "vol_ratio": vol_ratio, "rsi": rsi}),
        patch("intraday_monitor.fetch_recent_news", return_value=[]),
    ]


def test_sl_hit_writes_row_to_csv(tmp_path, monkeypatch):
    csv_path = _make_picks_csv(tmp_path, [_base_pick("A", 100, 95, 110)])
    monkeypatch.chdir(tmp_path)
    mod = _setup_module(csv_path, tmp_path)
    patches = _patches(price=94.50)
    for p in patches: p.start()
    try:
        picks = mod.load_todays_picks()
        mod.monitor_existing_picks(picks, set())
    finally:
        for p in patches: p.stop()
    row = _read_row(csv_path, "A")
    assert row["evaluation_status"] == "sl_hit", \
        f"expected 'sl_hit', got '{row['evaluation_status']}'"
    assert row["evaluated_on"] == "2026-05-05"
    assert float(row["exit_price"]) == 95.0


def test_tp_hit_writes_row_to_csv(tmp_path, monkeypatch):
    csv_path = _make_picks_csv(tmp_path, [_base_pick("B", 100, 95, 110)])
    monkeypatch.chdir(tmp_path)
    mod = _setup_module(csv_path, tmp_path)
    patches = _patches(price=110.50, rsi=60)
    for p in patches: p.start()
    try:
        picks = mod.load_todays_picks()
        mod.monitor_existing_picks(picks, set())
    finally:
        for p in patches: p.stop()
    row = _read_row(csv_path, "B")
    assert row["evaluation_status"] == "tp_hit"
    assert float(row["exit_price"]) == 110.0


def test_already_closed_pick_skips_write_and_alert(tmp_path, monkeypatch):
    csv_path = _make_picks_csv(
        tmp_path, [_base_pick("C", 100, 95, 110, status="sl_hit")])
    monkeypatch.chdir(tmp_path)
    mod = _setup_module(csv_path, tmp_path)
    patches = _patches(price=94.0, rsi=40)
    for p in patches: p.start()
    try:
        picks = mod.load_todays_picks()
        assert picks == [], "closed picks must be filtered out"
    finally:
        for p in patches: p.stop()
    row = _read_row(csv_path, "C")
    assert row["evaluation_status"] == "sl_hit"


def test_near_sl_does_not_close(tmp_path, monkeypatch):
    csv_path = _make_picks_csv(tmp_path, [_base_pick("D", 100, 95, 110)])
    monkeypatch.chdir(tmp_path)
    mod = _setup_module(csv_path, tmp_path)
    patches = _patches(price=95.50, rsi=45)
    for p in patches: p.start()
    try:
        picks = mod.load_todays_picks()
        mod.monitor_existing_picks(picks, set())
    finally:
        for p in patches: p.stop()
    row = _read_row(csv_path, "D")
    assert row["evaluation_status"] == "pending", \
        "near_sl alone must NOT close the pick"


def test_closed_row_has_required_evaluator_columns(tmp_path, monkeypatch):
    csv_path = _make_picks_csv(tmp_path, [_base_pick("E", 100, 95, 110)])
    monkeypatch.chdir(tmp_path)
    mod = _setup_module(csv_path, tmp_path)
    patches = _patches(price=94.0, rsi=30)
    for p in patches: p.start()
    try:
        picks = mod.load_todays_picks()
        mod.monitor_existing_picks(picks, set())
    finally:
        for p in patches: p.stop()
    row = _read_row(csv_path, "E")
    for col in ("evaluation_status", "evaluated_on", "exit_price",
                "actual_return_pct", "r_multiple"):
        assert row[col] not in ("", None), \
            f"required column {col!r} not populated"
    assert float(row["actual_return_pct"]) == pytest.approx(-5.0, abs=0.1)
    assert float(row["r_multiple"]) == pytest.approx(-1.0, abs=0.1)


def test_idempotent_second_run_no_double_write(tmp_path, monkeypatch):
    csv_path = _make_picks_csv(tmp_path, [_base_pick("F", 100, 95, 110)])
    monkeypatch.chdir(tmp_path)
    mod = _setup_module(csv_path, tmp_path)
    patches = _patches(price=94.0, rsi=30)
    for p in patches: p.start()
    try:
        picks = mod.load_todays_picks()
        mod.monitor_existing_picks(picks, set())
        first = _read_row(csv_path, "F")
        picks2 = mod.load_todays_picks()
        assert picks2 == [], "second run must see no pending picks"
        mod.monitor_existing_picks(picks2, set())
        second = _read_row(csv_path, "F")
    finally:
        for p in patches: p.stop()
    assert first == second, "row must be byte-identical after second run"
