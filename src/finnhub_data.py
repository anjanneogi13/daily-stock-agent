"""Real fundamentals from Finnhub — parallel + cached for speed without losing data."""
import os, time, json, requests, threading
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Optional

BASE = "https://finnhub.io/api/v1"
CACHE_DIR = Path("data/finnhub_cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL = timedelta(days=1)

# Token bucket rate limiter — safely under 60 req/min
_LOCK = threading.Lock()
_CALL_TIMES = []
_RATE_LIMIT = 55  # requests per minute (5 buffer)
_WINDOW = 60.0    # seconds


def _throttle():
    """Block until safe to make next call (token-bucket style)."""
    with _LOCK:
        now = time.time()
        # Drop calls older than window
        _CALL_TIMES[:] = [t for t in _CALL_TIMES if now - t < _WINDOW]
        if len(_CALL_TIMES) >= _RATE_LIMIT:
            sleep_for = _WINDOW - (now - _CALL_TIMES[0]) + 0.1
            time.sleep(max(sleep_for, 0))
            now = time.time()
            _CALL_TIMES[:] = [t for t in _CALL_TIMES if now - t < _WINDOW]
        _CALL_TIMES.append(now)


def _cache_path(ticker: str) -> Path:
    return CACHE_DIR / f"{ticker.upper()}.json"


def _load_cache(ticker: str) -> Optional[dict]:
    p = _cache_path(ticker)
    if not p.exists():
        return None
    try:
        data = json.loads(p.read_text())
        cached_at = datetime.fromisoformat(data["_cached_at"])
        if datetime.now() - cached_at < CACHE_TTL:
            return data["payload"]
    except Exception:
        pass
    return None


def _save_cache(ticker: str, payload: dict):
    try:
        _cache_path(ticker).write_text(json.dumps({
            "_cached_at": datetime.now().isoformat(),
            "payload": payload,
        }))
    except Exception:
        pass


def _get(endpoint: str, params: dict, retries: int = 2) -> Optional[dict]:
    key = os.getenv("FINNHUB_API_KEY")
    if not key:
        return None
    params["token"] = key
    for attempt in range(retries + 1):
        _throttle()
        try:
            r = requests.get(f"{BASE}/{endpoint}", params=params, timeout=15)
            if r.status_code == 200:
                return r.json()
            if r.status_code == 429:
                time.sleep(5 * (attempt + 1))
                continue
        except Exception:
            time.sleep(2)
    return None


def fetch_fundamentals(ticker: str) -> Dict:
    """Returns fundamentals dict, with disk caching + retries."""
    cached = _load_cache(ticker)
    if cached is not None:
        return cached

    metric = _get("stock/metric", {"symbol": ticker, "metric": "all"})
    profile = _get("stock/profile2", {"symbol": ticker})

    out = {
        "trailingPE": None, "earningsQuarterlyGrowth": None,
        "profitMargins": None, "debtToEquity": None,
        "marketCap": None, "sector": "N/A", "shortName": ticker,
    }
    if metric and "metric" in metric:
        m = metric["metric"]
        out["trailingPE"] = m.get("peTTM") or m.get("peBasicExclExtraTTM")
        eps_g = m.get("epsGrowthQuarterlyYoy")
        out["earningsQuarterlyGrowth"] = (eps_g / 100.0) if eps_g is not None else None
        pm = m.get("netProfitMarginTTM")
        out["profitMargins"] = (pm / 100.0) if pm is not None else None
        out["debtToEquity"] = m.get("totalDebt/totalEquityAnnual")
    if profile:
        out["marketCap"] = (profile.get("marketCapitalization") or 0) * 1_000_000
        out["sector"] = profile.get("finnhubIndustry") or "N/A"
        out["shortName"] = profile.get("name") or ticker

    _save_cache(ticker, out)
    return out
