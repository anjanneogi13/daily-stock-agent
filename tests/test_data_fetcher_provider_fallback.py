import pandas as pd

from src import data_fetcher


def _df(close=10.0, rows=60):
    idx = pd.date_range("2026-01-01", periods=rows, freq="D")
    return pd.DataFrame({
        "open": [close] * rows,
        "high": [close + 1] * rows,
        "low": [close - 1] * rows,
        "close": [close] * rows,
        "volume": [1000] * rows,
    }, index=idx)


def test_fetch_ohlcv_yfinance_success_does_not_call_stooq(monkeypatch):
    calls = []

    monkeypatch.setattr(data_fetcher, "_fetch_yfinance_ohlcv", lambda ticker, period, interval: _df())
    monkeypatch.setattr(data_fetcher, "_fetch_stooq_fallback_ohlcv", lambda *args: calls.append(args) or _df(close=20))
    monkeypatch.setattr(data_fetcher, "record_market_data_event", lambda **kwargs: None)

    out = data_fetcher.fetch_ohlcv("AAPL")

    assert not out.empty
    assert out["close"].iloc[-1] == 10.0
    assert calls == []


def test_fetch_ohlcv_yfinance_empty_calls_stooq(monkeypatch):
    events = []

    monkeypatch.setattr(data_fetcher, "_fetch_yfinance_ohlcv", lambda ticker, period, interval: pd.DataFrame())
    monkeypatch.setattr(data_fetcher, "_fetch_stooq_fallback_ohlcv", lambda ticker, period, interval: _df(close=20))
    monkeypatch.setattr(data_fetcher, "record_market_data_event", lambda **kwargs: events.append(kwargs))

    out = data_fetcher.fetch_ohlcv("AAPL")

    assert not out.empty
    assert out["close"].iloc[-1] == 20.0
    assert any(e["provider"] == "yfinance" and e["result"] == "empty" for e in events)
    assert any(e["provider"] == "stooq" and e["result"] == "success" for e in events)


def test_fetch_ohlcv_yfinance_error_calls_stooq(monkeypatch):
    events = []

    def boom(*args):
        raise RuntimeError("rate limit")

    monkeypatch.setattr(data_fetcher, "_fetch_yfinance_ohlcv", boom)
    monkeypatch.setattr(data_fetcher, "_fetch_stooq_fallback_ohlcv", lambda ticker, period, interval: _df(close=30))
    monkeypatch.setattr(data_fetcher, "record_market_data_event", lambda **kwargs: events.append(kwargs))

    out = data_fetcher.fetch_ohlcv("AAPL")

    assert not out.empty
    assert out["close"].iloc[-1] == 30.0
    assert any(e["provider"] == "yfinance" and e["result"] == "error" for e in events)
    assert any(e["provider"] == "stooq" and e["result"] == "success" for e in events)


def test_fetch_ohlcv_all_providers_fail_returns_empty(monkeypatch):
    events = []

    monkeypatch.setattr(data_fetcher, "_fetch_yfinance_ohlcv", lambda ticker, period, interval: pd.DataFrame())
    monkeypatch.setattr(data_fetcher, "_fetch_stooq_fallback_ohlcv", lambda ticker, period, interval: pd.DataFrame())
    monkeypatch.setattr(data_fetcher, "record_market_data_event", lambda **kwargs: events.append(kwargs))

    out = data_fetcher.fetch_ohlcv("AAPL")

    assert out.empty
    assert any(e["provider"] == "yfinance" and e["result"] == "empty" for e in events)
    assert any(e["provider"] == "stooq" and e["result"] == "empty" for e in events)


def test_fetch_universe_data_still_filters_short_history(monkeypatch):
    monkeypatch.setattr(data_fetcher, "fetch_ohlcv", lambda ticker, period: _df(rows=10))
    monkeypatch.setattr(data_fetcher, "write_market_data_run_summary", lambda **kwargs: None)

    out = data_fetcher.fetch_universe_data(["AAPL"], period="6mo", max_workers=1)

    assert out == {}
