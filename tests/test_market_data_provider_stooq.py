from io import StringIO

import pandas as pd

from src.market_data_providers import stooq_provider


def test_stooq_symbol_appends_us_suffix():
    assert stooq_provider.stooq_symbol("AAPL") == "aapl.us"


def test_stooq_symbol_preserves_existing_suffix():
    assert stooq_provider.stooq_symbol("BRK.B") == "brk.b"


def test_fetch_stooq_ohlcv_normalizes_csv(monkeypatch):
    csv_text = """Date,Open,High,Low,Close,Volume
2026-05-01,10,11,9,10.5,1000
2026-05-02,10.5,12,10,11.5,2000
"""

    monkeypatch.setattr(
        stooq_provider,
        "_http_get",
        lambda url, params, timeout=20: csv_text,
    )

    df = stooq_provider.fetch_stooq_ohlcv("AAPL", period="6mo", interval="1d")

    assert list(df.columns) == ["open", "high", "low", "close", "volume"]
    assert len(df) == 2
    assert df["close"].iloc[-1] == 11.5
    assert isinstance(df.index, pd.DatetimeIndex)


def test_fetch_stooq_ohlcv_returns_empty_for_intraday_interval():
    df = stooq_provider.fetch_stooq_ohlcv("AAPL", period="5d", interval="5m")
    assert df.empty
