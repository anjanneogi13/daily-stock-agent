"""T46 / Pillar 6: per-sector P&L tests."""
from __future__ import annotations
import pytest

from src import sector_pnl as sp


def test_per_sector_pnl_empty():
    assert sp.per_sector_pnl([]) == []


def test_per_sector_pnl_groups_correctly():
    picks = [
        {"sector":"SEMI","r_multiple":2.0},
        {"sector":"SEMI","r_multiple":-1.0},
        {"sector":"BANK","r_multiple":1.5},
    ]
    rows = sp.per_sector_pnl(picks)
    assert len(rows) == 2
    semi = next(r for r in rows if r["sector"]=="SEMI")
    assert semi["trades"] == 2
    assert semi["total_r"] == pytest.approx(1.0)
    assert semi["wins"] == 1


def test_per_sector_pnl_falls_back_to_tag():
    rows = sp.per_sector_pnl([{"tag":"SEMI / AI","r_multiple":2.0}])
    assert rows[0]["sector"] == "SEMI"


def test_per_sector_pnl_verdicts():
    rows = sp.per_sector_pnl([
        {"sector":"WIN","r_multiple":3.0},
        {"sector":"LOSS","r_multiple":-2.0},
        {"sector":"FLAT","r_multiple":0.5},
    ])
    by = {r["sector"]: r["verdict"] for r in rows}
    assert "PROFITABLE" in by["WIN"]
    assert "LOSING"     in by["LOSS"]
    assert "FLAT"       in by["FLAT"]


def test_format_table_includes_headers():
    rows = sp.per_sector_pnl([{"sector":"X","r_multiple":1.0}])
    out = sp.format_table(rows)
    assert "Sector" in out
    assert "Total R" in out
    assert "X" in out


def test_per_sector_pnl_skips_no_r():
    rows = sp.per_sector_pnl([
        {"sector":"X"},  # no r_multiple
        {"sector":"Y","r_multiple":1.0},
    ])
    assert len(rows) == 1
    assert rows[0]["sector"] == "Y"
