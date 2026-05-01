"""
Watchlist Manager — maintains a 3-day rolling watchlist of news-flagged tickers.
Picks consume this watchlist as a score boost the next morning.

PR #68: Added freshness-weighted boost — fresh news (<4h) gets up to
2× boost so news catalysts actually drive picks (not just nudge them).
"""
import json
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import List, Dict

WATCHLIST_PATH = Path("data/watchlist.json")
WATCHLIST_TTL_HOURS = 72  # 3 days
MIN_TRADEABLE_SCORE = 0.5


def _load() -> Dict:
    if WATCHLIST_PATH.exists():
        try:
            return json.loads(WATCHLIST_PATH.read_text())
        except Exception:
            pass
    return {"items": []}


def _save(data: Dict):
    WATCHLIST_PATH.parent.mkdir(parents=True, exist_ok=True)
    WATCHLIST_PATH.write_text(json.dumps(data, indent=2))


def _prune_expired(items: List[Dict]) -> List[Dict]:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=WATCHLIST_TTL_HOURS)
    out = []
    for it in items:
        try:
            t = datetime.fromisoformat(it["added_at"].replace("Z", "+00:00"))
            if t >= cutoff:
                out.append(it)
        except Exception:
            continue
    return out


def _hours_old(item: Dict) -> float:
    """Return hours since item was added to watchlist."""
    try:
        t = datetime.fromisoformat(item["added_at"].replace("Z", "+00:00"))
        delta = datetime.now(timezone.utc) - t
        return delta.total_seconds() / 3600
    except Exception:
        return 999.0  # treat as ancient if missing


def _freshness_multiplier(hours_old: float) -> float:
    """
    PR #68: Freshness multiplier for news boost.
      <  4h  : 2.0× (fresh catalyst — overnight news, premarket)
      <  8h  : 1.5× (this morning's news)
      < 24h  : 1.0× (yesterday's news, baseline)
      < 48h  : 0.6× (stale)
      ≥ 48h  : 0.3× (very stale)
    """
    if hours_old < 4:   return 2.0
    if hours_old < 8:   return 1.5
    if hours_old < 24:  return 1.0
    if hours_old < 48:  return 0.6
    return 0.3


def add_from_news(classified_items: List[Dict]) -> List[Dict]:
    """Add high-tradeable-score news to watchlist. Returns newly added items."""
    data = _load()
    data["items"] = _prune_expired(data.get("items", []))
    added = []

    for item in classified_items:
        cls = item.get("classification", {})
        score = cls.get("tradeable_score", 0)
        ticker = cls.get("primary_ticker") or (item.get("ticker_list") or [None])[0]

        if not ticker or score < MIN_TRADEABLE_SCORE:
            continue

        existing = next((x for x in data["items"] if x["ticker"] == ticker), None)
        if existing:
            if score > existing.get("tradeable_score", 0):
                existing.update({
                    "tradeable_score": score,
                    "sentiment": cls.get("sentiment"),
                    "category": cls.get("category"),
                    "rationale": cls.get("rationale"),
                    "headline": item.get("headline"),
                    "url": item.get("url"),
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                })
            continue

        new_entry = {
            "ticker": ticker,
            "tradeable_score": score,
            "sentiment": cls.get("sentiment"),
            "category": cls.get("category"),
            "rationale": cls.get("rationale"),
            "action_window": cls.get("action_window"),
            "headline": item.get("headline"),
            "url": item.get("url"),
            "source": item.get("source"),
            "added_at": datetime.now(timezone.utc).isoformat(),
        }
        data["items"].append(new_entry)
        added.append(new_entry)

    _save(data)
    return added


def get_watchlist() -> List[Dict]:
    """Return current (non-expired) watchlist sorted by tradeable_score desc."""
    data = _load()
    items = _prune_expired(data.get("items", []))
    return sorted(items, key=lambda x: x.get("tradeable_score", 0), reverse=True)


def get_watchlist_tickers(bullish_only: bool = False) -> List[str]:
    """
    Return just tickers, ordered by score.
    PR #68: bullish_only flag — used by universe.py to expand candidate pool.
    """
    items = get_watchlist()
    if bullish_only:
        items = [it for it in items if it.get("sentiment") == "bullish"]
    return [it["ticker"] for it in items]


def watchlist_score_boost(ticker: str) -> float:
    """
    Return score boost for a stock based on watchlist presence.

    PR #68 enhancements:
      - Bullish boost: max +0.30 (was +0.15) when news is fresh (<4h)
      - Bearish penalty: max -0.30 when fresh bearish news
      - Freshness-weighted: fresh news has 2× impact
    """
    items = get_watchlist()
    match = next((it for it in items if it["ticker"] == ticker), None)
    if not match:
        return 0.0

    hours_old = _hours_old(match)
    fresh_mult = _freshness_multiplier(hours_old)

    # Base = tradeable_score * 0.15 (was max +0.15 flat)
    # Now: tradeable_score * 0.15 * freshness (max +0.30 on fresh news)
    base = match.get("tradeable_score", 0) * 0.15 * fresh_mult

    # Cap boost at ±0.30 to prevent runaway scoring
    base = max(-0.30, min(0.30, base))

    if match.get("sentiment") == "bearish":
        return -base
    return base


def watchlist_meta(ticker: str) -> Dict:
    """PR #68: Return rich watchlist metadata for a ticker (for display/debug)."""
    items = get_watchlist()
    match = next((it for it in items if it["ticker"] == ticker), None)
    if not match:
        return {}
    return {
        "ticker": ticker,
        "sentiment": match.get("sentiment"),
        "category": match.get("category"),
        "headline": match.get("headline", "")[:80],
        "hours_old": round(_hours_old(match), 1),
        "freshness_mult": _freshness_multiplier(_hours_old(match)),
        "tradeable_score": match.get("tradeable_score"),
        "boost_applied": round(watchlist_score_boost(ticker), 3),
    }


if __name__ == "__main__":
    print(f"Current watchlist ({len(get_watchlist())} items):")
    for it in get_watchlist():
        boost = watchlist_score_boost(it["ticker"])
        hrs = _hours_old(it)
        print(f"  {it['ticker']:6s} score={it['tradeable_score']:.2f} "
              f"sent={it.get('sentiment','?'):8s} "
              f"age={hrs:5.1f}h boost={boost:+.3f}  "
              f"{(it.get('headline') or '')[:60]}")