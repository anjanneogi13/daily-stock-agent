"""Evaluator determinism + expiry regression tests (Clusters B/E — Aug 2026).

Replaying any day must be idempotent: expiry dates come from the position's
own horizon, never from wall-clock "today"; corrupt bars are skipped; the
TP/SL walk never consumes bars beyond the hold horizon.
"""
import sys
from pathlib import Path
from unittest.mock import patch

import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from src import pick_evaluator as ev


def _bars(rows):
    """rows: list of (date_str, o, h, l, c)."""
    idx = pd.DatetimeIndex([pd.Timestamp(d) for d, *_ in rows])
    return pd.DataFrame(
        {"Open": [o for _, o, *_ in rows],
         "High": [h for _, _, h, *_ in rows],
         "Low": [l for _, _, _, l, _ in rows],
         "Close": [c for *_, c in rows],
         "Volume": [1_000_000] * len(rows)},
        index=idx)


def _row(ticker="ANL", trade_type="swing", pick_date="2026-08-03",
         entry=13.0, sl=12.0, tp=15.0):
    return {
        "pick_date": pick_date, "ticker": ticker, "trade_type": trade_type,
        "entry": str(entry), "stop_loss": str(sl), "take_profit": str(tp),
        "evaluation_status": "pending",
        "evaluated_on": "", "exit_price": "", "actual_return_pct": "",
        "r_multiple": "", "spy_close": "", "sector_etf": "",
        "spy_close_at_exit": "", "spy_return_pct": "", "alpha_pct": "",
        "sector_close": "", "sector_close_at_exit": "",
        "sector_return_pct": "", "sector_alpha_pct": "",
    }


def _run(rows, ohlc, today=(2026, 8, 24)):
    saved = []
    with patch.object(ev, "_load_picks", return_value=rows), \
         patch.object(ev, "_save_picks", side_effect=lambda r: saved.extend(r)), \
         patch.object(ev, "_fetch_ohlc", side_effect=lambda tk, start: ohlc.get(tk, pd.DataFrame())), \
         patch.object(ev, "_add_spy_alpha", return_value=""), \
         patch.object(ev, "_add_sector_alpha", return_value=""), \
         patch.object(ev, "_journal_attach", return_value=None):
        from datetime import datetime as _dt
        class _FrozenDT(_dt):
            @classmethod
            def now(cls, tz=None):
                return cls(*today, 12, 0, 0)
        with patch.object(ev, "datetime", _FrozenDT):
            counts = ev.evaluate_pending()
    return saved, counts


def test_expiry_date_is_horizon_bound_not_today():
    """ANL shape: swing past its 10d horizon expires with evaluated_on set to
    the last in-horizon session — identical no matter which day you re-run."""
    ohlc = {"ANL": _bars([
        ("2026-08-04", 13.0, 13.4, 12.8, 13.1),
        ("2026-08-11", 13.1, 13.3, 12.9, 13.0),   # last bar inside 10d horizon
        ("2026-08-20", 13.0, 13.2, 12.7, 12.9),   # outside horizon — ignored
    ])}
    saved_a, _ = _run([_row()], ohlc, today=(2026, 8, 24))
    saved_b, _ = _run([_row()], ohlc, today=(2026, 8, 28))  # re-run later
    row_a = saved_a[0]
    row_b = saved_b[0]
    assert row_a["evaluation_status"] == "expired"
    assert row_a["evaluated_on"] == "2026-08-11"          # not 08-24
    assert row_a["evaluated_on"] == row_b["evaluated_on"]  # idempotent replay
    assert row_a["exit_price"] == row_b["exit_price"]


def test_tp_walk_never_consumes_bars_beyond_horizon():
    """A TP touch after the horizon must NOT book a win — the position
    expired first (exactly-one-terminal-transition)."""
    ohlc = {"ANL": _bars([
        ("2026-08-04", 13.0, 13.4, 12.8, 13.1),
        ("2026-08-20", 13.0, 15.5, 12.9, 15.2),   # TP touch, but 17d out
    ])}
    saved, _ = _run([_row()], ohlc)
    assert saved[0]["evaluation_status"] == "expired"
    assert saved[0]["evaluated_on"] == "2026-08-04"


def test_corrupt_bar_skipped_in_walk():
    """An MRNA-style corrupt bar (implausible vs prior close) must not
    trigger a TP/SL booking; the sane later bar decides the outcome."""
    row = _row(ticker="MRNA", pick_date="2026-08-19",
               entry=62.96, sl=60.70, tp=66.72)
    ohlc = {"MRNA": _bars([
        ("2026-08-19", 63.0, 174.0, 117.0, 150.0),  # corrupt print bar
        ("2026-08-20", 63.5, 66.9, 62.8, 66.8),     # genuine TP touch
    ])}
    saved, _ = _run([row], ohlc, today=(2026, 8, 24))
    assert saved[0]["evaluation_status"] == "tp_hit"
    assert saved[0]["evaluated_on"] == "2026-08-20"   # corrupt bar ignored
    assert float(saved[0]["exit_price"]) == 66.72


def test_expiry_without_bars_settles_unverified():
    """No price data inside the horizon → settle once, honestly, with no
    fabricated exit price (UNVERIFIED classification downstream)."""
    saved, _ = _run([_row()], {"ANL": pd.DataFrame()})
    r = saved[0]
    assert r["evaluation_status"] == "expired"
    assert r["exit_price"] == "" and r["actual_return_pct"] == ""
    assert r["evaluated_on"] == "2026-08-13"  # deterministic horizon date

    from src.trade_state import classify_outcome, OUTCOME_UNVERIFIED
    assert classify_outcome(r) == OUTCOME_UNVERIFIED
