"""
Watchlist Manager — maintains a 3-day rolling watchlist of news-flagged tickers.
Picks consume this watchlist as a score boost the next morning.
"""
import json
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import List, Dict

WATCHLIST_PATH = Path("data/watchlist.json")
WATCHLIST_TTL_HOURS = 72  # 3 days
MIN_TRADEABLE_SCORE = 0.5  # below this, don't add to watchlist


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


def add_from_news(classified_items: List[Dict]) -> List[Dict]:
    """Add high-tradeable-score news to watchlist. Returns newly added items."""
    data = _load()
    data["items"] = _prune_expired(data.get("items", []))
    existing_tickers = {it["ticker"] for it in data["items"]}
    added = []

    for item in classified_items:
        cls = item.get("classification", {})
        score = cls.get("tradeable_score", 0)
        ticker = cls.get("primary_ticker") or (item.get("ticker_list") or [None])[0]

        if not ticker or score < MIN_TRADEABLE_SCORE:
            continue

        # If already on watchlist, update if new score is higher
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


def get_watchlist_tickers() -> List[str]:
    """Return just tickers, ordered by score."""
    return [it["ticker"] for it in get_watchlist()]


def watchlist_score_boost(ticker: str) -> float:
    """Return score boost (0-0.15) to apply to a stock based on watchlist presence."""
    items = get_watchlist()
    match = next((it for it in items if it["ticker"] == ticker), None)
    if not match:
        return 0.0
    # Bullish news → positive boost; bearish → negative (so we avoid)
    base = match.get("tradeable_score", 0) * 0.15  # max +0.15
    if match.get("sentiment") == "bearish":
        return -base
    return base


if __name__ == "__main__":
    print(f"Current watchlist ({len(get_watchlist())} items):")
    for it in get_watchlist():
        print(f"  {it['ticker']:6s} score={it['tradeable_score']:.2f} sent={it['sentiment']:8s} {it['headline'][:60]}")
        