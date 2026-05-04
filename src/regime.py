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
        # No cache, no data → DEFENSIVE transition (Finding #4 fix May 4 2026)
        # Was "bull" but that meant full-size trades on a total data blackout.
        # transition = 0.8x sizing in atr_trade_plan, more honest about uncertainty.
        return {
            "regime": "transition",
            "spy_close": None,
            "spy_sma200": None,
            "bullish": False,
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
    distance_pct = (spy_close / sma - 1) * 100

    # E3a: 4-state regime classification (was binary bull/bear)
    # Distance from SMA is a robust regime proxy — used by hypothesis_engine,
    # pattern_stats, and (after E3b) position sizer.
    #   > +5%       → bull       (strong uptrend, risk-on)
    #   -2% to +5%  → transition (near SMA, undecided — caution)
    #   -5% to -2%  → chop       (below SMA but not collapsed — reduce risk)
    #   < -5%       → bear       (true bear market, defensive)
    if distance_pct >= 5.0:
        regime_label = "bull"
    elif distance_pct >= -2.0:
        regime_label = "transition"
    elif distance_pct >= -5.0:
        regime_label = "chop"
    else:
        regime_label = "bear"

    result = {
        "regime": regime_label,
        "spy_close": round(spy_close, 2),
        "spy_sma200": round(sma, 2),
        "spy_sma_anchor": round(sma, 2),  # M5: honest name when sma_window != 200
        "sma_value": round(sma, 2),  # keep field name for backward compat
        "bullish": bullish,             # legacy boolean for callers expecting it
        "distance_pct": round(distance_pct, 2),
        "sma_window": sma_window,
    }
    _save_regime(result)
    return result
