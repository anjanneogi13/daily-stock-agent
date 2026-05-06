from datetime import datetime
from zoneinfo import ZoneInfo
from unittest.mock import patch

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

import intraday_scanner as scanner
from intraday_monitor import build_message


ET = ZoneInfo("America/New_York")


def bar(h, m, high, low, close, volume=1000):
    return {
        "ts": datetime(2026, 5, 6, h, m, tzinfo=ET),
        "open": close,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
    }


def breakout_bars():
    return [
        bar(9, 30, 100.4, 99.7, 100.1, 1000),
        bar(9, 35, 100.8, 99.9, 100.6, 1200),
        bar(9, 40, 101.0, 100.2, 100.9, 1100),
        bar(9, 45, 101.8, 101.0, 101.6, 3500),
    ]


def test_scan_opening_range_opportunities_returns_watch_only_candidate():
    sent = set()

    with patch.object(scanner, "load_watchlist", return_value=["NET"]), \
         patch.object(scanner, "get_live_quote", return_value={
             "price": 101.6,
             "prev_close": 100.0,
             "change_pct": 1.6,
             "vol_ratio": 2.0,
         }), \
         patch.object(scanner, "fetch_opening_range_bars", return_value=breakout_bars()):
        out = scanner.scan_opening_range_opportunities(exclude=set(), sent_alerts=sent)

    assert len(out) == 1
    cand = out[0]
    assert cand["ticker"] == "NET"
    assert cand["watch_only"] is True
    assert cand["mode"] == "monitoring_only"
    assert cand["scanner"] == "opening_range"
    assert "opening-range breakout" in cand["reason"]
    assert sent, "opening-range candidate should be deduped"


def test_scan_for_new_opportunities_prioritizes_opening_range_before_legacy_momentum():
    with patch.object(scanner, "scan_opening_range_opportunities", return_value=[{
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
    }]):
        out = scanner.scan_for_new_opportunities(exclude=set(), sent_alerts=set(), max_results=3)

    assert out, "opening-range candidate should be present"
    assert out[0]["scanner"] == "opening_range"
    assert out[0]["watch_only"] is True
    assert len(out) <= 3
    assert all(o.get("watch_only") is True for o in out)


def test_intraday_message_labels_new_opportunities_watch_only():
    msg = build_message([], [{
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
    }])

    assert "WATCH ONLY" in msg
    assert "Monitoring-only. Do not treat as a buy instruction." in msg
    assert "Scanner: opening_range" in msg
    assert "Observe levels:" in msg
