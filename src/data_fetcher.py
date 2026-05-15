"""Market data via yfinance + Finnhub fundamentals."""
import yfinance as yf
import pandas as pd
import os
from typing import Dict, List
from concurrent.futures import ThreadPoolExecutor, as_completed

from .market_data_health import (
    classify_provider_error,
    record_market_data_event,
    write_market_data_run_summary,
)
from .market_data_providers.stooq_provider import fetch_stooq_ohlcv

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


def _normalize_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize OHLCV dataframe columns to lowercase."""
    if df is None or df.empty:
        return pd.DataFrame()
    out = df.copy()
    if isinstance(out.columns, pd.MultiIndex):
        out.columns = out.columns.get_level_values(0)
    out.columns = [str(c).lower() for c in out.columns]
    return out


def _fetch_yfinance_ohlcv(ticker: str, period: str, interval: str) -> pd.DataFrame:
    t = yf.Ticker(ticker, session=SESSION) if SESSION else yf.Ticker(ticker)
    df = t.history(period=period, interval=interval, auto_adjust=False, timeout=20)
    return _normalize_ohlcv(df)


def _fetch_stooq_fallback_ohlcv(ticker: str, period: str, interval: str) -> pd.DataFrame:
    return fetch_stooq_ohlcv(ticker, period=period, interval=interval)


def fetch_ohlcv(ticker: str, period: str = "6mo", interval: str = "1d") -> pd.DataFrame:
    """Thread-safe OHLCV fetch with official daily fallback.

    Primary provider:
    - yfinance

    Fallback provider:
    - Stooq for daily OHLCV only

    Safety:
    - no stale/cache fabrication,
    - no paper/live trading behavior,
    - empty dataframe if all providers fail.

    Thread-safety note:
    - do not replace this with yf.download() in parallel fetches;
      yf.download() uses shared module-level state and previously caused
      cross-ticker data leakage. yf.Ticker().history() is per-instance.
    """
    try:
        df = _fetch_yfinance_ohlcv(ticker, period, interval)
        if df is not None and not df.empty:
            record_market_data_event(provider="yfinance", stage="ohlcv", ticker=ticker, result="success")
            return df

        record_market_data_event(
            provider="yfinance",
            stage="ohlcv",
            ticker=ticker,
            result="empty",
            message="empty OHLCV dataframe",
        )
    except Exception as e:
        record_market_data_event(
            provider="yfinance",
            stage="ohlcv",
            ticker=ticker,
            result="error",
            error_type=classify_provider_error(e),
            message=str(e),
        )
        print(f"[data] {ticker}: yfinance {type(e).__name__}: {str(e)[:120]}")

    try:
        fallback = _fetch_stooq_fallback_ohlcv(ticker, period, interval)
        if fallback is not None and not fallback.empty:
            record_market_data_event(provider="stooq", stage="ohlcv", ticker=ticker, result="success")
            return fallback

        record_market_data_event(
            provider="stooq",
            stage="ohlcv",
            ticker=ticker,
            result="empty",
            message="empty OHLCV dataframe",
        )
    except Exception as e:
        record_market_data_event(
            provider="stooq",
            stage="ohlcv",
            ticker=ticker,
            result="error",
            error_type=classify_provider_error(e),
            message=str(e),
        )
        print(f"[data] {ticker}: stooq {type(e).__name__}: {str(e)[:120]}")

    return pd.DataFrame()


def fetch_universe_data(tickers: List[str], period: str = "6mo",
                        max_workers: int = 5) -> Dict[str, pd.DataFrame]:
    results: Dict[str, pd.DataFrame] = {}
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futs = {ex.submit(fetch_ohlcv, t, period): t for t in tickers}
        for fut in as_completed(futs):
            t = futs[fut]
            df = fut.result()
            # PR-A2 F9-1: was >50 which silently dropped IPOs/post-halt resumes.
            # 20 days is enough for short-term technical signal.
            if not df.empty and len(df) > 20:
                results[t] = df
    print(f"[data] Fetched {len(results)}/{len(tickers)} tickers.")
    write_market_data_run_summary(universe_count=len(tickers), fetched_count=len(results))
    return results


def fetch_info(ticker: str) -> dict:
    """Combined info: price/volume from yfinance + fundamentals from Finnhub."""
    info = {
        # Bug #6: do not use ticker as a fake company-name fallback.
        # Downstream layman rendering already hides blank company names.
        "shortName": "",
        "longName": None,
        "name": "",                     # what main.py reads (info_short.name)
        "currentPrice": None,
        "averageVolume": None, "sector": "N/A",  # PR-A7 (audit DF-28): was 1_000_000 default → silent fail-open
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
        info["averageVolume"] = getattr(fast, "ten_day_average_volume", None)  # PR-A7 (audit DF-28): no 1M fallback; preserve None
        info["marketCap"] = getattr(fast, "market_cap", None)
        # Fetch real company name only when explicitly enabled.
        #
        # yfinance .info is substantially heavier than fast_info and can trigger
        # rate limits across hundreds of Daily Picks candidates. Company name is
        # useful presentation metadata, but it must not destabilize official
        # monitoring runs. Default remains lightweight; opt in only for small
        # debug/reporting contexts.
        # PR-A7 (audit DF-33): default flipped from "true" to "false" to match
        # the docstring promise "Default remains lightweight".
        if os.getenv("DAILY_FETCH_YF_FULL_INFO", "false").strip().lower() == "true":
            try:
                full_info = t.info or {}
                long_name = full_info.get("longName") or full_info.get("shortName")
                if long_name and str(long_name).strip().upper() != ticker.upper():
                    long_name = str(long_name).strip()
                    info["longName"]  = long_name
                    info["shortName"] = long_name
                    info["name"]      = long_name
            except Exception:
                pass
    except Exception as e:
        record_market_data_event(provider="yfinance", stage="info", ticker=ticker, result="error", error_type=classify_provider_error(e), message=str(e))
        pass
    else:
        record_market_data_event(provider="yfinance", stage="info", ticker=ticker, result="success")

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



# ═══════════════════════════════════════════════════════════════
# Data validation (E2c.3 — May 4 2026)
# ═══════════════════════════════════════════════════════════════
def is_valid_market_data(info: dict) -> tuple[bool, str]:
    """Return (is_valid, reason) for fetched info dict.

    Catches:
      - currentPrice is None (XXYYZZ123 / delisted)
      - currentPrice <= 0 (corrupted)
      - currentPrice obviously wrong (>$100k for non-BRK.A)
      - averageVolume is None or 0 (untradeable)

    Does NOT cross-validate (that's smell_stale_price's job — it's heavier).
    This is the cheap hard gate.
    """
    p = info.get("currentPrice")
    if p is None:
        return False, "currentPrice is None (likely delisted or invalid ticker)"
    try:
        price = float(p)
    except (TypeError, ValueError):
        return False, f"currentPrice not numeric: {p!r}"
    if price <= 0:
        return False, f"currentPrice not positive: {price}"
    if price > 1_000_000  # PR-A7 (audit DF-45): was 100k which flagged BRK.A (~$700k):
        return False, f"currentPrice suspiciously high: ${price:,.0f}"

    vol = info.get("averageVolume")
    # PR-A7 (audit DF-28): None volume now invalid with clear reason
    if vol is None:
        return False, "averageVolume missing (untradeable, was silently defaulted to 1M)"
    try:
        vol = float(vol or 0)
    except (TypeError, ValueError):
        vol = 0
    if vol <= 0:
        return False, "averageVolume is zero (untradeable)"

    return True, "valid"
