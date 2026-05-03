"""
Fetch float / short interest data for monster scoring.
Cached to disk to avoid hammering yfinance.
"""
import json
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime, timedelta

CACHE_DIR = Path("data/monster_cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL_HOURS = 24


def _cache_path(ticker: str) -> Path:
    return CACHE_DIR / f"{ticker.upper()}.json"


def _is_fresh(p: Path) -> bool:
    if not p.exists():
        return False
    mtime = datetime.fromtimestamp(p.stat().st_mtime)
    return (datetime.now() - mtime) < timedelta(hours=CACHE_TTL_HOURS)


def get_monster_data(ticker: str) -> Dict[str, Optional[float]]:
    """
    Returns {short_pct_of_float, float_shares} — values may be None on failure.
    Cached for 24h to avoid yfinance rate limits.
    """
    cp = _cache_path(ticker)
    if _is_fresh(cp):
        try:
            return json.loads(cp.read_text())
        except Exception:
            pass

    result = {"short_pct_of_float": None, "float_shares": None}
    try:
        import yfinance as yf
        info = yf.Ticker(ticker).info
        spo = info.get("shortPercentOfFloat")
        fs = info.get("floatShares")
        if spo is not None:
            result["short_pct_of_float"] = float(spo)
        if fs is not None:
            result["float_shares"] = float(fs)
        cp.write_text(json.dumps(result))
    except Exception as e:
        print(f"[monster_data] {ticker}: {type(e).__name__}: {str(e)[:60]}")

    return result
