import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

import intraday_scanner


ET = ZoneInfo("America/New_York")


def test_new_opportunity_window_open_before_cutoff():
    assert intraday_scanner.new_opportunity_window_open(
        now=datetime(2026, 5, 7, 15, 14, tzinfo=ET)
    )


def test_new_opportunity_window_closed_at_cutoff():
    assert not intraday_scanner.new_opportunity_window_open(
        now=datetime(2026, 5, 7, 15, 15, tzinfo=ET)
    )


def test_scan_for_new_opportunities_suppresses_near_close(monkeypatch):
    calls = []

    def fake_opening_range(*args, **kwargs):
        calls.append("opening_range")
        return [{
            "ticker": "UNH",
            "price": 369.65,
            "score": 75.0,
            "entry": 369.65,
            "sl": 365.63,
            "tp": 375.68,
            "reason": "late opening-range breakout",
            "watch_only": True,
            "mode": "monitoring_only",
            "scanner": "opening_range",
        }]

    monkeypatch.setattr(intraday_scanner, "scan_opening_range_opportunities", fake_opening_range)

    out = intraday_scanner.scan_for_new_opportunities(
        exclude=set(),
        sent_alerts=set(),
        max_results=3,
        now=datetime(2026, 5, 7, 15, 45, tzinfo=ET),
    )

    assert out == []
    assert calls == []
