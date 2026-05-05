"""Bug #11 (2026-05-05): days_to_earnings must parse real yfinance calendar shapes.

Problem:
  src.earnings.days_to_earnings currently handles only dict-style calendars.
  yfinance may return DataFrame-like calendar objects, Timestamp values,
  lists/tuples, strings, or empty calendars. Returning 999 too often means
  earnings-risk filtering silently becomes blind.

Contract:
  - Known future earnings date returns days until earnings.
  - Past/today earnings date clamps to 0.
  - Unknown/empty calendar returns 999.
"""
from datetime import date, datetime

import pandas as pd

import src.earnings as earnings


class FixedDateTime(datetime):
    @classmethod
    def now(cls, tz=None):
        return cls(2026, 5, 5)


class FakeTicker:
    def __init__(self, calendar):
        self.calendar = calendar


def patch_ticker(monkeypatch, calendar):
    monkeypatch.setattr(earnings, "SESSION", None)
    monkeypatch.setattr(earnings, "datetime", FixedDateTime)
    monkeypatch.setattr(earnings.yf, "Ticker", lambda ticker: FakeTicker(calendar))


def test_days_to_earnings_parses_dict_list_timestamp(monkeypatch):
    patch_ticker(monkeypatch, {"Earnings Date": [pd.Timestamp("2026-05-10")]})
    assert earnings.days_to_earnings("AAPL") == 5


def test_days_to_earnings_parses_dict_string(monkeypatch):
    patch_ticker(monkeypatch, {"Earnings Date": ["2026-05-12"]})
    assert earnings.days_to_earnings("NVDA") == 7


def test_days_to_earnings_parses_dataframe_index_shape(monkeypatch):
    """Common yfinance shape: index contains 'Earnings Date', value cell has date."""
    cal = pd.DataFrame({0: [pd.Timestamp("2026-05-20")]}, index=["Earnings Date"])
    patch_ticker(monkeypatch, cal)

    assert earnings.days_to_earnings("MSFT") == 15


def test_days_to_earnings_parses_dataframe_column_shape(monkeypatch):
    """Alternate shape: column contains 'Earnings Date'."""
    cal = pd.DataFrame({"Earnings Date": [pd.Timestamp("2026-05-18")]})
    patch_ticker(monkeypatch, cal)

    assert earnings.days_to_earnings("TSM") == 13


def test_days_to_earnings_clamps_past_date_to_zero(monkeypatch):
    patch_ticker(monkeypatch, {"Earnings Date": [date(2026, 5, 1)]})
    assert earnings.days_to_earnings("OLD") == 0


def test_days_to_earnings_unknown_empty_returns_999(monkeypatch):
    patch_ticker(monkeypatch, pd.DataFrame())
    assert earnings.days_to_earnings("UNKNOWN") == 999
