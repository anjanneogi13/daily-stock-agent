"""Market regime detection — avoid buying in bear markets."""
import pandas as pd
from .data_fetcher import fetch_ohlcv


def market_regime() -> dict:
    """Check if SPY is above its 200-day SMA (bull) or below (bear)."""
    spy = fetch_ohlcv("SPY", period="1y")
    if spy.empty or len(spy) < 200:
        return {"regime": "unknown", "spy_close": None, "spy_sma200": None,
                "bullish": True}  # default to allow trading
    spy_close = float(spy["close"].iloc[-1])
    spy_sma200 = float(spy["close"].rolling(200).mean().iloc[-1])
    bullish = spy_close > spy_sma200
    return {
        "regime": "bull" if bullish else "bear",
        "spy_close": round(spy_close, 2),
        "spy_sma200": round(spy_sma200, 2),
        "bullish": bullish,
        "distance_pct": round((spy_close / spy_sma200 - 1) * 100, 2),
    }
