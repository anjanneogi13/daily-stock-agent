"""Skip tickers with imminent earnings (gap risk)."""
import yfinance as yf
from datetime import datetime, timedelta

try:
    from curl_cffi import requests as cf_requests
    SESSION = cf_requests.Session(impersonate="chrome")
except Exception:
    SESSION = None


def days_to_earnings(ticker: str) -> int:
    """Returns days until next earnings, or 999 if unknown."""
    try:
        t = yf.Ticker(ticker, session=SESSION) if SESSION else yf.Ticker(ticker)
        cal = t.calendar
        if cal is None or (hasattr(cal, "empty") and cal.empty):
            return 999
        if isinstance(cal, dict):
            ed = cal.get("Earnings Date")
            if ed and len(ed) > 0:
                next_date = ed[0] if not isinstance(ed[0], list) else ed[0][0]
            else:
                return 999
        else:
            return 999
        if isinstance(next_date, str):
            next_date = datetime.fromisoformat(next_date).date()
        elif hasattr(next_date, "date"):
            next_date = next_date.date()
        delta = (next_date - datetime.now().date()).days
        return max(delta, 0)
    except Exception:
        return 999


def earnings_safe(ticker: str, min_days: int = 5) -> bool:
    """True if no earnings in next `min_days` days."""
    return days_to_earnings(ticker) >= min_days
