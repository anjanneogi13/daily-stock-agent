"""Tests for yfinance info-pressure controls."""
from types import SimpleNamespace


class FakeTicker:
    def __init__(self):
        self.fast_info = SimpleNamespace(
            last_price=123.45,
            ten_day_average_volume=2_000_000,
            market_cap=10_000_000_000,
        )
        self.info_access_count = 0

    @property
    def info(self):
        self.info_access_count += 1
        return {
            "longName": "Example Corporation",
            "shortName": "Example",
        }


def test_fetch_info_skips_heavy_yfinance_info_when_disabled(monkeypatch):
    import src.data_fetcher as df

    fake = FakeTicker()
    monkeypatch.setenv("DAILY_FETCH_YF_FULL_INFO", "false")
    monkeypatch.setattr(df.yf, "Ticker", lambda ticker, session=None: fake)
    monkeypatch.setattr(df, "SESSION", None)
    monkeypatch.setattr(df, "HAS_FINNHUB", False)

    info = df.fetch_info("EXAMPLE")

    assert fake.info_access_count == 0
    assert info["currentPrice"] == 123.45
    assert info["averageVolume"] == 2_000_000
    assert info["marketCap"] == 10_000_000_000
    assert info["name"] == ""


def test_fetch_info_heavy_yfinance_info_disabled_by_default_contract(monkeypatch):
    """PR-A7 (audit DF-33): default is now 'false' to match the docstring
    promise 'Default remains lightweight'. With env unset, t.info must NOT
    be touched, and company name fields stay empty/None."""
    import src.data_fetcher as df

    fake = FakeTicker()
    monkeypatch.delenv("DAILY_FETCH_YF_FULL_INFO", raising=False)
    monkeypatch.setattr(df.yf, "Ticker", lambda ticker, session=None: fake)
    monkeypatch.setattr(df, "SESSION", None)
    monkeypatch.setattr(df, "HAS_FINNHUB", False)

    info = df.fetch_info("EXAMPLE")

    assert fake.info_access_count == 0
    assert info["name"] == ""
    assert info["longName"] is None


def test_fetch_info_heavy_yfinance_info_when_env_true(monkeypatch):
    """Coverage for the opt-in heavy path: env=true → t.info IS read."""
    import src.data_fetcher as df

    fake = FakeTicker()
    monkeypatch.setenv("DAILY_FETCH_YF_FULL_INFO", "true")
    monkeypatch.setattr(df.yf, "Ticker", lambda ticker, session=None: fake)
    monkeypatch.setattr(df, "SESSION", None)
    monkeypatch.setattr(df, "HAS_FINNHUB", False)

    info = df.fetch_info("EXAMPLE")

    assert fake.info_access_count == 1
    assert info["name"] == "Example Corporation"
    assert info["longName"] == "Example Corporation"


def test_daily_picks_workflow_disables_heavy_yfinance_full_info():
    from pathlib import Path

    workflow = Path(".github/workflows/daily-picks.yml").read_text()

    assert "DAILY_FETCH_YF_FULL_INFO: false" in workflow
