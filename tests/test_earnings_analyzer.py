"""Coverage for src.earnings_analyzer without real network calls."""

import json
import os
import time
from datetime import datetime, timedelta

from src import earnings_analyzer as ea


def test_cached_get_returns_fresh_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(ea, "_CACHE_DIR", tmp_path)

    path = tmp_path / "AAPL_earnings.json"
    path.write_text(json.dumps([{"actual": 1.2}]))

    assert ea._cached_get("AAPL", "earnings") == [{"actual": 1.2}]


def test_cached_get_ignores_stale_or_corrupt_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(ea, "_CACHE_DIR", tmp_path)

    stale = tmp_path / "AAPL_earnings.json"
    stale.write_text(json.dumps([{"actual": 1.2}]))
    old = time.time() - (ea._CACHE_TTL.total_seconds() + 60)
    os.utime(stale, (old, old))

    corrupt = tmp_path / "MSFT_earnings.json"
    corrupt.write_text("{not-json")

    assert ea._cached_get("AAPL", "earnings") is None
    assert ea._cached_get("MSFT", "earnings") is None


def test_cache_put_writes_json(tmp_path, monkeypatch):
    monkeypatch.setattr(ea, "_CACHE_DIR", tmp_path)

    ea._cache_put("NVDA", "recs", [{"buy": 3}])

    assert json.loads((tmp_path / "NVDA_recs.json").read_text()) == [{"buy": 3}]


def test_fetch_earnings_history_returns_empty_without_key(monkeypatch, tmp_path):
    monkeypatch.setattr(ea, "_CACHE_DIR", tmp_path)
    monkeypatch.setattr(ea, "_KEY", "")

    called = {"requests": False}

    def fake_get(*args, **kwargs):
        called["requests"] = True
        raise AssertionError("should not call requests without key")

    monkeypatch.setattr(ea.requests, "get", fake_get)

    assert ea.fetch_earnings_history("AAPL") == []
    assert called["requests"] is False


def test_fetch_earnings_history_caches_successful_response(monkeypatch, tmp_path):
    monkeypatch.setattr(ea, "_CACHE_DIR", tmp_path)
    monkeypatch.setattr(ea, "_KEY", "token")

    class Response:
        status_code = 200

        def json(self):
            return [{"actual": 1.2, "estimate": 1.0}]

    calls = []

    def fake_get(url, params=None, timeout=15):
        calls.append((url, params, timeout))
        return Response()

    monkeypatch.setattr(ea.requests, "get", fake_get)

    result = ea.fetch_earnings_history("AAPL")

    assert result == [{"actual": 1.2, "estimate": 1.0}]
    assert calls[0][1]["symbol"] == "AAPL"
    assert calls[0][1]["limit"] == 8
    assert json.loads((tmp_path / "AAPL_earnings.json").read_text()) == result


def test_fetch_recommendations_handles_non_200_and_exceptions(monkeypatch, tmp_path):
    monkeypatch.setattr(ea, "_CACHE_DIR", tmp_path)
    monkeypatch.setattr(ea, "_KEY", "token")

    class Response:
        status_code = 500

        def json(self):
            raise AssertionError("json should not be read on non-200")

    monkeypatch.setattr(ea.requests, "get", lambda *a, **k: Response())
    assert ea.fetch_recommendations("AAPL") == []

    monkeypatch.setattr(ea.requests, "get", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")))
    assert ea.fetch_recommendations("AAPL") == []


def test_analyze_earnings_defaults_when_no_data(monkeypatch):
    monkeypatch.setattr(ea, "fetch_earnings_history", lambda ticker: [])
    monkeypatch.setattr(ea, "fetch_recommendations", lambda ticker: [])

    result = ea.analyze_earnings("EMPTY")

    assert result["earnings_quality"] == 0.5
    assert result["quarters_analyzed"] == 0
    assert result["beat_rate"] is None
    assert result["analyst_buy_pct"] is None
    assert result["rec_trend"] is None


def test_analyze_earnings_computes_quality_metrics(monkeypatch):
    earnings = [
        {"actual": 1.20, "estimate": 1.00},
        {"actual": 1.10, "estimate": 1.00},
        {"actual": 1.00, "estimate": 1.00},
        {"actual": 0.90, "estimate": 1.00},
        {"actual": 0.80, "estimate": 0.70},
        {"actual": None, "estimate": 1.00},  # ignored
    ]
    recs = [
        {"strongBuy": 6, "buy": 4, "hold": 2, "sell": 0, "strongSell": 0},
        {"strongBuy": 4, "buy": 4, "hold": 4, "sell": 0, "strongSell": 0},
        {"strongBuy": 2, "buy": 3, "hold": 7, "sell": 0, "strongSell": 0},
    ]

    monkeypatch.setattr(ea, "fetch_earnings_history", lambda ticker: earnings)
    monkeypatch.setattr(ea, "fetch_recommendations", lambda ticker: recs)

    result = ea.analyze_earnings("AAPL")

    assert result["quarters_analyzed"] == 5
    assert result["beat_rate"] == 0.6
    assert result["avg_surprise_pct"] == 6.86
    assert result["last_eps_actual"] == 1.20
    assert result["last_eps_estimate"] == 1.00
    assert result["last_eps_surprise_pct"] == 20.0
    assert result["eps_momentum"] == 50.0
    assert result["analyst_buy_pct"] == 83.3
    assert result["analyst_total"] == 12
    assert result["rec_trend"] == "improving"
    assert result["earnings_quality"] == 0.81
