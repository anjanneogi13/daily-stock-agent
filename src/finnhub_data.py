"""Finnhub fundamentals fetcher with full field mapping + caching."""
import os
import json
import time
import requests
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

_BASE = "https://finnhub.io/api/v1"
_KEY = os.getenv("FINNHUB_API_KEY", "")
_CACHE_DIR = Path("data/finnhub_cache")
_CACHE_DIR.mkdir(parents=True, exist_ok=True)
_CACHE_TTL = timedelta(hours=24)


def _cache_get(ticker: str):
    p = _CACHE_DIR / f"{ticker}.json"
    if not p.exists():
        return None
    try:
        d = json.loads(p.read_text())
        if datetime.now() - datetime.fromisoformat(d["at"]) < _CACHE_TTL:
            return d["data"]
    except Exception:
        pass
    return None


def _cache_put(ticker: str, data: dict):
    try:
        (_CACHE_DIR / f"{ticker}.json").write_text(
            json.dumps({"at": datetime.now().isoformat(), "data": data})
        )
    except Exception:
        pass


def _safe_pct(v):
    """Convert percent-as-number (e.g. 95.27) to decimal (0.9527)."""
    return (v / 100.0) if v is not None else None


def fetch_fundamentals(ticker: str) -> dict:
    """Fetch full fundamentals for a ticker. Cached 24h."""
    cached = _cache_get(ticker)
    if cached:
        return cached

    out = {
        # Core
        "shortName": ticker, "sector": "N/A", "marketCap": None,
        # Valuation
        "trailingPE": None, "pegRatio": None, "priceToBook": None,
        "priceToSales": None,
        # Growth
        "earningsQuarterlyGrowth": None, "epsGrowth5Y": None,
        "revenueGrowth": None, "revenueGrowth5Y": None,
        # Profitability
        "profitMargins": None, "returnOnEquity": None,
        "returnOnEquity5Y": None, "pretaxMargin": None,
        # EPS
        "eps": None, "epsAnnual": None,
        # Health
        "debtToEquity": None, "longTermDebtToEquity": None,
        "currentRatio": None,
        # Cash flow
        "freeCashFlowPerShare": None, "freeCashFlowYield": None,
        "cashFlowPerShare": None,
        # Performance
        "relativeToSP500_52w": None,
    }

    if not _KEY:
        print(f"[finnhub] No API key — returning empty for {ticker}")
        _cache_put(ticker, out)
        return out

    # 1) Profile (name + sector + market cap)
    try:
        r = requests.get(f"{_BASE}/stock/profile2",
                         params={"symbol": ticker, "token": _KEY}, timeout=10)
        if r.status_code == 200:
            p = r.json()
            out["shortName"] = p.get("name") or ticker
            out["sector"] = p.get("finnhubIndustry") or "N/A"
            mc = p.get("marketCapitalization")
            # Finnhub returns marketCap in millions
            if mc:
                out["marketCap"] = float(mc) * 1_000_000
    except Exception as e:
        print(f"[finnhub] {ticker} profile error: {e}")

    # 2) Metrics (the big one)
    try:
        r = requests.get(f"{_BASE}/stock/metric",
                         params={"symbol": ticker, "metric": "all", "token": _KEY},
                         timeout=15)
        if r.status_code == 200:
            m = r.json().get("metric", {}) or {}

            # === VALUATION ===
            out["trailingPE"] = m.get("peTTM") or m.get("peAnnual")
            out["pegRatio"] = m.get("pegTTM")
            out["priceToBook"] = m.get("pbAnnual") or m.get("pb")
            out["priceToSales"] = m.get("psTTM") or m.get("psAnnual")

            # === GROWTH (Finnhub returns percentages; convert to decimals) ===
            out["earningsQuarterlyGrowth"] = _safe_pct(m.get("epsGrowthQuarterlyYoy"))
            out["epsGrowth5Y"] = _safe_pct(m.get("epsGrowth5Y"))
            out["revenueGrowth"] = _safe_pct(m.get("revenueGrowthQuarterlyYoy"))
            out["revenueGrowth5Y"] = _safe_pct(m.get("revenueGrowth5Y"))

            # === PROFITABILITY ===
            out["profitMargins"] = _safe_pct(m.get("netProfitMarginTTM") or m.get("netProfitMarginAnnual"))
            out["returnOnEquity"] = _safe_pct(m.get("roeTTM"))
            out["returnOnEquity5Y"] = _safe_pct(m.get("roe5Y"))
            out["pretaxMargin"] = _safe_pct(m.get("pretaxMarginTTM"))

            # === EPS ===
            out["eps"] = m.get("epsBasicExclExtraItemsTTM") or m.get("epsExclExtraItemsTTM") or m.get("epsAnnual")
            out["epsAnnual"] = m.get("epsAnnual")

            # === BALANCE SHEET HEALTH ===
            out["debtToEquity"] = m.get("totalDebt/totalEquityAnnual") or m.get("totalDebt/totalEquityQuarterly")
            out["longTermDebtToEquity"] = m.get("longTermDebt/equityAnnual")
            out["currentRatio"] = m.get("currentRatioAnnual") or m.get("currentRatioQuarterly")

            # === CASH FLOW ===
            out["cashFlowPerShare"] = m.get("cashFlowPerShareTTM") or m.get("cashFlowPerShareAnnual")
            # FCF yield = 1 / (Price-to-FCF). pfcfShareTTM = Price / FCF-per-share
            pfcf = m.get("pfcfShareTTM") or m.get("pfcfShareAnnual")
            if pfcf and pfcf > 0:
                out["freeCashFlowYield"] = round(1.0 / pfcf, 4)
            # FCF per share derived: cashFlowPerShare is operating CF; use pfcf to back into FCF
            # If we have market cap and pfcf, FCF total = marketCap / pfcf
            if out["marketCap"] and pfcf and pfcf > 0:
                out["freeCashFlow"] = round(out["marketCap"] / pfcf, 2)
            else:
                out["freeCashFlow"] = None

            # === PERFORMANCE (relative strength vs SPY) ===
            out["relativeToSP500_52w"] = m.get("priceRelativeToS&P50052Week")

    except Exception as e:
        print(f"[finnhub] {ticker} metric error: {e}")

    _cache_put(ticker, out)
    return out


