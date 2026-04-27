"""Market data via yfinance with curl_cffi session (bypasses EU consent)."""
import yfinance as yf
import pandas as pd
from typing import Dict, List
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from curl_cffi import requests as cf_requests
    SESSION = cf_requests.Session(impersonate="chrome")
except Exception:
    SESSION = None


def fetch_ohlcv(ticker: str, period: str = "6mo", interval: str = "1d") -> pd.DataFrame:
    try:
        kwargs = dict(period=period, interval=interval,
                      progress=False, auto_adjust=True, timeout=20)
        if SESSION is not None:
            kwargs["session"] = SESSION
        df = yf.download(ticker, **kwargs)
        if df.empty:
            return pd.DataFrame()
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df.columns = [c.lower() for c in df.columns]
        return df
    except Exception as e:
        print(f"[data] {ticker}: {type(e).__name__}")
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
    """Lightweight info fetch with browser-impersonating session."""
    try:
        t = yf.Ticker(ticker, session=SESSION) if SESSION else yf.Ticker(ticker)
        fast = t.fast_info
        return {
            "shortName": ticker,
            "currentPrice": getattr(fast, "last_price", None),
            "regularMarketPrice": getattr(fast, "last_price", None),
            "averageVolume": getattr(fast, "ten_day_average_volume", None) or 1_000_000,
            "marketCap": getattr(fast, "market_cap", None),
            "sector": "N/A",
        }
    except Exception:
        return {
            "shortName": ticker,
            "currentPrice": None,
            "averageVolume": 1_000_000,
            "sector": "N/A",
        }
