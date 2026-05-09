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
        out = scanner.scan_opening_range_opportunities(exclude=set(), sent_alerts=sent, now=datetime(2026, 5, 6, 10, 0, tzinfo=ET))

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
        out = scanner.scan_for_new_opportunities(
            exclude=set(),
            sent_alerts=set(),
            max_results=3,
            now=datetime(2026, 5, 6, 10, 0, tzinfo=ET),
        )

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
    assert "Reference levels: Observed $101.60" in msg
    assert "Observe levels: Entry" not in msg

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


def test_opening_range_run_status_is_monitoring_only(tmp_path):
    path = tmp_path / "opening_range_run_status_2026-05-06.jsonl"

    out = scanner.append_opening_range_run_status(
        event="monitor_completed",
        result="no_alerts",
        reason="scanner ran with no qualifying opening-range candidates",
        candidate_count=0,
        alert_count=0,
        observation_count=0,
        telegram_sent=False,
        path=path,
        now=datetime(2026, 5, 6, 10, 0, tzinfo=ET),
    )

    assert out == path
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    assert len(rows) == 1
    row = rows[0]
    assert row["date"] == "2026-05-06"
    assert row["workflow"] == "intraday-monitor"
    assert row["scanner"] == "opening_range"
    assert row["event"] == "monitor_completed"
    assert row["result"] == "no_alerts"
    assert row["candidate_count"] == 0
    assert row["alert_count"] == 0
    assert row["observation_count"] == 0
    assert row["telegram_sent"] is False
    assert row["watch_only"] is True
    assert row["mode"] == "monitoring_only"
    assert row["paper_trading_enabled"] is False
    assert row["live_trading_enabled"] is False


def test_append_opening_range_observations_ignores_non_or_or_non_watch_only(tmp_path):
    path = tmp_path / "opening_range_observations_2026-05-06.jsonl"

    written = scanner.append_opening_range_observations([
        {"ticker": "AAPL", "scanner": "momentum", "watch_only": True},
        {"ticker": "MSFT", "scanner": "opening_range", "watch_only": False},
    ], path=path)

    assert written == 0
    assert not path.exists()

def test_append_intraday_momentum_observations_writes_jsonl(tmp_path):
    path = tmp_path / "intraday_momentum_observations_2026-05-06.jsonl"
    candidate = {
        "ticker": "SMCI",
        "price": 32.15,
        "score": 75,
        "entry": 32.15,
        "sl": 31.67,
        "tp": 33.11,
        "reason": "+15.5% on 1.8× volume",
        "watch_only": True,
        "mode": "monitoring_only",
        "scanner": "momentum",
    }

    written = scanner.append_intraday_momentum_observations(
        [candidate],
        path=path,
        now=datetime(2026, 5, 6, 11, 38, tzinfo=ET),
    )

    assert written == 1
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    assert len(rows) == 1
    row = rows[0]
    assert row["date"] == "2026-05-06"
    assert row["ticker"] == "SMCI"
    assert row["scanner"] == "momentum"
    assert row["mode"] == "monitoring_only"
    assert row["watch_only"] is True
    assert row["entry_observe"] == 32.15
    assert row["stop_loss_observe"] == 31.67
    assert row["take_profit_observe"] == 33.11
    assert row["paper_trading_enabled"] is False
    assert row["live_trading_enabled"] is False
    assert row["ready_for_paper_trading"] is False


def test_append_intraday_momentum_observations_ignores_non_momentum_or_non_watch_only(tmp_path):
    path = tmp_path / "intraday_momentum_observations_2026-05-06.jsonl"

    written = scanner.append_intraday_momentum_observations([
        {"ticker": "NET", "scanner": "opening_range", "watch_only": True},
        {"ticker": "AAPL", "scanner": "momentum", "watch_only": False},
    ], path=path)

    assert written == 0
    assert not path.exists()

def test_write_opening_range_bar_artifact_is_monitoring_only(tmp_path):
    path = tmp_path / "opening_range_bars" / "2026-05-06" / "NET.jsonl"

    out = scanner.write_opening_range_bar_artifact(
        "net",
        breakout_bars(),
        path=path,
        now=datetime(2026, 5, 6, 10, 0, tzinfo=ET),
    )

    assert out == path
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    assert len(rows) == 4
    first = rows[0]
    assert first["date"] == "2026-05-06"
    assert first["ticker"] == "NET"
    assert first["artifact"] == "opening_range_bar"
    assert first["scanner"] == "opening_range"
    assert first["mode"] == "monitoring_only"
    assert first["watch_only"] is True
    assert first["paper_trading_enabled"] is False
    assert first["live_trading_enabled"] is False
    assert first["official_pick_stats_mutated"] is False
    assert first["high"] == 100.4
    assert first["low"] == 99.7
    assert first["close"] == 100.1
    assert first["volume"] == 1000.0


def test_append_opening_range_observations_also_writes_candidate_bars(tmp_path, monkeypatch):
    observation_path = tmp_path / "opening_range_observations_2026-05-06.jsonl"
    bars_path = tmp_path / "opening_range_bars" / "2026-05-06" / "NET.jsonl"

    monkeypatch.setattr(scanner, "opening_range_bar_path", lambda ticker, today=None: bars_path)

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
        "_opening_range_bars": breakout_bars(),
    }

    written = scanner.append_opening_range_observations(
        [candidate],
        path=observation_path,
        now=datetime(2026, 5, 6, 10, 0, tzinfo=ET),
    )

    assert written == 1
    assert observation_path.exists()
    assert bars_path.exists()

    observation = json.loads(observation_path.read_text().splitlines()[0])
    assert "_opening_range_bars" not in observation

    bars = [json.loads(line) for line in bars_path.read_text().splitlines()]
    assert len(bars) == 4
    assert {row["ticker"] for row in bars} == {"NET"}
    assert all(row["mode"] == "monitoring_only" for row in bars)
    assert all(row["watch_only"] is True for row in bars)

