"""Fundamental scoring + filters — None-safe."""

def score_fundamentals(info: dict) -> float:
    if not info:
        return 0.5
    score = 0.5
    pe = info.get("trailingPE")
    eps_growth = info.get("earningsQuarterlyGrowth")
    profit_margin = info.get("profitMargins")
    debt_to_equity = info.get("debtToEquity")
    market_cap = info.get("marketCap") or 0
    if pe and 0 < pe < 30:   score += 0.10
    elif pe and pe >= 50:    score -= 0.10
    if eps_growth and eps_growth > 0.10: score += 0.15
    elif eps_growth and eps_growth < 0:  score -= 0.10
    if profit_margin and profit_margin > 0.10: score += 0.10
    if debt_to_equity is not None and debt_to_equity < 100: score += 0.05
    if market_cap and market_cap > 10e9: score += 0.05
    return max(0.0, min(1.0, score))


def passes_filters(info: dict, config: dict) -> bool:
    cfg = config["universe"]
    price = info.get("currentPrice") or info.get("regularMarketPrice") or 0
    avg_vol = info.get("averageVolume") or 0
    if price and (price < cfg["min_price"] or price > cfg["max_price"]):
        return False
    if avg_vol < cfg["min_avg_volume"]:
        return False
    return True
