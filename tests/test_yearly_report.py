"""T46 / Pillar 6: yearly report scaffold."""
from __future__ import annotations
import csv
from pathlib import Path
import pytest

from src import yearly_report as yr


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    csvp = tmp_path / "picks.csv"
    monkeypatch.setattr(yr, "PICKS", csvp)
    monkeypatch.setattr(yr, "REPORTS", tmp_path / "out")
    with csvp.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=[
            "pick_date","evaluation_status","r_multiple","alpha_pct"])
        w.writeheader()
        for d, st, r, a in [
            ("2026-01-15","tp_hit", 2.0,  1.5),
            ("2026-02-10","sl_hit",-1.0, -0.5),
            ("2026-03-05","tp_hit", 1.5,  0.8),
            ("2025-11-01","tp_hit", 3.0,  2.0),  # different year
        ]:
            w.writerow({"pick_date":d,"evaluation_status":st,
                        "r_multiple":r,"alpha_pct":a})
    return csvp


def test_build_report_filters_by_year(isolated):
    r = yr.build_report(2026)
    assert r["closed"] == 3
    assert r["wins"] == 2
    assert r["total_r"] == pytest.approx(2.5)


def test_build_report_handles_missing_csv(tmp_path, monkeypatch):
    monkeypatch.setattr(yr, "PICKS", tmp_path / "nope.csv")
    r = yr.build_report(2026)
    assert r["picks"] == 0


def test_format_markdown_includes_headers(isolated):
    md = yr.format_markdown(yr.build_report(2026))
    assert "Annual Report" in md
    assert "2026" in md
    assert "Win rate" in md


def test_main_writes_file(isolated, tmp_path):
    out = tmp_path / "yr.md"
    rc = yr.main(["--year","2026","--out",str(out)])
    assert rc == 0
    assert out.exists()
    assert "2026" in out.read_text()
