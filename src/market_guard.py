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

def classify_trade_type(scores: dict, sig: dict = None, gap_pct: float = 0.0) -> str:
    """
    Auto-tag pick as 'day' or 'swing' based on score profile + indicators.

    PR #67 FIX: Old logic required momentum > 0.75 AND volume > 0.7
    which was IMPOSSIBLY HIGH (no picks ever qualified). Result: all
    28 picks tagged "swing", causing -6% losses on what should have
    been quick intraday trades.

    NEW LOGIC:
      - DAY trade if: high momentum (>0.65) + decent volume (>0.55)
                      + tight ATR (<3.5%) + no big gap
      - Otherwise: SWING (multi-day hold)

    Args:
        scores: composite_score output (momentum, volume, trend, etc.)
        sig: latest_signals dict (for ATR/price ratio check) — optional
        gap_pct: overnight gap as decimal (0.02 = 2%)

    Returns:
        "day" or "swing"
    """
    momentum = scores.get("momentum", 0.5)
    volume   = scores.get("volume", 0.5)
    trend    = scores.get("trend", 0.5)

    # ATR/price ratio — too volatile = better as swing (overnight risk)
    atr_ratio = 0.02
    if sig:
        atr = sig.get("atr_14") or sig.get("atr") or 0
        price = sig.get("close", 0)
        if atr and price > 0:
            atr_ratio = atr / price

    # DAY criteria (REALISTIC thresholds)
    is_day = (
        momentum >= 0.65 and       # strong intraday momentum
        volume   >= 0.55 and       # above-average volume
        atr_ratio <= 0.035 and     # not too crazy volatile
        abs(gap_pct) < 0.04        # not a huge gap (gap-and-fade risk)
    )

    if is_day:
        return "day"

    # Strong trend + reasonable composite → swing
    if trend >= 0.60:
        return "swing"

    # Default: swing (safer default for marginal setups)
    return "swing"


def classify_with_day_score(scores: dict, day_score: float,
                             sig: dict = None, gap_pct: float = 0.0) -> str:
    """
    Enhanced classifier using the dedicated day_trading_score.
    Use this when day_score is available (preferred over classify_trade_type alone).

    Returns "day" if day_score >= 0.65 AND meets gap constraint.
    """
    if day_score >= 0.65 and abs(gap_pct) < 0.04:
        return "day"
    return classify_trade_type(scores, sig, gap_pct)