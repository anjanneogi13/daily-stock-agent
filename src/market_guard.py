"""Market-wide guards: VIX gate, SPY trend gate, sector strength check."""
import yfinance as yf
from datetime import datetime, timedelta

def vix_level() -> float:
    """Current VIX. Returns 0 on failure."""
    try:
        v = yf.Ticker("^VIX").history(period="2d")
        return float(v["Close"].iloc[-1]) if len(v) else 0.0
    except Exception:
        return 0.0

def spy_trend() -> dict:
    """Returns {'above_50dma': bool, 'above_200dma': bool, 'spy_close': float}."""
    try:
        h = yf.Ticker("SPY").history(period="250d")
        if len(h) < 200:
            return {"above_50dma": True, "above_200dma": True, "spy_close": 0.0}
        c = h["Close"]
        return {
            "above_50dma": bool(c.iloc[-1] > c.rolling(50).mean().iloc[-1]),
            "above_200dma": bool(c.iloc[-1] > c.rolling(200).mean().iloc[-1]),
            "spy_close": float(c.iloc[-1]),
        }
    except Exception:
        return {"above_50dma": True, "above_200dma": True, "spy_close": 0.0}

def sector_strength(sector_etfs: dict = None) -> dict:
    """
    Returns dict of {sector: {'change_pct': X, 'weak': bool}} based on yesterday→today.
    sector_etfs: {"Technology": "XLK", "Semiconductors": "SOXX", ...}
    """
    sector_etfs = sector_etfs or {
        "Technology": "XLK", "Semiconductors": "SOXX",
        "Healthcare": "XLV", "Financials": "XLF", "Energy": "XLE",
        "Consumer Cyclical": "XLY", "Consumer Defensive": "XLP",
        "Industrials": "XLI", "Communication Services": "XLC",
        "Utilities": "XLU", "Real Estate": "XLRE", "Materials": "XLB",
    }
    out = {}
    for sector, etf in sector_etfs.items():
        try:
            h = yf.Ticker(etf).history(period="3d")
            if len(h) < 2:
                continue
            change = (h["Close"].iloc[-1] - h["Close"].iloc[-2]) / h["Close"].iloc[-2]
            out[sector] = {"change_pct": round(change*100, 2),
                           "weak": change < -0.02}
        except Exception:
            continue
    return out

def classify_trade_type(scores: dict, gap_pct: float = 0.0) -> str:
    """
    Auto-tag pick as 'day' or 'swing' based on score profile.
    DAY = high momentum + volume + small gap (intraday momentum)
    SWING = trend + fundamentals (multi-day hold)
    """
    momentum = scores.get("momentum", 0.5)
    volume   = scores.get("volume", 0.5)
    trend    = scores.get("trend", 0.5)
    # High momentum + high volume + decent gap → day trade
    if momentum > 0.75 and volume > 0.7 and abs(gap_pct) < 0.025:
        return "day"
    # Strong trend + composite → swing
    return "swing"
