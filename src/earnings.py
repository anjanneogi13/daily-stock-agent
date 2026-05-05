"""Skip tickers with imminent earnings (gap risk)."""
from datetime import date, datetime
from collections.abc import Iterable

import yfinance as yf

try:
    from curl_cffi import requests as cf_requests
    SESSION = cf_requests.Session(impersonate="chrome")
except Exception:
    SESSION = None


UNKNOWN_EARNINGS_DAYS = 999


def _first_non_empty(value):
    """Unwrap common yfinance calendar containers to a scalar date-like value.

    Handles:
      - [Timestamp(...)]
      - [[Timestamp(...), Timestamp(...)]]
      - pandas Series / Index / numpy arrays
      - plain scalar values
    """
    if value is None:
        return None

    # pandas Series/DataFrame row values often expose .iloc
    if hasattr(value, "iloc"):
        try:
            if len(value) == 0:
                return None
            return _first_non_empty(value.iloc[0])
        except Exception:
            pass

    # Strings are iterable, but should be treated as scalar date values.
    if isinstance(value, str):
        return value

    # datetime/date/Timestamp-like objects should be scalar.
    if hasattr(value, "date") or isinstance(value, date):
        return value

    if isinstance(value, Iterable):
        try:
            seq = list(value)
        except Exception:
            return value
        if not seq:
            return None
        return _first_non_empty(seq[0])

    return value


def _extract_earnings_date(calendar):
    """Extract the next earnings date from known yfinance calendar shapes."""
    if calendar is None:
        return None

    # Empty pandas DataFrame/Series.
    if hasattr(calendar, "empty"):
        try:
            if calendar.empty:
                return None
        except Exception:
            pass

    # Shape 1: dict, e.g. {"Earnings Date": [Timestamp("2026-05-10")]}
    if isinstance(calendar, dict):
        return _first_non_empty(calendar.get("Earnings Date"))

    # Shape 2: DataFrame with column "Earnings Date"
    #   Earnings Date
    # 0 2026-05-18
    if hasattr(calendar, "columns"):
        try:
            if "Earnings Date" in calendar.columns:
                return _first_non_empty(calendar["Earnings Date"])
        except Exception:
            pass

    # Shape 3: DataFrame with index "Earnings Date"
    #                    0
    # Earnings Date 2026-05-20
    if hasattr(calendar, "index") and hasattr(calendar, "loc"):
        try:
            if "Earnings Date" in calendar.index:
                return _first_non_empty(calendar.loc["Earnings Date"])
        except Exception:
            pass

    return None


def _to_date(value):
    """Normalize a date-like value to datetime.date, or None if unknown."""
    value = _first_non_empty(value)
    if value is None:
        return None

    if isinstance(value, datetime):
        return value.date()

    # pandas Timestamp also has .date()
    if hasattr(value, "date"):
        try:
            return value.date()
        except Exception:
            pass

    if isinstance(value, date):
        return value

    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value).date()
        except ValueError:
            return None

    return None


def _as_of_date(as_of=None):
    """Normalize an optional historical anchor date.

    None preserves live behavior. A date/datetime/ISO string enables historical
    backfills where days_to_earnings must be relative to pick_date, not today.
    """
    if as_of is None:
        return datetime.now().date()
    if isinstance(as_of, datetime):
        return as_of.date()
    if isinstance(as_of, date):
        return as_of
    if isinstance(as_of, str):
        return datetime.fromisoformat(as_of).date()
    raise TypeError(f"Unsupported as_of date value: {as_of!r}")


def days_to_earnings(ticker: str, as_of=None) -> int:
    """Returns days until next earnings, or 999 if unknown.

    yfinance has changed calendar shapes over time. This parser accepts dict
    and DataFrame-like shapes so earnings-risk filtering does not silently go
    blind when the upstream object format changes.

    Args:
        ticker: Symbol to query.
        as_of: Optional historical anchor date. When provided, the returned
            delta is relative to that date instead of today's date.
    """
    try:
        t = yf.Ticker(ticker, session=SESSION) if SESSION else yf.Ticker(ticker)
        next_date = _to_date(_extract_earnings_date(t.calendar))
        if next_date is None:
            return UNKNOWN_EARNINGS_DAYS

        delta = (next_date - _as_of_date(as_of)).days
        return max(delta, 0)
    except Exception:
        return UNKNOWN_EARNINGS_DAYS


def earnings_safe(ticker: str, min_days: int = 5) -> bool:
    """True if no earnings in next `min_days` days."""
    return days_to_earnings(ticker) >= min_days
