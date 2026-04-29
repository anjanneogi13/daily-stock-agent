"""News fetcher + materiality classifier."""
import os, json, urllib.request, urllib.parse
from datetime import datetime, timedelta, timezone

FINNHUB_KEY = os.environ.get("FINNHUB_API_KEY", "")

# Material keywords → category
MATERIAL_KEYWORDS = {
    "downgrade":   ["downgrade", "downgraded", "cut to sell", "lowered to", "price target cut"],
    "upgrade":     ["upgrade", "upgraded", "raised to buy", "price target raised", "outperform"],
    "earnings":    ["earnings beat", "earnings miss", "eps beat", "eps miss", "revenue beat",
                    "revenue miss", "guides", "preannounce"],
    "guidance":    ["guidance", "outlook", "forecast cut", "forecast raised", "warns"],
    "lawsuit":     ["lawsuit", "sued", "investigation", "probe", "fraud", "sec charges"],
    "ma":          ["acquires", "acquisition", "merger", "buyout", "takeover", "to acquire"],
}

def fetch_recent_news(ticker: str, lookback_min: int = 45) -> list:
    """Returns recent news items from Finnhub (free tier)."""
    if not FINNHUB_KEY:
        return []
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
    url = (
        f"https://finnhub.io/api/v1/company-news?"
        f"symbol={ticker}&from={yesterday}&to={today}&token={FINNHUB_KEY}"
    )
    try:
        with urllib.request.urlopen(url, timeout=8) as r:
            items = json.loads(r.read())
    except Exception as e:
        print(f"[news] {ticker} fetch failed: {e}")
        return []

    cutoff = datetime.now(timezone.utc) - timedelta(minutes=lookback_min)
    recent = []
    for it in items:
        ts = it.get("datetime", 0)
        if not ts:
            continue
        when = datetime.fromtimestamp(ts, tz=timezone.utc)
        if when >= cutoff:
            recent.append(it)
    return recent

def classify_material(headline: str) -> str | None:
    """Returns category name if headline is material, else None."""
    if not headline:
        return None
    h = headline.lower()
    for cat, kws in MATERIAL_KEYWORDS.items():
        if any(kw in h for kw in kws):
            return cat
    return None
