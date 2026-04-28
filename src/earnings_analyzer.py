"""Earnings analysis: beat/miss history, momentum, analyst recommendations.
Adds an 'earnings_quality' score (0-1) for any ticker."""
import os
import json
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List
from dotenv import load_dotenv

load_dotenv()

_FINNHUB = "https://finnhub.io/api/v1"
_KEY = os.getenv("FINNHUB_API_KEY", "")
_CACHE_DIR = Path("data/earnings_cache")
_CACHE_DIR.mkdir(parents=True, exist_ok=True)
_CACHE_TTL = timedelta(hours=24)


def _cached_get(ticker: str, kind: str):
    p = _CACHE_DIR / f"{ticker}_{kind}.json"
    if p.exists() and (datetime.now().timestamp() - p.stat().st_mtime) < _CACHE_TTL.total_seconds():
        try:
            return json.loads(p.read_text())
        except Exception:
            pass
    return None


def _cache_put(ticker: str, kind: str, data):
    try:
        (_CACHE_DIR / f"{ticker}_{kind}.json").write_text(json.dumps(data))
    except Exception:
        pass


def fetch_earnings_history(ticker: str) -> List[Dict]:
    """Fetch last 4-8 quarters of EPS actual vs estimate."""
    cached = _cached_get(ticker, "earnings")
    if cached is not None:
        return cached
    if not _KEY:
        return []
    try:
        r = requests.get(f"{_FINNHUB}/stock/earnings",
                         params={"symbol": ticker, "limit": 8, "token": _KEY}, timeout=15)
        if r.status_code != 200:
            return []
        data = r.json() or []
        _cache_put(ticker, "earnings", data)
        return data
    except Exception as e:
        print(f"[earnings] {ticker} fetch error: {e}")
        return []


def fetch_recommendations(ticker: str) -> List[Dict]:
    """Fetch analyst recommendation trends (last several months)."""
    cached = _cached_get(ticker, "recs")
    if cached is not None:
        return cached
    if not _KEY:
        return []
    try:
        r = requests.get(f"{_FINNHUB}/stock/recommendation",
                         params={"symbol": ticker, "token": _KEY}, timeout=15)
        if r.status_code != 200:
            return []
        data = r.json() or []
        _cache_put(ticker, "recs", data)
        return data
    except Exception as e:
        print(f"[earnings] {ticker} recs error: {e}")
        return []


