"""Bug #8/#10: sector alpha helpers repair legacy missing sector fields."""

import pytest

from src import pick_evaluator as pe


def test_add_sector_alpha_fills_anchor_from_tag(monkeypatch):
    closes = {
        ("SOXX", "2026-05-02"): 465.75,
        ("SOXX", "2026-05-04"): 462.06,
    }
    monkeypatch.setattr(pe, "_etf_close_on", lambda etf, dt: closes.get((etf, dt)))

    row = {
        "ticker": "MPWR",
        "pick_date": "2026-05-02",
        "tag": "SEMI / AI",
        "sector_etf": "",
        "sector_close": "",
    }

    exit_close = pe._add_sector_alpha(row, "2026-05-04", -0.64)

    assert row["sector_etf"] == "SOXX"
    assert row["sector_close"] == "465.75"
    assert exit_close == "462.06"
    assert row["sector_return_pct"] == pytest.approx(-0.79, abs=0.01)
    assert row["sector_alpha_pct"] == pytest.approx(0.15, abs=0.01)


def test_add_sector_alpha_preserves_existing_spy_anchor(monkeypatch):
    closes = {("SPY", "2026-05-04"): 718.01}
    monkeypatch.setattr(pe, "_etf_close_on", lambda etf, dt: closes.get((etf, dt)))

    row = {
        "ticker": "A",
        "pick_date": "2026-05-04",
        "tag": "",
        "sector_etf": "SPY",
        "sector_close": "",
    }

    exit_close = pe._add_sector_alpha(row, "2026-05-04", -1.89)

    assert row["sector_etf"] == "SPY"
    assert row["sector_close"] == "718.01"
    assert exit_close == "718.01"
    assert row["sector_return_pct"] == 0.0
    assert row["sector_alpha_pct"] == -1.89


def test_sector_anchor_falls_back_to_spy_when_resolved_etf_missing(monkeypatch):
    closes = {
        ("SOXX", "2026-05-02"): None,
        ("SPY", "2026-05-02"): 720.65,
    }
    monkeypatch.setattr(pe, "_etf_close_on", lambda etf, dt: closes.get((etf, dt)))

    row = {
        "ticker": "TSM",
        "pick_date": "2026-05-02",
        "tag": "SEMI / AI",
        "sector_etf": "",
        "sector_close": "",
    }

    etf, close = pe._ensure_sector_benchmark_anchor(row)

    assert etf == "SPY"
    assert close == 720.65
    assert row["sector_etf"] == "SPY"
    assert row["sector_close"] == "720.65"
