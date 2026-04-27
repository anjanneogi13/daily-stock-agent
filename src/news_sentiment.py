"""News + simple sentiment via Yahoo RSS."""
import feedparser
from typing import List, Dict

POSITIVE = {"beat", "surge", "rally", "upgrade", "soar", "record",
            "growth", "strong", "profit", "outperform", "buy"}
NEGATIVE = {"miss", "plunge", "downgrade", "lawsuit", "fraud", "loss",
            "weak", "cut", "decline", "underperform", "sell", "warn",
            "probe", "investigation"}

def fetch_news(ticker: str, limit: int = 5) -> List[Dict]:
    url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US"
    try:
        feed = feedparser.parse(url)
        return [{"title": e.get("title",""), "link": e.get("link",""),
                 "published": e.get("published","")} for e in feed.entries[:limit]]
    except Exception as e:
        print(f"[news] {ticker}: {e}")
        return []

def score_sentiment(news: List[Dict]) -> float:
    if not news:
        return 0.5
    pos = neg = 0
    for item in news:
        text = item["title"].lower()
        pos += sum(1 for w in POSITIVE if w in text)
        neg += sum(1 for w in NEGATIVE if w in text)
    total = pos + neg
    return 0.5 if total == 0 else pos / total
