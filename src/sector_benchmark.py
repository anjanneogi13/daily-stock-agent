"""
Sector Benchmark — map a pick's sector/tag to its representative ETF.

Why: alpha vs SPY conflates market beta with sector beta.
A SEMI pick that beat SPY by +1% but underperformed SOXX by -3%
is NOT alpha — it's just sector beta + a worse-than-peer pick.

Usage:
    etf = resolve_sector_etf(sector="Technology", tag="SEMI / AI")
    # -> "SOXX"  (tag wins over generic sector)
"""
from typing import Optional


# Tag mappings (more specific — checked FIRST)
TAG_TO_ETF = {
    "SEMI": "SOXX",
    "AI": "QQQ",          # AI exposure ~ NASDAQ-100 best proxy
    "BIOTECH": "XBI",
    "FINTECH": "ARKF",
    "CLOUD": "WCLD",
    "CYBER": "HACK",
    "EV": "DRIV",
    "DEFENSE": "ITA",
}

# Sector mappings (yfinance sector names)
SECTOR_TO_ETF = {
    "Technology": "XLK",
    "Healthcare": "XLV",
    "Financial Services": "XLF",
    "Financial": "XLF",
    "Financials": "XLF",
    "Energy": "XLE",
    "Consumer Cyclical": "XLY",
    "Consumer Defensive": "XLP",
    "Consumer Staples": "XLP",
    "Consumer Discretionary": "XLY",
    "Industrials": "XLI",
    "Communication Services": "XLC",
    "Communications": "XLC",
    "Utilities": "XLU",
    "Real Estate": "XLRE",
    "Basic Materials": "XLB",
    "Materials": "XLB",
}


def resolve_sector_etf(sector: Optional[str] = None,
                        tag: Optional[str] = None) -> str:
    """
    Pick the most-specific ETF benchmark for this pick.
    Priority: tag (specific) > sector (generic) > SPY (fallback).
    """
    # Tag wins (more specific)
    if tag:
        primary = tag.split("/")[0].strip().upper()
        if primary in TAG_TO_ETF:
            return TAG_TO_ETF[primary]

    # Then sector
    if sector and sector in SECTOR_TO_ETF:
        return SECTOR_TO_ETF[sector]

    # Fallback
    return "SPY"
