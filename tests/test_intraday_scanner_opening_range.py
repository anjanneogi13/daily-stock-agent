import json
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

def test_append_opening_range_observations_writes_jsonl(tmp_path):
    path = tmp_path / "opening_range_observations_2026-05-06.jsonl"
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
        "opening_range": {
            "start": "2026-05-06T09:30:00-04:00",
            "end": "2026-05-06T09:45:00-04:00",
            "high": 101.0,
            "low": 99.7,
            "width_pct": 1.3039,
            "volume": 3300,
        },
        "breakout_pct": 0.5941,
        "volume_ratio": 3.1818,
    }

    written = scanner.append_opening_range_observations(
        [candidate],
        path=path,
        now=datetime(2026, 5, 6, 14, 0, tzinfo=ET),
    )

    assert written == 1
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    assert len(rows) == 1
    row = rows[0]
    assert row["ticker"] == "NET"
    assert row["scanner"] == "opening_range"
    assert row["mode"] == "monitoring_only"
    assert row["watch_only"] is True
    assert row["entry_observe"] == 101.6
    assert row["stop_loss_observe"] == 99.7
    assert row["take_profit_observe"] == 104.45
    assert row["opening_range_high"] == 101.0
    assert row["source"] == "intraday_scanner"


def test_append_opening_range_observations_ignores_non_or_or_non_watch_only(tmp_path):
    path = tmp_path / "opening_range_observations_2026-05-06.jsonl"

    written = scanner.append_opening_range_observations([
        {"ticker": "AAPL", "scanner": "momentum", "watch_only": True},
        {"ticker": "MSFT", "scanner": "opening_range", "watch_only": False},
    ], path=path)

    assert written == 0
    assert not path.exists()
