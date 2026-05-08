"""Stooq daily OHLCV fallback provider.

Scope:
- official daily OHLCV fallback only,
- no paper/live trading,
- no stale/fabricated data,
- no intraday support.

Stooq daily CSV format:
Date,Open,High,Low,Close,Volume
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from io import StringIO

import pandas as pd

try:
    from curl_cffi import requests as cf_requests
except Exception:  # pragma: no cover - optional dependency
    cf_requests = None

try:
    import requests
except Exception:  # pragma: no cover - optional dependency
    requests = None


STOOQ_URL = "https://stooq.com/q/d/l/"
DAILY_INTERVALS = {"1d", "1D", "d", "D"}


def stooq_symbol(ticker: str) -> str:
    """Convert a US ticker to Stooq's daily symbol format.

    Keep this conservative. If a ticker already contains an exchange suffix,
    preserve it; otherwise append `.US`.
    """
    raw = str(ticker or "").strip().lower()
    if not raw:
        return ""
    if "." in raw:
        return raw
    return f"{raw}.us"


def _start_date_for_period(period: str) -> str:
    """Return Stooq d1 YYYYMMDD start date for common yfinance periods."""
    now = datetime.now(timezone.utc).date()
    p = str(period or "").strip().lower()

    days = 365
    if p.endswith("d"):
        try:
            days = max(1, int(p[:-1]))
        except ValueError:
            days = 365
    elif p.endswith("mo"):
        try:
            days = max(1, int(p[:-2])) * 31
        except ValueError:
            days = 365
    elif p.endswith("y"):
        try:
            days = max(1, int(p[:-1])) * 366
        except ValueError:
            days = 365
    elif p in {"max", "ytd"}:
        days = 3650

    return (now - timedelta(days=days + 10)).strftime("%Y%m%d")


def _http_get(url: str, params: dict, timeout: int = 20) -> str:
    if cf_requests is not None:
        resp = cf_requests.get(url, params=params, timeout=timeout, impersonate="chrome")
        resp.raise_for_status()
        return resp.text

    if requests is None:
        raise RuntimeError("no HTTP client available for Stooq provider")

    resp = requests.get(url, params=params, timeout=timeout)
    resp.raise_for_status()
    return resp.text


def fetch_stooq_ohlcv(ticker: str, period: str = "6mo", interval: str = "1d") -> pd.DataFrame:
    """Fetch daily OHLCV from Stooq and normalize to lowercase OHLCV schema."""
    if interval not in DAILY_INTERVALS:
        return pd.DataFrame()

    symbol = stooq_symbol(ticker)
    if not symbol:
        return pd.DataFrame()

    text = _http_get(
        STOOQ_URL,
        params={
            "s": symbol,
            "i": "d",
            "d1": _start_date_for_period(period),
        },
        timeout=20,
    )

    if not text or "No data" in text:
        return pd.DataFrame()

    df = pd.read_csv(StringIO(text))
    if df is None or df.empty:
        return pd.DataFrame()

    df.columns = [str(c).strip().lower() for c in df.columns]
    required = {"date", "open", "high", "low", "close", "volume"}
    if not required.issubset(set(df.columns)):
        return pd.DataFrame()

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).set_index("date").sort_index()

    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["open", "high", "low", "close"])
    df["volume"] = df["volume"].fillna(0)

    return df[["open", "high", "low", "close", "volume"]]
