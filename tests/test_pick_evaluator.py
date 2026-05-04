"""F3: pick_evaluator correctness — outcome tracker has been UNTESTED.

Discovered May 4 2026: 6 Apr 28 SEMI picks logged with entry prices
$2-$20 ABOVE that day's actual high. Trades were physically
unexecutable yet got marked sl_hit. Fixed by unreachable_entry guard
+ this test file (was zero-coverage before).
"""
import csv
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch
import pandas as pd
import pytest


# ════════════════════════════════════════════════════════════════
# Helpers
# ════════════════════════════════════════════════════════════════
def _ohlc(rows):
    """Build a DataFrame with proper index from list of (date, o, h, l, c)."""
    df = pd.DataFrame(rows, columns=["date", "Open", "High", "Low", "Close"])
    df["date"] = pd.to_datetime(df["date"])
    df.set_index("date", inplace=True)
    return df


def _seed_pick(tmp_path, **fields):
    """Create a fresh picks_log.csv in tmp_path with one pending pick."""
    base = {
        "pick_date": date.today().isoformat(),
        "pick_time": "12:00",
        "ticker": "TEST",
        "company": "Test Co",
        "tag": "TEST",
        "trade_type": "day",
        "score": "0.75",
        "multiplier": "1.0",
        "entry": "100.00",
        "stop_loss": "95.00",
        "take_profit": "110.00",
        "risk_reward": "2.0",
        "qty": "10",
        "days_to_earnings": "30",
        "regime": "bull",
        "spy_close": "500",
        "cape": "30",
        "evaluation_status": "pending",
        "evaluated_on": "",
        "exit_price": "",
        "actual_return_pct": "",
        "r_multiple": "",
    }
    base.update(fields)
    p = tmp_path / "picks_log.csv"
    with p.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(base.keys()))
        w.writeheader()
        w.writerow(base)
    return p


# ════════════════════════════════════════════════════════════════
# Tests for unreachable_entry detection (the core F3 fix)
# ════════════════════════════════════════════════════════════════
def test_unreachable_entry_above_high_marked(tmp_path, monkeypatch):
    """Entry logged $5 ABOVE pick_date high → unreachable_entry."""
    from src import pick_evaluator
    pick_date = date.today() - timedelta(days=1)
    log = _seed_pick(tmp_path,
                     pick_date=pick_date.isoformat(),
                     entry="100.00", stop_loss="95.00", take_profit="110.00")
    monkeypatch.setattr(pick_evaluator, "LOG_PATH", log)
    # Mock OHLC: entry=100 but day's high was only 95 (gap-down scenario)
    df = _ohlc([
        (pick_date.isoformat(), 92.0, 95.0, 90.0, 93.0),
    ])
    monkeypatch.setattr(pick_evaluator, "_fetch_ohlc", lambda t, s: df)

    counts = pick_evaluator.evaluate_pending()
    assert counts["unreachable_entry"] == 1
    assert counts["sl_hits"] == 0  # critical: NOT spuriously marked sl_hit

    rows = list(csv.DictReader(log.open()))
    assert rows[0]["evaluation_status"] == "unreachable_entry"


def test_unreachable_entry_below_low_marked(tmp_path, monkeypatch):
    """Entry logged $5 BELOW pick_date low → unreachable_entry."""
    from src import pick_evaluator
    pick_date = date.today() - timedelta(days=1)
    log = _seed_pick(tmp_path,
                     pick_date=pick_date.isoformat(),
                     entry="100.00", stop_loss="95.00", take_profit="110.00")
    monkeypatch.setattr(pick_evaluator, "LOG_PATH", log)
    df = _ohlc([
        (pick_date.isoformat(), 108.0, 112.0, 105.0, 110.0),  # low=105 > entry=100
    ])
    monkeypatch.setattr(pick_evaluator, "_fetch_ohlc", lambda t, s: df)

    counts = pick_evaluator.evaluate_pending()
    assert counts["unreachable_entry"] == 1


def test_entry_within_range_proceeds_normally(tmp_path, monkeypatch):
    """Entry inside [low, high] → normal eval, NOT flagged unreachable."""
    from src import pick_evaluator
    pick_date = date.today() - timedelta(days=1)
    log = _seed_pick(tmp_path,
                     pick_date=pick_date.isoformat(),
                     entry="100.00", stop_loss="95.00", take_profit="110.00")
    monkeypatch.setattr(pick_evaluator, "LOG_PATH", log)
    # Bar fully envelops entry; low > sl, high < tp → still_open
    df = _ohlc([
        (pick_date.isoformat(), 99.0, 105.0, 97.0, 103.0),
    ])
    monkeypatch.setattr(pick_evaluator, "_fetch_ohlc", lambda t, s: df)

    counts = pick_evaluator.evaluate_pending()
    assert counts["unreachable_entry"] == 0


def test_05pct_tolerance_for_rounding(tmp_path, monkeypatch):
    """Entry $0.30 above high but within 0.5% tolerance → NOT unreachable."""
    from src import pick_evaluator
    pick_date = date.today() - timedelta(days=1)
    log = _seed_pick(tmp_path,
                     pick_date=pick_date.isoformat(),
                     entry="100.00", stop_loss="90.00", take_profit="115.00")
    monkeypatch.setattr(pick_evaluator, "LOG_PATH", log)
    # High=99.80, entry=100.00 → 0.20 above high, tol=0.50 → allowed
    df = _ohlc([
        (pick_date.isoformat(), 98.0, 99.80, 97.0, 99.0),
    ])
    monkeypatch.setattr(pick_evaluator, "_fetch_ohlc", lambda t, s: df)

    counts = pick_evaluator.evaluate_pending()
    assert counts["unreachable_entry"] == 0


