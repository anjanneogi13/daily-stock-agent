"""Bug #8/#10 (2026-05-05): audit sector benchmark fill-rate.

Sector-relative learning depends on sector_etf/sector_close at pick time and
sector exit fields after close. The partial fix needs a dashboard.
"""

import json
import subprocess

from scripts.audit_sector_fill_rate import (
    DATA_QUALITY_FLOOR,
    CLOSED_STATUSES,
    audit_rows,
    has_value,
)


def row(**kw):
    base = {
        "pick_date": "2026-05-05",
        "ticker": "NVDA",
        "trade_type": "swing",
        "evaluation_status": "pending",
        "sector_etf": "XLK",
        "sector_close": "100.0",
        "sector_close_at_exit": "",
        "sector_return_pct": "",
        "sector_alpha_pct": "",
    }
    base.update(kw)
    return base


def test_has_value_rejects_blank_none_and_nan():
    assert has_value("") is False
    assert has_value(None) is False
    assert has_value("None") is False
    assert has_value("nan") is False


def test_has_value_accepts_zero_and_text():
    assert has_value("0") is True
    assert has_value("0.0") is True
    assert has_value("XLK") is True


def test_audit_rows_measures_entry_fields_on_post_floor_rows():
    rows = [
        row(pick_date="2026-05-01", ticker="OLD", sector_etf="", sector_close=""),
        row(ticker="A", sector_etf="XLK", sector_close="100"),
        row(ticker="B", sector_etf="", sector_close=""),
    ]

    result = audit_rows(rows, floor="2026-05-02", warning_threshold=0.80)

    assert result["total_rows"] == 3
    assert result["post_floor_rows"] == 2
    assert result["fields"]["sector_etf"]["filled"] == 1
    assert result["fields"]["sector_etf"]["fill_rate"] == 0.5
    assert result["fields"]["sector_close"]["filled"] == 1
    assert result["fields"]["sector_close"]["fill_rate"] == 0.5
    assert result["warning"] is True
    assert result["missing_entry_tickers"] == ["B"]


def test_audit_rows_measures_exit_fields_on_closed_post_floor_rows_only():
    rows = [
        row(ticker="A", evaluation_status="pending", sector_close_at_exit="", sector_return_pct="", sector_alpha_pct=""),
        row(ticker="B", evaluation_status="tp_hit", sector_close_at_exit="110", sector_return_pct="10", sector_alpha_pct="1"),
        row(ticker="C", evaluation_status="sl_hit", sector_close_at_exit="", sector_return_pct="", sector_alpha_pct=""),
    ]

    result = audit_rows(rows, floor=DATA_QUALITY_FLOOR, warning_threshold=0.80)

    assert result["closed_post_floor_rows"] == 2
    assert result["fields"]["sector_close_at_exit"]["denominator"] == 2
    assert result["fields"]["sector_close_at_exit"]["filled"] == 1
    assert result["fields"]["sector_close_at_exit"]["fill_rate"] == 0.5
    assert result["missing_exit_tickers"] == ["C"]


def test_cli_json_outputs_sector_fields():
    out = subprocess.check_output(
        ["python", "scripts/audit_sector_fill_rate.py", "--json"],
        text=True,
    )
    data = json.loads(out)

    assert "post_floor_rows" in data
    assert "closed_post_floor_rows" in data
    assert "fields" in data
    assert "sector_etf" in data["fields"]
    assert "sector_alpha_pct" in data["fields"]
