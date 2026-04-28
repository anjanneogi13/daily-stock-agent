"""Market data via yfinance + Finnhub fundamentals."""
import yfinance as yf
import pandas as pd
import os
from typing import Dict, List
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from curl_cffi import requests as cf_requests
    SESSION = cf_requests.Session(impersonate="chrome")
except Exception:
    SESSION = None

# Optional Finnhub for fundamentals
try:
    from .finnhub_data import fetch_fundamentals as _finnhub_fundamentals
    HAS_FINNHUB = True
except Exception:
    HAS_FINNHUB = False


def fetch_ohlcv(ticker: str, period: str = "6mo", interval: str = "1d") -> pd.DataFrame:
    """Thread-safe OHLCV fetch.

    NOTE: yf.download() is NOT thread-safe (shares module-level cache,
    causes data leakage across parallel ticker fetches). yf.Ticker().history()
    is per-instance and safe to use in ThreadPoolExecutor.
    """
    try:
        t = yf.Ticker(ticker)
        df = t.history(period=period, interval=interval,
                       auto_adjust=False, timeout=20)
        if df is None or df.empty:
            return pd.DataFrame()
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df.columns = [c.lower() for c in df.columns]
        return df
    except Exception as e:
        print(f"[data] {ticker}: {type(e).__name__}: {str(e)[:120]}")
        return pd.DataFrame()


def fetch_universe_data(tickers: List[str], period: str = "6mo",
                        max_workers: int = 5) -> Dict[str, pd.DataFrame]:
    results: Dict[str, pd.DataFrame] = {}
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futs = {ex.submit(fetch_ohlcv, t, period): t for t in tickers}
        for fut in as_completed(futs):
            t = futs[fut]
            df = fut.result()
            if not df.empty and len(df) > 50:
                results[t] = df
    print(f"[data] Fetched {len(results)}/{len(tickers)} tickers.")
    return results


def fetch_info(ticker: str) -> dict:
    """Combined info: price/volume from yfinance + fundamentals from Finnhub."""
    info = {
        "shortName": ticker, "currentPrice": None,
        "averageVolume": 1_000_000, "sector": "N/A",
        "marketCap": None, "trailingPE": None,
        "earningsQuarterlyGrowth": None, "profitMargins": None,
        "debtToEquity": None,
    }
    # 1. Price + volume from yfinance fast_info (lightweight)
    try:
        t = yf.Ticker(ticker, session=SESSION) if SESSION else yf.Ticker(ticker)
        fast = t.fast_info
        info["currentPrice"] = getattr(fast, "last_price", None)
        info["regularMarketPrice"] = getattr(fast, "last_price", None)
        info["averageVolume"] = getattr(fast, "ten_day_average_volume", None) or 1_000_000
        info["marketCap"] = getattr(fast, "market_cap", None)
    except Exception:
        pass

    # 2. Real fundamentals from Finnhub (if key set)
    if HAS_FINNHUB and os.getenv("FINNHUB_API_KEY"):
        try:
            fund = _finnhub_fundamentals(ticker)
            for k, v in fund.items():
                if v is not None and v != "N/A":
                    info[k] = v
        except Exception as e:
            print(f"[finnhub] {ticker} skipped: {type(e).__name__}")

    return info
