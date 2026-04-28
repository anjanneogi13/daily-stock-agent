"""Daily market news fetcher + Gemini-powered sentiment & narrative analysis.
Pulls general market news from Finnhub, classifies sentiment, identifies dominant themes."""
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
_GEMINI_KEY = os.getenv("GEMINI_API_KEY", "") or os.getenv("GOOGLE_API_KEY", "")
_CACHE_DIR = Path("data/news_cache")
_CACHE_DIR.mkdir(parents=True, exist_ok=True)
_CACHE_TTL = timedelta(hours=4)


def _cache_path(category: str) -> Path:
    return _CACHE_DIR / f"market_{category}_{datetime.now().strftime('%Y%m%d_%H')}.json"


def fetch_market_news(limit: int = 40) -> List[Dict]:
    """Fetch top market-moving headlines from Finnhub general news."""
    if not _KEY:
        return []

    cache = _cache_path("general")
    if cache.exists() and (datetime.now().timestamp() - cache.stat().st_mtime) < _CACHE_TTL.total_seconds():
        try:
            return json.loads(cache.read_text())[:limit]
        except Exception:
            pass

    try:
        r = requests.get(f"{_FINNHUB}/news",
                         params={"category": "general", "token": _KEY}, timeout=15)
        if r.status_code != 200:
            return []
        items = r.json() or []
        # Sort by datetime desc (most recent first)
        items.sort(key=lambda x: x.get("datetime", 0), reverse=True)
        cache.write_text(json.dumps(items))
        return items[:limit]
    except Exception as e:
        print(f"[market_news] fetch error: {e}")
        return []


def analyze_market_sentiment(headlines: List[Dict], model: str = "gemini-2.5-flash-lite") -> Dict:
    """Use Gemini to classify market sentiment + extract dominant narratives."""
    default = {
        "sentiment": "neutral",
        "score": 0.5,
        "narratives": [],
        "key_risks": [],
        "key_catalysts": [],
        "summary": "Unable to analyze.",
    }

    if not headlines or not _GEMINI_KEY:
        return default

    # Build compact headline list for prompt
    head_text = "\n".join(
        f"- [{h.get('source','?')}] {h.get('headline','')[:140]}"
        for h in headlines[:30]
    )

    prompt = f"""You are a senior macro market strategist analyzing today's news for a quant trading agent.

Analyze these {len(headlines[:30])} top market headlines and respond with STRICT JSON only:

{head_text}

Respond with this EXACT JSON structure (no markdown, no extra text):
{{
  "sentiment": "bullish" | "neutral" | "bearish",
  "score": <float 0.0 to 1.0 where 0=very bearish, 0.5=neutral, 1=very bullish>,
  "narratives": [<3-5 short dominant themes, e.g. "AI capex peaking", "Fed pivot expected">],
  "key_risks": [<2-3 concrete downside risks for US equities today>],
  "key_catalysts": [<2-3 concrete upside catalysts>],
  "summary": "<1-2 sentence executive summary for a trader>"
}}"""

    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={_GEMINI_KEY}"
        r = requests.post(url, json={
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.3, "maxOutputTokens": 800},
        }, timeout=30)
        if r.status_code != 200:
            print(f"[market_news] Gemini error {r.status_code}: {r.text[:200]}")
            return default
        text = r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        # Strip markdown fences if present
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:].strip()
        result = json.loads(text)
        # Validate required keys
        for k in default:
            result.setdefault(k, default[k])
        return result
    except Exception as e:
        print(f"[market_news] Analysis error: {e}")
        return default


def get_market_briefing() -> Dict:
    """One-shot: fetch + analyze. Returns full briefing dict."""
    headlines = fetch_market_news(limit=40)
    sentiment = analyze_market_sentiment(headlines)
    return {
        "headlines_count": len(headlines),
        "top_headlines": [h.get("headline", "")[:120] for h in headlines[:5]],
        **sentiment,
    }


if __name__ == "__main__":
    import sys
    print("Fetching daily market briefing...\n")
    b = get_market_briefing()
    print(f"Sentiment: {b['sentiment'].upper()} (score: {b['score']})")
    print(f"\nSummary: {b['summary']}\n")
    print("Dominant Narratives:")
    for n in b["narratives"]:
        print(f"  • {n}")
    print("\nKey Risks:")
    for r in b["key_risks"]:
        print(f"  ⚠ {r}")
    print("\nKey Catalysts:")
    for c in b["key_catalysts"]:
        print(f"  🚀 {c}")
