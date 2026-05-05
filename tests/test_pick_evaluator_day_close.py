"""Test that pick_evaluator force-closes day-trades at pick_date close
if neither SL nor TP was hit during the day.

Bug fixed 2026-05-05: evaluator had ZERO knowledge of trade_type. Day
trades that didn't hit SL/TP intraday stayed 'pending' forever (until
20-day expiry kicked in). Concrete victim: MPWR picked 2026-05-02 as
trade_type=day, still pending 3 days later.

Rule: trade_type=day MUST close on pick_date. If SL/TP hit → that wins.
Otherwise → mark 'day_close' with exit_price = pick_date Close.
"""
import sys
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from src import pick_evaluator as ev


# ─────────────────── Helpers ───────────────────
def _bar(date_str, o, h, l, c):
    """Single OHLC bar as a 1-row DataFrame indexed by date."""
    idx = pd.DatetimeIndex([pd.Timestamp(date_str)])
    return pd.DataFrame(
        {"Open":[o], "High":[h], "Low":[l], "Close":[c], "Volume":[1_000_000]},
        index=idx)


def _row(ticker="MPWR", trade_type="day", pick_date="2026-05-02",
         entry=1583.48, sl=1545.16, tp=1647.35, status="pending"):
    return {
        "pick_date": pick_date, "ticker": ticker, "trade_type": trade_type,
        "entry": str(entry), "stop_loss": str(sl), "take_profit": str(tp),
        "evaluation_status": status,
        "evaluated_on": "", "exit_price": "", "actual_return_pct": "",
        "r_multiple": "", "spy_close": "", "sector_etf": "",
        "spy_close_at_exit": "", "spy_return_pct": "", "alpha_pct": "",
        "sector_close": "", "sector_close_at_exit": "",
        "sector_return_pct": "", "sector_alpha_pct": "",
    }


def _run_evaluator(rows, ohlc_for_ticker):
    """Run evaluate_pending() with mocked load/save/fetch/SPY/journal.
    Returns the saved rows for assertions."""
    saved = []
    def _fake_save(rows_):
        saved.extend(rows_)
    def _fake_fetch(tk, start):
        return ohlc_for_ticker.get(tk, pd.DataFrame())
    with patch.object(ev, "_load_picks", return_value=rows), \
         patch.object(ev, "_save_picks", side_effect=_fake_save), \
         patch.object(ev, "_fetch_ohlc", side_effect=_fake_fetch), \
         patch.object(ev, "_add_spy_alpha", return_value=""), \
         patch.object(ev, "_add_sector_alpha", return_value=""), \
         patch.object(ev, "_journal_attach", return_value=None):
        # Force "today" deterministically. Use a subclass so strptime
        # and arithmetic still work (patching the whole module attr broke that).
        from datetime import datetime as _dt
        class _FrozenDT(_dt):
            @classmethod
            def now(cls, tz=None):
                return cls(2026, 5, 5, 12, 0, 0)
        with patch.object(ev, "datetime", _FrozenDT):
            counts = ev.evaluate_pending()
    return saved, counts


# ─────────────────── Tests ───────────────────
def test_day_pick_no_sl_tp_hit_closes_at_pick_date_close():
    """The MPWR-style case. Day pick, neither SL nor TP hit → day_close at Close."""
    rows = [_row(ticker="MPWR", entry=1583.48, sl=1545.16, tp=1647.35)]
    # Pick-date bar: Close 1600 (between SL and TP, neither hit)
    ohlc = {"MPWR": _bar("2026-05-02", o=1585, h=1610, l=1570, c=1600)}
    saved, _ = _run_evaluator(rows, ohlc)
    assert saved[0]["evaluation_status"] == "day_close", \
        f"expected 'day_close', got {saved[0]['evaluation_status']!r}"
    assert float(saved[0]["exit_price"]) == 1600.0
    assert saved[0]["evaluated_on"] == "2026-05-02"


