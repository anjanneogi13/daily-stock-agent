"""Day Trading Scorer.

Different from swing scorer — emphasizes INTRADAY momentum,
relative volume, ATR/price ratio, and gap behavior.

Returns a 0-1 score representing day-trade-ability for a candidate.

Day trades require:
  - Liquidity (avg daily $ volume > $20M)
  - Volatility (ATR/price between 1% and 5%)
  - Recent momentum (RSI 50-75, not overbought)
  - Volume confirmation (RVOL > 1.2)
  - Trend alignment (price above VWAP/EMAs)
  - Catalyst (news, gap, breakout)
"""
from typing import Dict


def _score_rvol(vol_ratio: float) -> float:
    """Relative volume vs 20-day average. Higher = more interest."""
    if vol_ratio >= 2.5: return 1.00   # huge volume spike
    if vol_ratio >= 2.0: return 0.95
    if vol_ratio >= 1.5: return 0.85
    if vol_ratio >= 1.2: return 0.70
    if vol_ratio >= 1.0: return 0.50
    if vol_ratio >= 0.8: return 0.30
    return 0.15  # dead volume


def _score_atr_ratio(atr: float, price: float) -> float:
    """ATR/price ratio — sweet spot is 1.5-3% for day trades."""
    if not atr or not price or price <= 0:
        return 0.30
    ratio = atr / price
    if 0.015 <= ratio <= 0.035: return 1.00   # ideal day-trade volatility
    if 0.010 <= ratio <= 0.045: return 0.80
    if 0.008 <= ratio <= 0.055: return 0.60
    if ratio < 0.008: return 0.30  # too quiet to day trade
    return 0.40  # too volatile (gap risk)


def _score_intraday_momentum(rsi: float, macd_hist: float) -> float:
    """Day trades like RSI 50-75 (rising, not exhausted) + positive MACD hist."""
    rsi_score = 0.50
    if rsi:
        if 55 <= rsi <= 70: rsi_score = 1.00     # sweet spot
        elif 50 <= rsi < 55: rsi_score = 0.80
        elif 70 < rsi <= 75: rsi_score = 0.75
        elif 45 <= rsi < 50: rsi_score = 0.55
        elif rsi > 80: rsi_score = 0.20          # exhausted
        elif rsi < 40: rsi_score = 0.30          # weak

    macd_score = 0.50
    if macd_hist is not None:
        if macd_hist > 0.5: macd_score = 1.00
        elif macd_hist > 0: macd_score = 0.75
        elif macd_hist > -0.5: macd_score = 0.40
        else: macd_score = 0.20

    return round(rsi_score * 0.6 + macd_score * 0.4, 3)


def _score_trend_alignment(sig: dict) -> float:
    """Price above EMAs + above VWAP = bullish intraday."""
    score = 0.30
    close = sig.get("close", 0)
    ema_20 = sig.get("ema_20", 0)
    ema_50 = sig.get("ema_50", 0)
    vwap = sig.get("vwap", 0)

    if close and ema_20 and close > ema_20: score += 0.25
    if close and ema_50 and close > ema_50: score += 0.20
    if close and vwap and close > vwap: score += 0.25
    return min(1.0, round(score, 3))


def _score_liquidity(volume: float, price: float) -> float:
    """Avg daily $ volume — day trades need depth to enter/exit fast."""
    if not volume or not price:
        return 0.30
    daily_dollars = volume * price
    if daily_dollars >= 100_000_000: return 1.00  # $100M+ very liquid
    if daily_dollars >= 50_000_000:  return 0.90
    if daily_dollars >= 20_000_000:  return 0.75
    if daily_dollars >= 10_000_000:  return 0.55
    if daily_dollars >= 5_000_000:   return 0.35
    return 0.15  # too thin


def day_trading_score(sig: dict, news_boost: float = 0.0) -> Dict:
    """
    Compute day-trade-ability score from indicators.

    Args:
        sig: latest_signals(df) output (close, atr_14, rsi_14, vol_ratio, etc.)
        news_boost: 0.0 to 0.15 — added if recent bullish catalyst

    Returns:
        dict with: day_score (0-1), components, day_reason (text)
    """
    price = sig.get("close", 0)
    atr = sig.get("atr_14") or sig.get("atr") or 0
    vol_ratio = sig.get("vol_ratio", 1.0) or 1.0
    rsi = sig.get("rsi_14") or sig.get("rsi") or 50
    macd_hist = sig.get("macd_hist", 0) or 0
    volume = sig.get("volume", 0) or 0

    components = {
        "rvol":       _score_rvol(vol_ratio),
        "atr_ratio":  _score_atr_ratio(atr, price),
        "momentum":   _score_intraday_momentum(rsi, macd_hist),
        "trend":      _score_trend_alignment(sig),
        "liquidity":  _score_liquidity(volume, price),
    }

    # Day-trade weights (different from swing!)
    weights = {
        "rvol":       0.30,   # volume is KING for day trades
        "atr_ratio":  0.20,   # need right volatility level
        "momentum":   0.20,   # intraday momentum
        "trend":      0.15,   # trend alignment
        "liquidity":  0.15,   # must be tradable
    }

    raw = sum(components[k] * weights[k] for k in components)
    final = min(1.0, raw + news_boost)

    # Build reason string
    reasons = []
    if components["rvol"] >= 0.85: reasons.append(f"RVOL={vol_ratio:.1f}x")
    if components["atr_ratio"] >= 0.80: reasons.append(f"ATR={atr/price*100:.1f}%")
    if components["momentum"] >= 0.75: reasons.append(f"RSI={rsi:.0f}")
    if components["trend"] >= 0.75: reasons.append("above VWAP+EMAs")
    if news_boost > 0: reasons.append(f"news+{news_boost:.2f}")
    reason = " · ".join(reasons) if reasons else "weak day setup"

    return {
        "day_score": round(final, 3),
        "day_components": components,
        "day_reason": reason,
        "news_boost": news_boost,
    }


def is_day_tradeable(day_score: float, min_threshold: float = 0.65) -> bool:
    """Quick boolean check: is this pick suitable for day trading?"""
    return day_score >= min_threshold