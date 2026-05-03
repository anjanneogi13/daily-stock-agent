"""Tests for sector_etf dimension + sector_alpha aggregation in strategy_breakdown."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.strategy_breakdown import breakdown_by, format_breakdown_text


def _row(**kw):
    base = {
        "evaluation_status": "tp_hit",
        "actual_return_pct": "5.0",
        "r_multiple": "1.5",
        "alpha_pct": "2.0",
        "sector_alpha_pct": "1.0",
        "trade_type": "swing",
        "tag": "SEMI",
        "regime": "bull",
        "sector_etf": "SOXX",
    }
    base.update(kw)
    return base


def test_breakdown_by_sector_etf():
    rows = [_row(sector_etf="SOXX"), _row(sector_etf="SOXX"), _row(sector_etf="XLV")]
    out = breakdown_by("sector_etf", rows)
    by = {r["group"]: r for r in out}
    assert "SOXX" in by and "XLV" in by
    assert by["SOXX"]["n"] == 2
    assert by["XLV"]["n"] == 1


def test_avg_sector_alpha_aggregated():
    rows = [_row(sector_alpha_pct="3.0"), _row(sector_alpha_pct="-1.0")]
    out = breakdown_by("trade_type", rows)
    assert out[0]["avg_sector_alpha_pct"] == 1.0  # (3 + -1) / 2


def test_missing_sector_alpha_handled():
    rows = [_row(sector_alpha_pct=""), _row(sector_alpha_pct=None)]
    out = breakdown_by("trade_type", rows)
    assert out[0]["avg_sector_alpha_pct"] is None


def test_format_includes_sector_alpha_column():
    rows = [_row(sector_alpha_pct="1.5")]
    bd = breakdown_by("trade_type", rows)
    text = format_breakdown_text("trade_type", bd)
    assert "αSec%" in text
    assert "αSPY%" in text


def test_empty_handled():
    out = breakdown_by("sector_etf", [])
    assert out == []
