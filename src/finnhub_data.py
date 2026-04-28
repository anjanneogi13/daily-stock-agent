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
