"""Market regime detection — avoid buying in bear markets.

BUG-3 FIX (May 2 2026): Eliminated "unknown" regime via:
  1. Retry fetch up to 3× with backoff
  2. Fallback to 100-day SMA when 200d data unavailable
  3. Disk cache (data/last_regime.json) for transient failures
"""
import json
import time
from pathlib import Path
import pandas as pd
from .data_fetcher import fetch_ohlcv

_CACHE_PATH = Path("data/last_regime.json")


def _load_cached_regime() -> dict | None:
    """Return last successfully computed regime, or None."""
    if not _CACHE_PATH.exists():
        return None
    try:
        with _CACHE_PATH.open() as f:
            cached = json.load(f)
        cached["from_cache"] = True
        return cached
    except Exception:
        return None


def _save_regime(regime: dict) -> None:
    """Persist regime for future fallback use."""
    try:
        _CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with _CACHE_PATH.open("w") as f:
            json.dump(regime, f, indent=2)
    except Exception:
        pass


def _fetch_spy_with_retry(max_attempts: int = 3) -> pd.DataFrame:
    """Fetch SPY OHLCV with retries on empty/short data."""
    last = pd.DataFrame()
    for attempt in range(max_attempts):
        df = fetch_ohlcv("SPY", period="1y")
        if not df.empty and len(df) >= 100:
            return df
        last = df
        if attempt < max_attempts - 1:
            time.sleep(2)
    return last


def market_regime() -> dict:
    """Check if SPY is above its 200-day SMA (bull) or below (bear).

    Falls back to:
      - 100-day SMA if 200d unavailable (marked sma_window=100)
      - Cached last-known regime if fetch fails entirely
      - Conservative bull default if no cache exists (allows trading)
    """
    spy = _fetch_spy_with_retry()

    # Total fetch failure → fall back to cache
    if spy.empty:
        cached = _load_cached_regime()
        if cached:
            cached["fetch_failed"] = True
            return cached
        # No cache, no data → conservative bull (allows trading)
        return {
            "regime": "bull",
            "spy_close": None,
            "spy_sma200": None,
            "bullish": True,
            "sma_window": 0,
            "fetch_failed": True,
            "fallback": "no_data_no_cache",
        }

    spy_close = float(spy["close"].iloc[-1])

    # Prefer 200d SMA, fall back to 100d
    if len(spy) >= 200:
        sma = float(spy["close"].rolling(200).mean().iloc[-1])
        sma_window = 200
    else:
        sma = float(spy["close"].rolling(min(100, len(spy))).mean().iloc[-1])
        sma_window = min(100, len(spy))

    bullish = spy_close > sma
    result = {
        "regime": "bull" if bullish else "bear",
        "spy_close": round(spy_close, 2),
        "spy_sma200": round(sma, 2),  # keep field name for backward compat
        "bullish": bullish,
        "distance_pct": round((spy_close / sma - 1) * 100, 2),
        "sma_window": sma_window,
    }
    _save_regime(result)
    return result