def analyze_earnings(ticker: str) -> Dict:
    """Compute earnings quality metrics + 0-1 composite score."""
    out = {
        "earnings_quality": 0.5,
        "beat_rate": None,
        "avg_surprise_pct": None,
        "eps_momentum": None,        # sequential growth
        "last_eps_actual": None,
        "last_eps_estimate": None,
        "last_eps_surprise_pct": None,
        "analyst_buy_pct": None,
        "analyst_total": None,
        "rec_trend": None,           # "improving" | "stable" | "deteriorating"
        "quarters_analyzed": 0,
    }

    # === EARNINGS HISTORY ===
    earnings = fetch_earnings_history(ticker)
    if earnings:
        # Filter rows with both actual and estimate
        clean = [e for e in earnings
                 if e.get("actual") is not None and e.get("estimate") is not None]
        out["quarters_analyzed"] = len(clean)

        if clean:
            beats = sum(1 for e in clean if e["actual"] > e["estimate"])
            out["beat_rate"] = round(beats / len(clean), 2)

            surprises = []
            for e in clean:
                if e["estimate"] != 0:
                    surprises.append((e["actual"] - e["estimate"]) / abs(e["estimate"]) * 100)
            if surprises:
                out["avg_surprise_pct"] = round(sum(surprises) / len(surprises), 2)

            # Most recent quarter
            latest = clean[0]
            out["last_eps_actual"] = latest["actual"]
            out["last_eps_estimate"] = latest["estimate"]
            if latest["estimate"] != 0:
                out["last_eps_surprise_pct"] = round(
                    (latest["actual"] - latest["estimate"]) / abs(latest["estimate"]) * 100, 2)

            # EPS momentum: latest vs 4 quarters ago (YoY)
            if len(clean) >= 5:
                older = clean[4]
                if older["actual"] and older["actual"] != 0:
                    out["eps_momentum"] = round(
                        (latest["actual"] - older["actual"]) / abs(older["actual"]) * 100, 2)

    # === ANALYST RECOMMENDATIONS ===
    recs = fetch_recommendations(ticker)
    if recs:
        latest = recs[0]
        total = (latest.get("strongBuy", 0) + latest.get("buy", 0)
                 + latest.get("hold", 0) + latest.get("sell", 0)
                 + latest.get("strongSell", 0))
        if total > 0:
            buys = latest.get("strongBuy", 0) + latest.get("buy", 0)
            out["analyst_buy_pct"] = round(buys / total * 100, 1)
            out["analyst_total"] = total

            # Trend: compare latest vs 3 months ago
            if len(recs) >= 3:
                old = recs[2]
                old_total = (old.get("strongBuy", 0) + old.get("buy", 0)
                             + old.get("hold", 0) + old.get("sell", 0)
                             + old.get("strongSell", 0))
                if old_total > 0:
                    old_buys = old.get("strongBuy", 0) + old.get("buy", 0)
                    old_pct = old_buys / old_total * 100
                    delta = out["analyst_buy_pct"] - old_pct
                    if delta > 5:
                        out["rec_trend"] = "improving"
                    elif delta < -5:
                        out["rec_trend"] = "deteriorating"
                    else:
                        out["rec_trend"] = "stable"

    # === COMPOSITE SCORE ===
    sub_scores = []

    # Beat rate (35% weight)
    if out["beat_rate"] is not None:
        if out["beat_rate"] >= 0.85:    s = 0.95
        elif out["beat_rate"] >= 0.70:  s = 0.80
        elif out["beat_rate"] >= 0.55:  s = 0.65
        elif out["beat_rate"] >= 0.40:  s = 0.45
        else:                            s = 0.25
        sub_scores.append((s, 0.35))

    # Avg surprise (20% weight)
    if out["avg_surprise_pct"] is not None:
        if out["avg_surprise_pct"] >= 10:    s = 0.95
        elif out["avg_surprise_pct"] >= 5:   s = 0.80
        elif out["avg_surprise_pct"] >= 0:   s = 0.60
        elif out["avg_surprise_pct"] >= -5:  s = 0.40
        else:                                 s = 0.20
        sub_scores.append((s, 0.20))

    # EPS YoY momentum (20%)
    if out["eps_momentum"] is not None:
        if out["eps_momentum"] >= 30:    s = 0.95
        elif out["eps_momentum"] >= 15:  s = 0.80
        elif out["eps_momentum"] >= 0:   s = 0.60
        elif out["eps_momentum"] >= -10: s = 0.40
        else:                             s = 0.20
        sub_scores.append((s, 0.20))

    # Analyst buy % (15%)
    if out["analyst_buy_pct"] is not None:
        if out["analyst_buy_pct"] >= 75:   s = 0.95
        elif out["analyst_buy_pct"] >= 60: s = 0.80
        elif out["analyst_buy_pct"] >= 45: s = 0.60
        elif out["analyst_buy_pct"] >= 30: s = 0.40
        else:                               s = 0.20
        sub_scores.append((s, 0.15))

    # Recommendation trend (10%)
    if out["rec_trend"]:
        s = {"improving": 0.90, "stable": 0.60, "deteriorating": 0.25}[out["rec_trend"]]
        sub_scores.append((s, 0.10))

    if sub_scores:
        total_w = sum(w for _, w in sub_scores)
        out["earnings_quality"] = round(sum(s * w for s, w in sub_scores) / total_w, 3)

    return out


if __name__ == "__main__":
    import sys
    tickers = sys.argv[1:] if len(sys.argv) > 1 else ["NVDA", "AVGO", "TSM", "AMD"]
    for t in tickers:
        print(f"\n=== {t} ===")
        a = analyze_earnings(t)
        for k, v in a.items():
            print(f"  {k}: {v}")
