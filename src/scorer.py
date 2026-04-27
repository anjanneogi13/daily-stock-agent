"""Multi-factor scoring with semiconductor sector boost."""
from typing import Dict
from .semiconductors import is_semi, get_semi_meta

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

def composite_score(sig: dict, fund_score: float, sent_score: float,
                    weights: dict, ticker: str = "", sector_cfg: dict = None) -> Dict:
    components = {
        "trend":        score_trend(sig),
        "momentum":     score_momentum(sig),
        "volatility":   score_volatility(sig),
        "volume":       score_volume(sig),
        "fundamentals": fund_score,
        "sentiment":    sent_score,
    }
    raw = sum(components[k] * weights.get(k, 0) for k in components)
    bonus = sector_bonus(ticker, sector_cfg or {})
    boosted = max(0.0, min(1.0, raw * bonus["multiplier"]))
    components["raw_score"]   = round(raw, 4)
    components["sector_mult"] = bonus["multiplier"]
    components["sector_tag"]  = bonus["tag"]
    components["sector_cat"]  = bonus["category"]
    components["composite"]   = round(boosted, 4)
    return components
