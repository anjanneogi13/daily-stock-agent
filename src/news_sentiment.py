"""News + improved sentiment via Yahoo RSS."""
import feedparser
from typing import List, Dict

POSITIVE = {"beat", "beats", "surge", "surges", "rally", "rallies", "upgrade",
            "upgraded", "soar", "soars", "record", "records", "growth", "strong",
            "profit", "profits", "outperform", "buy", "bullish", "raises", "raised",
            "tops", "topped", "exceeded", "boost", "expansion", "winning", "wins",
            "breakthrough", "milestone", "approved"}

NEGATIVE = {"miss", "misses", "missed", "plunge", "plunges", "downgrade",
            "downgraded", "lawsuit", "fraud", "loss", "losses", "weak", "cut",
            "cuts", "decline", "declines", "underperform", "sell", "warn",
            "warning", "probe", "investigation", "bearish", "concerns", "fears",
            "tumble", "tumbles", "slump", "drops", "fell", "falls", "halts",
            "delays", "recall", "fired"}


def fetch_news(ticker: str, limit: int = 5) -> List[Dict]:
    url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US"
    try:
        feed = feedparser.parse(url)
        return [{"title": e.get("title", ""), "link": e.get("link", ""),
                 "published": e.get("published", "")} for e in feed.entries[:limit]]
    except Exception as e:
        print(f"[news] {ticker}: {e}")
        return []


def score_sentiment(news: List[Dict]) -> float:
    """Weighted sentiment in [0, 1] with neutral baseline at 0.5.
    Requires multiple signals before moving far from 0.5."""
    if not news:
        return 0.5
    pos = neg = 0
    for item in news:
        text = item["title"].lower()
        pos += sum(1 for w in POSITIVE if w in text)
        neg += sum(1 for w in NEGATIVE if w in text)
    n_articles = len(news)
    # Net sentiment per article, dampened by article count
    net = (pos - neg) / max(n_articles, 1)
    # Map [-2, +2] net score to [0, 1] with 0.5 = neutral
    score = 0.5 + (net / 4.0)
    return max(0.05, min(0.95, score))
