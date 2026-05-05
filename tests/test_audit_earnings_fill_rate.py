"""Bug #11 (2026-05-05): audit earnings fill-rate.

days_to_earnings was historically sparse. Before changing scoring logic,
we need an explicit audit dashboard that measures fill rate on post-floor rows.
"""

import json
import subprocess

from scripts.audit_earnings_fill_rate import (
    DATA_QUALITY_FLOOR,
    audit_rows,
    has_days_to_earnings,
)


def row(**kw):
    base = {
        "pick_date": "2026-05-05",
        "ticker": "NVDA",
        "trade_type": "swing",
        "days_to_earnings": "21",
    }
    base.update(kw)
    return base


def test_has_days_to_earnings_accepts_numeric_zero_and_positive_values():
    assert has_days_to_earnings(row(days_to_earnings="0")) is True
    assert has_days_to_earnings(row(days_to_earnings="12")) is True
    assert has_days_to_earnings(row(days_to_earnings=12)) is True


def test_has_days_to_earnings_rejects_blank_none_and_invalid_values():
    assert has_days_to_earnings(row(days_to_earnings="")) is False
    assert has_days_to_earnings(row(days_to_earnings=None)) is False
    assert has_days_to_earnings(row(days_to_earnings="None")) is False
    assert has_days_to_earnings(row(days_to_earnings="abc")) is False


def test_audit_rows_uses_post_floor_and_computes_fill_rate():
    rows = [
        row(pick_date="2026-05-01", ticker="OLD", days_to_earnings="5"),
        row(pick_date="2026-05-05", ticker="A", trade_type="day", days_to_earnings="7"),
        row(pick_date="2026-05-05", ticker="B", trade_type="day", days_to_earnings=""),
        row(pick_date="2026-05-05", ticker="C", trade_type="swing", days_to_earnings="30"),
        row(pick_date="2026-05-05", ticker="D", trade_type="swing", days_to_earnings="None"),
    ]

    result = audit_rows(rows, floor="2026-05-02", warning_threshold=0.80)

    assert result["floor"] == "2026-05-02"
    assert result["total_rows"] == 5
    assert result["post_floor_rows"] == 4
    assert result["filled_rows"] == 2
    assert result["missing_rows"] == 2
    assert result["fill_rate"] == 0.5
    assert result["warning"] is True
    assert result["missing_tickers"] == ["B", "D"]


def test_audit_rows_breaks_down_by_trade_type():
    rows = [
        row(trade_type="day", days_to_earnings="7"),
        row(trade_type="day", days_to_earnings=""),
        row(trade_type="swing", days_to_earnings="30"),
    ]

    result = audit_rows(rows, floor=DATA_QUALITY_FLOOR)
    by_type = result["by_trade_type"]

    assert by_type["day"]["rows"] == 2
    assert by_type["day"]["filled"] == 1
    assert by_type["day"]["fill_rate"] == 0.5
    assert by_type["swing"]["rows"] == 1
    assert by_type["swing"]["filled"] == 1
    assert by_type["swing"]["fill_rate"] == 1.0


def test_cli_json_outputs_fill_rate_fields():
    out = subprocess.check_output(
        ["python", "scripts/audit_earnings_fill_rate.py", "--json"],
        text=True,
    )
    data = json.loads(out)

    assert "post_floor_rows" in data
    assert "filled_rows" in data
    assert "fill_rate" in data
    assert "missing_tickers" in data
    assert "by_trade_type" in data