# Backwards-compat alias
fetch_info = fetch_fundamentals



# ═══════════════════════════════════════════════════════════════
# Real-time quote (E2c — May 4 2026)
# Used for cross-validating yfinance prices to catch stale/wrong data.
# ═══════════════════════════════════════════════════════════════
def fetch_finnhub_quote(ticker: str) -> dict:
    """Fetch real-time quote from Finnhub /quote endpoint.

    Returns dict with: current, prev_close, high, low, open, timestamp.
    All fields None if Finnhub unavailable or ticker invalid.

    Finnhub /quote response schema:
      c  = current price
      pc = previous close
      h  = high (today)
      l  = low (today)
      o  = open
      t  = timestamp (epoch)
    """
    out = {"current": None, "prev_close": None, "high": None,
           "low": None, "open": None, "timestamp": None, "source": "finnhub"}

    import os, urllib.request, json as _json
    key = os.getenv("FINNHUB_API_KEY")
    if not key:
        out["error"] = "no_api_key"
        return out

    try:
        url = f"https://finnhub.io/api/v1/quote?symbol={ticker}&token={key}"
        with urllib.request.urlopen(url, timeout=5) as r:
            data = _json.loads(r.read())
        # Finnhub returns c=0 for invalid tickers — treat as None
        c = data.get("c")
        if c == 0 or c is None:
            out["error"] = "invalid_ticker_or_no_data"
            return out
        out["current"]    = float(c)
        out["prev_close"] = float(data.get("pc") or 0) or None
        out["high"]       = float(data.get("h") or 0) or None
        out["low"]        = float(data.get("l") or 0) or None
        out["open"]       = float(data.get("o") or 0) or None
        out["timestamp"]  = data.get("t")
    except Exception as e:
        out["error"] = f"{type(e).__name__}: {str(e)[:60]}"

    return out


def cross_validate_price(ticker: str,
                          primary_price: float,
                          warn_threshold_pct: float = 2.0,
                          block_threshold_pct: float = 5.0) -> dict:
    """Cross-check primary (yfinance) price against Finnhub.

    Returns dict:
      {
        "is_valid":       bool,    # False if disagreement > block_threshold
        "should_warn":    bool,    # True if disagreement > warn_threshold
        "primary_price":  float,
        "second_price":   float | None,
        "disagreement_pct": float | None,  # |a-b|/avg * 100
        "reason":         str,     # human-readable
      }

    Graceful: if Finnhub unavailable, returns is_valid=True (don't block trades
    just because second source is down).
    """
    result = {
        "is_valid": True,
        "should_warn": False,
        "primary_price": primary_price,
        "second_price": None,
        "disagreement_pct": None,
        "reason": "",
    }

    # 1. Primary price sanity (catches the XXYYZZ123 case)
    if primary_price is None or primary_price <= 0:
        result["is_valid"] = False
        result["reason"] = f"primary price invalid ({primary_price!r})"
        return result

    # 2. Fetch second source
    quote = fetch_finnhub_quote(ticker)
    second = quote.get("current")

    if second is None:
        # Finnhub down or no key — graceful pass (don't punish for infra issues)
        result["reason"] = f"no second source: {quote.get('error', 'unavailable')}"
        return result

    # 3. Compare
    result["second_price"] = second
    avg = (primary_price + second) / 2
    disagreement = abs(primary_price - second) / avg * 100
    result["disagreement_pct"] = round(disagreement, 2)

    if disagreement > block_threshold_pct:
        result["is_valid"] = False
        result["reason"] = (
            f"price disagreement {disagreement:.1f}% > block threshold "
            f"{block_threshold_pct}% (yfinance ${primary_price:.2f} vs "
            f"finnhub ${second:.2f})"
        )
    elif disagreement > warn_threshold_pct:
        result["should_warn"] = True
        result["reason"] = (
            f"price disagreement {disagreement:.1f}% > warn threshold "
            f"{warn_threshold_pct}% (yfinance ${primary_price:.2f} vs "
            f"finnhub ${second:.2f})"
        )
    else:
        result["reason"] = (
            f"prices agree within {disagreement:.2f}% "
            f"(yfinance ${primary_price:.2f} vs finnhub ${second:.2f})"
        )

    return result
