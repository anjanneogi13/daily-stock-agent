"""Multi-factor scoring with semiconductor sector boost + advanced indicators."""
from typing import Dict
from .semiconductors import is_semi, get_semi_meta


# ─── Adaptive sector concentration (Week 2) ───────────────────────
def apply_sector_cap(picks: list, max_per_sector: int = 4,
                     reduced_sectors: dict = None) -> list:
    """Cap picks per sector. reduced_sectors = {"Technology": 2} for weak sectors today."""
    reduced_sectors = reduced_sectors or {}
    counts = {}
    kept = []
    for p in sorted(picks, key=lambda x: x.get("scores", {}).get("composite", 0), reverse=True):
        sector = p.get("info_short", {}).get("sector", "Unknown")
        cap = reduced_sectors.get(sector, max_per_sector)
        if counts.get(sector, 0) < cap:
            kept.append(p)
            counts[sector] = counts.get(sector, 0) + 1
    return kept


def apply_tag_cap(picks: list, max_per_tag: int = 2) -> list:
    """Hard cap by primary tag (SEMI, AI, etc.). Catches what yfinance sector misses.
    Tag format: 'SEMI / AI' → primary='SEMI'. Sorts by composite score, keeps top N per tag.
    """
    counts = {}
    kept = []
    for p in sorted(picks, key=lambda x: x.get("scores", {}).get("composite", 0), reverse=True):
        tag = p.get("tag") or ""
        if not tag:
            kept.append(p)
            continue
        primary = tag.split(" / ")[0].strip().upper()
        if not primary:
            kept.append(p)
            continue
        if counts.get(primary, 0) < max_per_tag:
            kept.append(p)
            counts[primary] = counts.get(primary, 0) + 1
    return kept


# ============================================================
# ENHANCED INDICATOR SCORES (Stochastic, OBV, PSAR, BB pos,
# Support/Resistance, Fibonacci)
# ============================================================

def _enhanced_indicator_score(sig: dict) -> dict:
    """Score derived from the FULL indicator suite (each 0-1)."""
    scores = {}

    # Stochastic — bullish if oversold, bearish if overbought
    k = sig.get("stoch_k")
    if k is not None:
        if k <= 20:    scores["stochastic"] = 0.85   # oversold = bounce setup
        elif k < 80:   scores["stochastic"] = 0.70   # healthy zone
        else:          scores["stochastic"] = 0.30   # overbought
    else:
        scores["stochastic"] = 0.50

    # OBV — institutional buying confirmation
    scores["obv_trend"] = 0.85 if sig.get("obv_rising") else 0.40

    # Parabolic SAR — trend confirmation
    scores["psar_trend"] = 0.85 if sig.get("above_psar") else 0.30

    # Bollinger position — prefer middle/lower, penalize upper
    bb_pos = sig.get("bb_position", 0.5)
    if bb_pos < 0.2:    scores["bb_position"] = 0.85
    elif bb_pos < 0.6:  scores["bb_position"] = 0.75
    elif bb_pos < 0.85: scores["bb_position"] = 0.55
    else:               scores["bb_position"] = 0.30

    # Support/Resistance — prefer near support, far from resistance
    d_sup = sig.get("distance_to_support_pct", 50)
    d_res = sig.get("distance_to_resistance_pct", 50)
    upside_room = min(d_res / 10.0, 1.0)
    safety = 1.0 - min(d_sup / 15.0, 1.0)
    scores["sr_setup"] = round(upside_room * 0.6 + safety * 0.4, 3)

    # Fibonacci — golden buy zone (38.2%-50%)
    close = sig.get("close")
    f382, f50, f618 = sig.get("fib_382"), sig.get("fib_50"), sig.get("fib_618")
    if close and f382 and f618:
        if f382 <= close <= f50:    scores["fibonacci"] = 0.85
        elif f50 < close <= f618:   scores["fibonacci"] = 0.75
        elif close < f382:          scores["fibonacci"] = 0.60
        else:                       scores["fibonacci"] = 0.50
    else:
        scores["fibonacci"] = 0.50


    # ADX — trend strength bonus
    adx_v = sig.get("adx")
    if adx_v is not None:
        if adx_v > 40:    scores["adx_strength"] = 0.90  # very strong trend
        elif adx_v > 25:  scores["adx_strength"] = 0.80  # solid trend
        elif adx_v > 20:  scores["adx_strength"] = 0.60
        else:             scores["adx_strength"] = 0.35  # choppy / no trend
    else:
        scores["adx_strength"] = 0.50

    # +DI vs -DI direction
    scores["di_direction"] = 0.80 if sig.get("di_bullish") else 0.30

    # VWAP — bullish if above, bearish if below
    if sig.get("above_vwap"):
        d = sig.get("vwap_distance_pct", 0)
        # Best zone: 0-3% above VWAP (uptrend, not stretched)
        if 0 < d <= 3:    scores["vwap_position"] = 0.85
        elif d <= 6:      scores["vwap_position"] = 0.70
        else:             scores["vwap_position"] = 0.50  # too extended
    else:
        scores["vwap_position"] = 0.30

    # Candlestick patterns
    if sig.get("cdl_bullish_signal"):
        scores["candlestick"] = 0.85
    elif sig.get("cdl_bearish_signal"):
        scores["candlestick"] = 0.20
    elif sig.get("cdl_doji"):
        scores["candlestick"] = 0.50  # indecision
    else:
        scores["candlestick"] = 0.55

    return scores


