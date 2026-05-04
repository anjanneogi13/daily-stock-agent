"""
News Engine — pulls news from Alpaca News API (primary), Yahoo Finance, and SEC EDGAR.
Returns deduplicated list of recent news items with ticker mentions.
"""
import os
import json
import time
import requests
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Dict, Set
import re

ALPACA_NEWS_URL = "https://data.alpaca.markets/v1beta1/news"
YAHOO_RSS_TPL = "https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US"
SEC_EDGAR_URL = "https://data.sec.gov/submissions/CIK{cik}.json"

NEWS_CACHE = Path("data/news_seen.json")  # dedup cache (id → ts)
NEWS_LOG = Path("data/news_log.jsonl")
DEDUP_TTL_HOURS = 48


def _load_seen() -> Dict[str, str]:
    if NEWS_CACHE.exists():
        try:
            return json.loads(NEWS_CACHE.read_text())
        except Exception:
            return {}
    return {}


def _save_seen(seen: Dict[str, str]):
    NEWS_CACHE.parent.mkdir(parents=True, exist_ok=True)
    # Trim entries older than DEDUP_TTL_HOURS
    cutoff = datetime.now(timezone.utc) - timedelta(hours=DEDUP_TTL_HOURS)
    pruned = {}
    for k, v in seen.items():
        try:
            t = datetime.fromisoformat(v.replace("Z", "+00:00"))
            if t >= cutoff:
                pruned[k] = v
        except Exception:
            pass
    NEWS_CACHE.write_text(json.dumps(pruned))


def fetch_alpaca_news(limit: int = 50, since_minutes: int = 60) -> List[Dict]:
    """Pull recent news from Alpaca News API (free with paper account)."""
    key = os.getenv("ALPACA_API_KEY")
    secret = os.getenv("ALPACA_API_SECRET")
    if not key or not secret:
        print("[news_engine] No Alpaca credentials — skipping Alpaca news")
        return []

    start = (datetime.now(timezone.utc) - timedelta(minutes=since_minutes)).isoformat()
    headers = {"APCA-API-KEY-ID": key, "APCA-API-SECRET-KEY": secret}
    params = {
        "limit": limit,
        "start": start,
        "sort": "desc",
        "include_content": "false",
    }

    try:
        r = requests.get(ALPACA_NEWS_URL, headers=headers, params=params, timeout=15)
        if r.status_code != 200:
            print(f"[news_engine] Alpaca news HTTP {r.status_code}: {r.text[:200]}")
            return []
        data = r.json().get("news", [])
        items = []
        for n in data:
            items.append({
                "id": f"alpaca_{n.get('id')}",
                "source": "alpaca",
                "ticker_list": n.get("symbols", []) or [],
                "headline": n.get("headline", "")[:300],
                "summary": (n.get("summary") or "")[:600],
                "url": n.get("url", ""),
                "published_at": n.get("created_at") or n.get("updated_at"),
                "author": n.get("author", ""),
            })
        return items
    except Exception as e:
        print(f"[news_engine] Alpaca fetch failed: {type(e).__name__}: {str(e)[:120]}")
        return []


def fetch_yahoo_rss(tickers: List[str]) -> List[Dict]:
    """Pull recent news from Yahoo Finance RSS for specific tickers (lightweight backup)."""
    items = []
    for tk in tickers[:20]:  # cap to avoid spamming
        try:
            url = YAHOO_RSS_TPL.format(ticker=tk)
            r = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
            if r.status_code != 200:
                continue
            # Parse XML loosely (no feedparser dependency)
            text = r.text
            # Extract <item>...</item> blocks
            for match in list(re.finditer(r"<item>(.*?)</item>", text, re.DOTALL))[:3]:
                block = match.group(1)
                title = re.search(r"<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>", block, re.DOTALL)
                link = re.search(r"<link>(.*?)</link>", block, re.DOTALL)
                pub = re.search(r"<pubDate>(.*?)</pubDate>", block, re.DOTALL)
                desc = re.search(r"<description>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</description>", block, re.DOTALL)
                if title and link:
                    items.append({
                        "id": f"yahoo_{tk}_{abs(hash(title.group(1)))}",
                        "source": "yahoo",
                        "ticker_list": [tk],
                        "headline": (title.group(1) or "").strip()[:300],
                        "summary": (desc.group(1) if desc else "").strip()[:600],
                        "url": (link.group(1) or "").strip(),
                        "published_at": (pub.group(1) if pub else "").strip(),
                        "author": "yahoo",
                    })
            time.sleep(0.2)  # be polite
        except Exception:
            continue
    return items


def fetch_all_news(watchlist_tickers: List[str] = None,
                   since_minutes: int = 60) -> List[Dict]:
    """Master: fetch all news from all sources, dedupe by id."""
    seen = _load_seen()
    fresh = []

    # Source 1: Alpaca News (broad market coverage)
    alpaca_items = fetch_alpaca_news(limit=50, since_minutes=since_minutes)
    for it in alpaca_items:
        if it["id"] not in seen:
            fresh.append(it)
            seen[it["id"]] = datetime.now(timezone.utc).isoformat()

    # Source 2: Yahoo RSS for watchlist tickers (deeper coverage)
    if watchlist_tickers:
        yahoo_items = fetch_yahoo_rss(watchlist_tickers)
        for it in yahoo_items:
            if it["id"] not in seen:
                fresh.append(it)
                seen[it["id"]] = datetime.now(timezone.utc).isoformat()

    _save_seen(seen)
    return fresh


def append_news_log(items: List[Dict]):
    """Append news items to data/news_log.jsonl."""
    if not items:
        return
    NEWS_LOG.parent.mkdir(parents=True, exist_ok=True)
    with NEWS_LOG.open("a") as f:
        for it in items:
            f.write(json.dumps(it) + "\n")


if __name__ == "__main__":
    # Smoke test
    items = fetch_all_news(since_minutes=120)
    print(f"Fetched {len(items)} fresh news items")
    for it in items[:5]:
        print(f"  [{it['source']}] {it['headline'][:80]}  ({','.join(it['ticker_list'][:3])})")