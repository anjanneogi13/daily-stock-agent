"""Bug #7 (2026-05-05): no future day picks on non-trading days.

The evaluator can robustly close historical weekend day-picks, but the picker
should not emit new trade_type=day picks when the US market is closed.
"""

from main import _safe_trade_type_for_pick


DAYLIKE_SCORES = {
    "momentum": 0.90,
    "volume": 0.90,
    "trend": 0.70,
}


def test_safe_trade_type_allows_day_on_trading_day():
    assert _safe_trade_type_for_pick(DAYLIKE_SCORES, pick_date="2026-05-06") == "day"


def test_safe_trade_type_downgrades_day_on_weekend():
    assert _safe_trade_type_for_pick(DAYLIKE_SCORES, pick_date="2026-05-02") == "swing"


def test_safe_trade_type_downgrades_day_on_market_holiday():
    assert _safe_trade_type_for_pick(DAYLIKE_SCORES, pick_date="2026-05-25") == "swing"