def test_scan_opening_range_opportunities_skips_stale_session_bars():
    sent = set()

    with patch.object(scanner, "load_watchlist", return_value=["NET"]), \
         patch.object(scanner, "get_live_quote", return_value={
             "price": 101.6,
             "prev_close": 100.0,
             "change_pct": 1.6,
             "vol_ratio": 2.0,
         }), \
         patch.object(scanner, "fetch_opening_range_bars", return_value=breakout_bars()):
        out = scanner.scan_opening_range_opportunities(
            exclude=set(),
            sent_alerts=sent,
            now=datetime(2026, 5, 7, 8, 50, tzinfo=ET),
        )

    assert out == []
    assert sent == set()

def test_opening_range_bar_artifact_merges_existing_rows_without_duplicates(tmp_path):
    path = tmp_path / "opening_range_bars" / "2026-05-06" / "MERGE.jsonl"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({
        "ticker": "MERGE",
        "ts": "2026-05-06T09:30:00-04:00",
        "timestamp_utc": "2026-05-06T13:30:00+00:00",
        "open": 100,
        "high": 101,
        "low": 99,
        "close": 100.5,
        "volume": 1000,
    }) + "\n")

    bars = [
        {
            "ts": datetime(2026, 5, 6, 9, 30, tzinfo=ET),
            "open": 100,
            "high": 101,
            "low": 99,
            "close": 100.5,
            "volume": 1000,
        },
        {
            "ts": datetime(2026, 5, 6, 9, 35, tzinfo=ET),
            "open": 100.5,
            "high": 102,
            "low": 100,
            "close": 101.5,
            "volume": 1200,
        },
    ]

    out = scanner.write_opening_range_bar_artifact(
        "MERGE",
        bars,
        path=path,
        now=datetime(2026, 5, 6, 10, 0, tzinfo=ET),
    )

    assert out == path
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    assert len(rows) == 2
    assert [r["ts"] for r in rows] == [
        "2026-05-06T09:30:00-04:00",
        "2026-05-06T09:35:00-04:00",
    ]


def test_refresh_opening_range_bar_artifacts_for_existing_observations(tmp_path, monkeypatch):
    obs_path = tmp_path / "opening_range_observations_2026-05-06.jsonl"
    obs_path.write_text(json.dumps({
        "ticker": "KEEP",
        "scanner": "opening_range",
        "watch_only": True,
        "ts": "2026-05-06T14:00:00+00:00",
    }) + "\n")

    def fake_bar_path(ticker, today=None):
        return tmp_path / "opening_range_bars" / (today or "2026-05-06") / f"{ticker}.jsonl"

    monkeypatch.setattr(scanner, "opening_range_bar_path", fake_bar_path)

    def fake_fetcher(ticker):
        assert ticker == "KEEP"
        return [
            {
                "ts": datetime(2026, 5, 6, 9, 30, tzinfo=ET),
                "open": 100,
                "high": 101,
                "low": 99,
                "close": 100.5,
                "volume": 1000,
            },
            {
                "ts": datetime(2026, 5, 6, 10, 5, tzinfo=ET),
                "open": 101,
                "high": 103,
                "low": 100.8,
                "close": 102,
                "volume": 1500,
            },
        ]

    summary = scanner.refresh_opening_range_bar_artifacts_for_observations(
        observation_path=obs_path,
        today="2026-05-06",
        now=datetime(2026, 5, 6, 10, 10, tzinfo=ET),
        fetcher=fake_fetcher,
    )

    assert summary["observe_only"] is True
    assert summary["production_scoring_effect"] is False
    assert summary["ticker_count"] == 1
    assert summary["refreshed_count"] == 1
    assert summary["ticker_status"]["KEEP"]["status"] == "refreshed"

    bar_path = tmp_path / "opening_range_bars" / "2026-05-06" / "KEEP.jsonl"
    rows = [json.loads(line) for line in bar_path.read_text().splitlines()]
    assert len(rows) == 2
    assert rows[-1]["ts"] == "2026-05-06T10:05:00-04:00"


def test_refresh_opening_range_bar_artifacts_reports_stale_session(tmp_path, monkeypatch):
    obs_path = tmp_path / "opening_range_observations_2026-05-06.jsonl"
    obs_path.write_text(json.dumps({
        "ticker": "STALE",
        "scanner": "opening_range",
        "watch_only": True,
        "ts": "2026-05-06T14:00:00+00:00",
    }) + "\n")

    def fake_bar_path(ticker, today=None):
        return tmp_path / "opening_range_bars" / (today or "2026-05-06") / f"{ticker}.jsonl"

    monkeypatch.setattr(scanner, "opening_range_bar_path", fake_bar_path)

    def stale_fetcher(_ticker):
        return [
            {
                "ts": datetime(2026, 5, 5, 9, 30, tzinfo=ET),
                "open": 100,
                "high": 101,
                "low": 99,
                "close": 100.5,
                "volume": 1000,
            }
        ]

    summary = scanner.refresh_opening_range_bar_artifacts_for_observations(
        observation_path=obs_path,
        today="2026-05-06",
        now=datetime(2026, 5, 6, 10, 10, tzinfo=ET),
        fetcher=stale_fetcher,
    )

    assert summary["ticker_count"] == 1
    assert summary["refreshed_count"] == 0
    assert summary["skipped_count"] == 1
    assert summary["ticker_status"]["STALE"]["status"] == "not_refreshed_stale_session"
    assert not (tmp_path / "opening_range_bars" / "2026-05-06" / "STALE.jsonl").exists()
