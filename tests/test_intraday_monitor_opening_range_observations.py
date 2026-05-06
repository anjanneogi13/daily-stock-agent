import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

import intraday_monitor as monitor


def test_intraday_monitor_records_opening_range_observations(tmp_path, monkeypatch):
    candidate = {
        "ticker": "NET",
        "price": 101.6,
        "score": 80,
        "entry": 101.6,
        "sl": 99.7,
        "tp": 104.45,
        "reason": "opening-range breakout",
        "watch_only": True,
        "mode": "monitoring_only",
        "scanner": "opening_range",
    }
    calls = []

    monkeypatch.setattr(monitor, "load_todays_picks", lambda: [{"ticker": "AAPL"}])
    monkeypatch.setattr(monitor, "load_sent_alerts", lambda: set())
    monkeypatch.setattr(monitor, "monitor_existing_picks", lambda picks, sent_alerts: [])
    monkeypatch.setattr(
        monitor,
        "scan_for_new_opportunities",
        lambda exclude, sent_alerts, max_results=3: [candidate],
    )
    monkeypatch.setattr(
        monitor,
        "append_opening_range_observations",
        lambda opportunities: calls.append(opportunities) or 1,
    )
    monkeypatch.setattr(monitor, "save_sent_alerts", lambda sent_alerts: None)
    monkeypatch.setattr(monitor, "OUT_FILE", tmp_path / "intraday_alert.md")

    monitor.main()

    assert calls == [[candidate]]
    assert monitor.OUT_FILE.exists()
    assert "WATCH ONLY" in monitor.OUT_FILE.read_text()