def test_day_pick_sl_hit_intraday_still_marks_sl_hit():
    """If day-trade hits SL during the day, sl_hit wins (NOT day_close)."""
    rows = [_row(ticker="DAY1", entry=100, sl=95, tp=110)]
    # Pick-date bar: Low 94 → SL hit
    ohlc = {"DAY1": _bar("2026-05-02", o=99, h=101, l=94, c=96)}
    saved, _ = _run_evaluator(rows, ohlc)
    assert saved[0]["evaluation_status"] == "sl_hit"
    assert float(saved[0]["exit_price"]) == 95.0


def test_day_pick_tp_hit_intraday_still_marks_tp_hit():
    """If day-trade hits TP during the day, tp_hit wins (NOT day_close)."""
    rows = [_row(ticker="DAY2", entry=100, sl=95, tp=110)]
    # Pick-date bar: High 111 → TP hit
    ohlc = {"DAY2": _bar("2026-05-02", o=101, h=111, l=99, c=109)}
    saved, _ = _run_evaluator(rows, ohlc)
    assert saved[0]["evaluation_status"] == "tp_hit"
    assert float(saved[0]["exit_price"]) == 110.0


def test_swing_pick_no_hit_is_NOT_day_closed():
    """REGRESSION GUARD: swing pick with no SL/TP hit must stay open,
    NOT get force-closed. Only day-trades get the day_close treatment."""
    rows = [_row(ticker="SWG1", trade_type="swing",
                 entry=100, sl=95, tp=110)]
    ohlc = {"SWG1": _bar("2026-05-02", o=101, h=105, l=98, c=103)}
    saved, _ = _run_evaluator(rows, ohlc)
    assert saved[0]["evaluation_status"] == "pending", \
        "swing pick must NOT be force-closed by day-trade rule"


def test_day_close_row_has_all_required_columns():
    """day_close row must populate same required cols as tp_hit/sl_hit."""
    rows = [_row(ticker="MPWR", entry=1583.48, sl=1545.16, tp=1647.35)]
    ohlc = {"MPWR": _bar("2026-05-02", o=1585, h=1610, l=1570, c=1600)}
    saved, _ = _run_evaluator(rows, ohlc)
    r = saved[0]
    for col in ("evaluation_status", "evaluated_on", "exit_price",
                "actual_return_pct", "r_multiple"):
        assert r[col] not in ("", None), f"col {col!r} not populated"
    # Math sanity: 1600 entry-1583.48 = +16.52 → +1.04%
    assert float(r["actual_return_pct"]) == pytest.approx(1.04, abs=0.05)
    # r_multiple: (1600-1583.48) / (1583.48-1545.16) = 16.52/38.32 = 0.43
    assert float(r["r_multiple"]) == pytest.approx(0.43, abs=0.05)


def test_day_close_counted_in_counts_dict():
    """evaluate_pending() must report day_close in its return dict."""
    rows = [_row(ticker="MPWR", entry=1583.48, sl=1545.16, tp=1647.35)]
    ohlc = {"MPWR": _bar("2026-05-02", o=1585, h=1610, l=1570, c=1600)}
    _, counts = _run_evaluator(rows, ohlc)
    assert counts.get("day_close", 0) == 1, \
        f"counts must include day_close=1, got {counts}"
    assert counts["evaluated"] >= 1


def test_day_pick_on_weekend_uses_next_trading_bar():
    """Edge case (MPWR 2026-05-02 — Saturday): day-trade picked on a
    non-trading day must close at the FIRST trading bar at-or-after
    pick_date, NOT stay pending forever.

    The upstream bug (picking on weekends) is filed separately. This
    test guards the evaluator's robustness regardless of upstream."""
    rows = [_row(ticker="MPWR", pick_date="2026-05-02",   # Saturday
                 entry=1583.48, sl=1545.16, tp=1647.35)]
    # First trading bar is Monday 2026-05-04. Neither SL nor TP hit.
    ohlc = {"MPWR": _bar("2026-05-04", o=1590.47, h=1603.70, l=1552.84, c=1573.30)}
    saved, counts = _run_evaluator(rows, ohlc)
    actual = saved[0]["evaluation_status"]
    assert actual == "day_close", f"weekend day-pick must close, got {actual!r}"
    assert float(saved[0]["exit_price"]) == 1573.30
    assert saved[0]["evaluated_on"] == "2026-05-04", \
        "evaluated_on should be the actual trading bar date, not pick_date"
    assert counts["day_close"] == 1