def score_indicators(sig: dict) -> float:
    """Average of all enhanced indicator sub-scores (0-1)."""
    sub = _enhanced_indicator_score(sig)
    return round(sum(sub.values()) / len(sub), 4) if sub else 0.5


# ============================================================
# CORE COMPONENT SCORES (existing)
# ============================================================

def score_trend(sig: dict) -> float:
    score = 0.5
    c, s20, s50, s200 = sig.get("close"), sig.get("sma_20"), sig.get("sma_50"), sig.get("sma_200")
    if not all([c, s20, s50]):
        return 0.5
    if c > s20 > s50: score += 0.25
    if s200 and c > s200: score += 0.15
    if c < s20 < s50: score -= 0.30
    return max(0.0, min(1.0, score))


def score_momentum(sig: dict) -> float:
    score = 0.5
    rsi = sig.get("rsi_14")
    macd, macd_sig, macd_hist = sig.get("macd"), sig.get("macd_signal"), sig.get("macd_hist")
    if rsi is not None:
        if 50 <= rsi <= 70: score += 0.20
        elif rsi > 70:      score -= 0.15
        elif rsi < 30:      score += 0.10
    if macd is not None and macd_sig is not None:
        if macd > macd_sig and (macd_hist or 0) > 0: score += 0.20
        elif macd < macd_sig:                         score -= 0.15
    return max(0.0, min(1.0, score))


def score_volatility(sig: dict) -> float:
    atr, close = sig.get("atr_14"), sig.get("close")
    if not (atr and close): return 0.5
    vol_pct = atr / close
    if 0.01 <= vol_pct <= 0.03: return 0.75
    elif vol_pct > 0.06:        return 0.30
    return 0.5


def score_volume(sig: dict) -> float:
    vr = sig.get("vol_ratio")
    if vr is None: return 0.5
    if vr > 2.0:   return 0.85
    if vr > 1.3:   return 0.70
    if vr < 0.7:   return 0.35
    return 0.5


# ============================================================
# SECTOR BOOST
# ============================================================

def sector_bonus(ticker: str, sector_cfg: dict) -> Dict:
    if not is_semi(ticker):
        return {"multiplier": 1.0, "tag": None, "category": None, "ai_weight": 0.0}
    meta = get_semi_meta(ticker)
    base_boost = sector_cfg.get("semi_boost", 1.10)
    ai_boost   = sector_cfg.get("ai_boost", 0.20)
    ai_weight  = meta.get("ai_weight", 0.5)
    multiplier = base_boost + (ai_boost * ai_weight)
    return {
        "multiplier": round(multiplier, 3),
        "tag": "SEMI" + (" / AI" if ai_weight >= 0.75 else ""),
        "category": meta.get("category"),
        "ai_weight": ai_weight,
    }


# ============================================================
# COMPOSITE
# ============================================================

def composite_score(sig: dict, fund_score: float, sent_score: float,
                    weights: dict, ticker: str = "", sector_cfg: dict = None) -> Dict:
    enhanced = _enhanced_indicator_score(sig)
    indicators_avg = round(sum(enhanced.values()) / len(enhanced), 4)

    components = {
        "trend":        score_trend(sig),
        "momentum":     score_momentum(sig),
        "volatility":   score_volatility(sig),
        "volume":       score_volume(sig),
        "fundamentals": fund_score,
        "sentiment":    sent_score,
        "indicators":   indicators_avg,   # NEW combined sub-score
    }

    raw = sum(components[k] * weights.get(k, 0) for k in components)
    bonus = sector_bonus(ticker, sector_cfg or {})
    boosted = max(0.0, min(1.0, raw * bonus["multiplier"]))

    components["raw_score"]   = round(raw, 4)
    components["sector_mult"] = bonus["multiplier"]
    components["sector_tag"]  = bonus["tag"]
    components["sector_cat"]  = bonus["category"]
    components["composite"]   = round(boosted, 4)

    # Surface individual indicator scores for transparency / LLM context
    for k, v in enhanced.items():
        components[f"ind_{k}"] = v

    return components
