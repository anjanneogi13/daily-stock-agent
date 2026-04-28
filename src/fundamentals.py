"""Fundamental scoring using full Finnhub field suite.
Inputs: dict from finnhub_data.fetch_fundamentals()
Output: composite 0-1 score."""
from typing import Dict


def score_fundamentals(info: Dict) -> float:
    """Weighted composite of 11 fundamental dimensions."""
    weights = []  # list of (sub_score, weight)

    # ============ VALUATION (35%) ============
    pe = info.get("trailingPE")
    if pe is not None and pe > 0:
        if pe < 15:        s = 0.90
        elif pe < 25:      s = 0.75
        elif pe < 40:      s = 0.55
        elif pe < 60:      s = 0.40
        else:              s = 0.25
        weights.append((s, 0.12))

    peg = info.get("pegRatio")
    if peg is not None and peg > 0:
        if peg < 1.0:      s = 0.95   # 🔥 undervalued vs growth
        elif peg < 1.5:    s = 0.80
        elif peg < 2.0:    s = 0.60
        elif peg < 3.0:    s = 0.40
        else:              s = 0.25
        weights.append((s, 0.15))

    pb = info.get("priceToBook")
    if pb is not None and pb > 0:
        if pb < 3:         s = 0.85
        elif pb < 8:       s = 0.65
        elif pb < 15:      s = 0.50
        elif pb < 30:      s = 0.40
        else:              s = 0.30
        weights.append((s, 0.04))

    ps = info.get("priceToSales")
    if ps is not None and ps > 0:
        if ps < 3:         s = 0.80
        elif ps < 10:      s = 0.65
        elif ps < 20:      s = 0.45
        else:              s = 0.30
        weights.append((s, 0.04))

    # ============ GROWTH (25%) ============
    eps_q = info.get("earningsQuarterlyGrowth")
    if eps_q is not None:
        if eps_q > 0.30:   s = 0.95
        elif eps_q > 0.15: s = 0.85
        elif eps_q > 0.05: s = 0.70
        elif eps_q > 0:    s = 0.55
        else:              s = 0.30
        weights.append((s, 0.10))

    eps5 = info.get("epsGrowth5Y")
    if eps5 is not None:
        if eps5 > 0.30:    s = 0.95
        elif eps5 > 0.15:  s = 0.85
        elif eps5 > 0.05:  s = 0.65
        elif eps5 > 0:     s = 0.50
        else:              s = 0.30
        weights.append((s, 0.08))

    rev_g = info.get("revenueGrowth") or info.get("revenueGrowth5Y")
    if rev_g is not None:
        if rev_g > 0.20:   s = 0.90
        elif rev_g > 0.10: s = 0.75
        elif rev_g > 0:    s = 0.55
        else:              s = 0.30
        weights.append((s, 0.07))

    # ============ PROFITABILITY (20%) ============
    pm = info.get("profitMargins")
    if pm is not None:
        if pm > 0.25:      s = 0.95
        elif pm > 0.15:    s = 0.80
        elif pm > 0.05:    s = 0.60
        elif pm > 0:       s = 0.45
        else:              s = 0.20
        weights.append((s, 0.10))

    roe = info.get("returnOnEquity")
    if roe is not None:
        if roe > 0.25:     s = 0.95
        elif roe > 0.15:   s = 0.80
        elif roe > 0.10:   s = 0.65
        elif roe > 0.05:   s = 0.50
        else:              s = 0.30
        weights.append((s, 0.10))

    # ============ FINANCIAL HEALTH (10%) ============
    de = info.get("debtToEquity")
    if de is not None:
        if de < 0.3:       s = 0.90
        elif de < 0.6:     s = 0.75
        elif de < 1.0:     s = 0.60
        elif de < 2.0:     s = 0.40
        else:              s = 0.25
        weights.append((s, 0.05))

    cr = info.get("currentRatio")
    if cr is not None:
        if cr > 2.0:       s = 0.85
        elif cr > 1.5:     s = 0.75
        elif cr > 1.0:     s = 0.60
        else:              s = 0.30
        weights.append((s, 0.05))

    # ============ CASH FLOW (8%) ============
    fcf_yield = info.get("freeCashFlowYield")
    if fcf_yield is not None:
        if fcf_yield > 0.06:    s = 0.90
        elif fcf_yield > 0.03:  s = 0.75
        elif fcf_yield > 0.01:  s = 0.60
        elif fcf_yield > 0:     s = 0.45
        else:                   s = 0.20
        weights.append((s, 0.08))

    # ============ RELATIVE STRENGTH (2%) ============
    rs = info.get("relativeToSP500_52w")
    if rs is not None:
        if rs > 30:        s = 0.90    # crushing market
        elif rs > 10:      s = 0.75
        elif rs > 0:       s = 0.60
        elif rs > -10:     s = 0.45
        else:              s = 0.25
        weights.append((s, 0.02))

    if not weights:
        return 0.5
    total_w = sum(w for _, w in weights)
    return round(sum(s * w for s, w in weights) / total_w, 3)


def passes_filters(info: Dict, cfg: Dict) -> bool:
    """Hard quality filters before scoring."""
    f = (cfg or {}).get("filters", {})
    mc = info.get("marketCap")
    if mc is not None and mc < f.get("min_market_cap", 0):
        return False
    return True