# ════════════════════════════════════════════════════════════════
# Lock-in tests for the existing (correct) outcome logic
# ════════════════════════════════════════════════════════════════
def test_sl_hit_when_low_breaches_stop(tmp_path, monkeypatch):
    from src import pick_evaluator
    pick_date = date.today() - timedelta(days=1)
    log = _seed_pick(tmp_path,
                     pick_date=pick_date.isoformat(),
                     entry="100.00", stop_loss="95.00", take_profit="110.00")
    monkeypatch.setattr(pick_evaluator, "LOG_PATH", log)
    # Entry inside bar, but low=94 < sl=95 → sl_hit
    df = _ohlc([
        (pick_date.isoformat(), 100.0, 102.0, 94.0, 96.0),
    ])
    monkeypatch.setattr(pick_evaluator, "_fetch_ohlc", lambda t, s: df)
    monkeypatch.setattr(pick_evaluator, "_add_spy_alpha", lambda *a, **k: "")
    monkeypatch.setattr(pick_evaluator, "_add_sector_alpha", lambda *a, **k: "")

    counts = pick_evaluator.evaluate_pending()
    assert counts["sl_hits"] == 1


def test_tp_hit_when_high_breaches_target(tmp_path, monkeypatch):
    from src import pick_evaluator
    pick_date = date.today() - timedelta(days=1)
    log = _seed_pick(tmp_path,
                     pick_date=pick_date.isoformat(),
                     entry="100.00", stop_loss="95.00", take_profit="110.00")
    monkeypatch.setattr(pick_evaluator, "LOG_PATH", log)
    df = _ohlc([
        (pick_date.isoformat(), 100.0, 112.0, 99.0, 108.0),
    ])
    monkeypatch.setattr(pick_evaluator, "_fetch_ohlc", lambda t, s: df)
    monkeypatch.setattr(pick_evaluator, "_add_spy_alpha", lambda *a, **k: "")
    monkeypatch.setattr(pick_evaluator, "_add_sector_alpha", lambda *a, **k: "")

    counts = pick_evaluator.evaluate_pending()
    assert counts["tp_hits"] == 1


def test_tie_break_open_closer_to_tp_means_tp_hit(tmp_path, monkeypatch):
    """When same bar hits both SL+TP, Open closer to TP → tp_hit."""
    from src import pick_evaluator
    pick_date = date.today() - timedelta(days=1)
    log = _seed_pick(tmp_path,
                     pick_date=pick_date.isoformat(),
                     entry="100.00", stop_loss="95.00", take_profit="110.00")
    monkeypatch.setattr(pick_evaluator, "LOG_PATH", log)
    # Open=109 (close to TP=110, far from SL=95) → TP first
    df = _ohlc([
        (pick_date.isoformat(), 109.0, 112.0, 94.0, 100.0),
    ])
    monkeypatch.setattr(pick_evaluator, "_fetch_ohlc", lambda t, s: df)
    monkeypatch.setattr(pick_evaluator, "_add_spy_alpha", lambda *a, **k: "")
    monkeypatch.setattr(pick_evaluator, "_add_sector_alpha", lambda *a, **k: "")

    counts = pick_evaluator.evaluate_pending()
    assert counts["tp_hits"] == 1
    assert counts["sl_hits"] == 0


def test_tie_break_open_closer_to_sl_means_sl_hit(tmp_path, monkeypatch):
    from src import pick_evaluator
    pick_date = date.today() - timedelta(days=1)
    log = _seed_pick(tmp_path,
                     pick_date=pick_date.isoformat(),
                     entry="100.00", stop_loss="95.00", take_profit="110.00")
    monkeypatch.setattr(pick_evaluator, "LOG_PATH", log)
    # Open=96 (close to SL=95, far from TP=110) → SL first
    df = _ohlc([
        (pick_date.isoformat(), 96.0, 112.0, 94.0, 100.0),
    ])
    monkeypatch.setattr(pick_evaluator, "_fetch_ohlc", lambda t, s: df)
    monkeypatch.setattr(pick_evaluator, "_add_spy_alpha", lambda *a, **k: "")
    monkeypatch.setattr(pick_evaluator, "_add_sector_alpha", lambda *a, **k: "")

    counts = pick_evaluator.evaluate_pending()
    assert counts["sl_hits"] == 1
    assert counts["tp_hits"] == 0


def test_still_open_when_neither_breached(tmp_path, monkeypatch):
    from src import pick_evaluator
    pick_date = date.today() - timedelta(days=1)
    log = _seed_pick(tmp_path,
                     pick_date=pick_date.isoformat(),
                     entry="100.00", stop_loss="95.00", take_profit="110.00")
    monkeypatch.setattr(pick_evaluator, "LOG_PATH", log)
    df = _ohlc([
        (pick_date.isoformat(), 100.0, 105.0, 97.0, 102.0),  # neither SL nor TP
    ])
    monkeypatch.setattr(pick_evaluator, "_fetch_ohlc", lambda t, s: df)

    counts = pick_evaluator.evaluate_pending()
    assert counts["sl_hits"] == 0
    assert counts["tp_hits"] == 0
