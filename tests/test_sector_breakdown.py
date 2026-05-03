"""T28: per-sector P&L breakdown for weekly review."""
import pytest
from src.sector_breakdown import (
    sector_breakdown, format_sector_panel, _verdict, _enrich_with_sector_etf,
)


def _pick(ticker, tag, status, ret, r_mult, sector=None):
    # Default sector mirrors tag so resolve_sector_etf maps to a real ETF
    return {
        "ticker": ticker, "tag": tag, "sector": sector or tag,
        "evaluation_status": status,
        "actual_return_pct": str(ret),
        "r_multiple": str(r_mult),
        "alpha_pct": "0",
    }


class TestVerdict:
    def test_strong(self):
        assert "🌟" in _verdict(0.7, 2.0)
    def test_ok(self):
        assert "🟢" in _verdict(0.55, 0.8)
    def test_mixed(self):
        assert "🟡" in _verdict(0.40, 0.2)
    def test_weak(self):
        assert "🟠" in _verdict(0.30, -1.0)
    def test_bleeding(self):
        assert "🔴" in _verdict(0.10, -3.5)
    def test_none(self):
        assert "N/A" in _verdict(0.0, None)


class TestEnrich:
    def test_resolves_sector_etf_from_tag(self):
        picks = [_pick("NVDA", "Technology/AI", "tp_hit", 5.0, 1.5)]
        out = _enrich_with_sector_etf(picks)
        assert out[0]["sector_etf"]  # set to something

    def test_does_not_overwrite(self):
        picks = [{"sector_etf": "CUSTOM", "tag": "Technology"}]
        out = _enrich_with_sector_etf(picks)
        assert out[0]["sector_etf"] == "CUSTOM"

    def test_falls_back_to_spy(self):
        picks = [_pick("X", "", "tp_hit", 1.0, 0.5)]
        out = _enrich_with_sector_etf(picks)
        assert out[0]["sector_etf"] == "SPY"


class TestSectorBreakdown:
    def test_empty_returns_empty(self):
        assert sector_breakdown([]) == []

    def test_groups_by_sector_etf(self):
        picks = [
            _pick("NVDA", "Technology", "tp_hit", 5.0,  1.5),
            _pick("AMD",  "Technology", "tp_hit", 4.0,  1.2),
            _pick("XOM",  "Energy",     "sl_hit", -2.0, -1.0),
        ]
        rows = sector_breakdown(picks)
        sectors = [r["sector"] for r in rows]
        assert len(rows) == 2
        # Bleeding sector first
        assert rows[0]["total_r"] < 0

    def test_verdict_attached(self):
        picks = [_pick("NVDA", "Technology", "tp_hit", 5.0, 2.0),
                 _pick("AMD",  "Technology", "tp_hit", 5.0, 2.0)]
        rows = sector_breakdown(picks)
        assert "🌟" in rows[0]["verdict"] or "🟢" in rows[0]["verdict"]

    def test_worst_first_ordering(self):
        picks = [
            _pick("NVDA", "Technology", "tp_hit",  5.0,  1.5),
            _pick("XOM",  "Energy",     "sl_hit", -3.0, -1.5),
            _pick("JPM",  "Financials", "tp_hit",  2.0,  1.0),
        ]
        rows = sector_breakdown(picks)
        rs = [r["total_r"] for r in rows]
        assert rs == sorted(rs)  # ascending = worst first


class TestFormatSectorPanel:
    def test_empty_returns_empty_string(self):
        assert format_sector_panel([]) == ""

    def test_table_has_header(self):
        rows = [{"sector": "XLK", "n": 3, "win_rate": 0.66,
                 "avg_r": 0.8, "total_r": 2.4, "verdict": "🌟 STRONG"}]
        s = format_sector_panel(rows)
        assert "Sector Breakdown" in s
        assert "XLK" in s
        assert "🌟" in s

    def test_handles_none_avg_r(self):
        rows = [{"sector": "XLE", "n": 1, "win_rate": 0.0,
                 "avg_r": None, "total_r": None, "verdict": "⚪ N/A"}]
        s = format_sector_panel(rows)
        assert "—" in s
