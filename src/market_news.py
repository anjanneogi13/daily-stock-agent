"""Daily market news fetcher + Claude-powered sentiment & narrative analysis.
Pulls general market news from Finnhub, classifies sentiment, identifies dominant themes.
Priority: Claude Sonnet 4.5 → Gemini fallback → neutral default.
"""
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
_ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY", "")
_GEMINI_KEY = os.getenv("GEMINI_API_KEY", "") or os.getenv("GOOGLE_API_KEY", "")
_CACHE_DIR = Path("data/news_cache")
_CACHE_DIR.mkdir(parents=True, exist_ok=True)
_CACHE_TTL = timedelta(hours=4)
_SENTIMENT_CACHE_TTL = timedelta(hours=4)

CLAUDE_MODEL = "claude-sonnet-4-5"


def _cache_path(category: str) -> Path:
    return _CACHE_DIR / f"market_{category}_{datetime.now().strftime('%Y%m%d_%H')}.json"


def _sentiment_cache_path() -> Path:
    return _CACHE_DIR / f"sentiment_{datetime.now().strftime('%Y%m%d_%H')}.json"


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
        items.sort(key=lambda x: x.get("datetime", 0), reverse=True)
        cache.write_text(json.dumps(items))
        return items[:limit]
    except Exception as e:
        print(f"[market_news] fetch error: {e}")
        return []


def _build_sentiment_prompt(headlines: List[Dict]) -> str:
    head_text = "\n".join(
        f"- [{h.get('source','?')}] {h.get('headline','')[:140]}"
        for h in headlines[:30]
    )
    return f"""You are a senior macro market strategist analyzing today's news for a quant trading agent.

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


def _strip_markdown_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:].strip()
        if text.endswith("```"):
            text = text[:-3].strip()
    return text


def _claude_sentiment(prompt: str) -> str:
    """Call Claude. Returns raw text response or raises."""
    import anthropic
    client = anthropic.Anthropic(api_key=_ANTHROPIC_KEY)
    resp = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=800,
        temperature=0.3,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.content[0].text.strip()


def _gemini_sentiment(prompt: str, model: str = "gemini-2.5-flash-lite") -> str:
    """Call Gemini via REST. Returns raw text response or raises."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={_GEMINI_KEY}"
    r = requests.post(url, timeout=30, json={
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.3, "maxOutputTokens": 800},
    })
    if r.status_code != 200:
        raise RuntimeError(f"Gemini HTTP {r.status_code}: {r.text[:200]}")
    return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()


def analyze_market_sentiment(headlines: List[Dict], model: str = CLAUDE_MODEL) -> Dict:
    """Use Claude (with Gemini fallback) to classify market sentiment + extract narratives."""
    default = {
        "sentiment": "neutral",
        "score": 0.5,
        "narratives": [],
        "key_risks": [],
        "key_catalysts": [],
        "summary": "Unable to analyze.",
    }

    if not headlines:
        return default

    # Cache hit?
    scache = _sentiment_cache_path()
    if scache.exists() and (datetime.now().timestamp() - scache.stat().st_mtime) < _SENTIMENT_CACHE_TTL.total_seconds():
        try:
            cached = json.loads(scache.read_text())
            print(f"[market_news] ✓ sentiment cache hit ({scache.name})")
            return cached
        except Exception:
            pass

    prompt = _build_sentiment_prompt(headlines)
    raw_text = None
    used = None

    # 1) Claude (primary)
    if _ANTHROPIC_KEY:
        try:
            raw_text = _claude_sentiment(prompt)
            used = "Claude"
        except Exception as e:
            print(f"[market_news] Claude failed: {str(e)[:160]}")

    # 2) Gemini (fallback)
    if not raw_text and _GEMINI_KEY:
        try:
            raw_text = _gemini_sentiment(prompt)
            used = "Gemini"
        except Exception as e:
            print(f"[market_news] Gemini fallback failed: {str(e)[:160]}")

    if not raw_text:
        print("[market_news] no LLM available — returning neutral default")
        return default

    # Parse JSON
    try:
        text = _strip_markdown_fences(raw_text)
        result = json.loads(text)
        for k in default:
            result.setdefault(k, default[k])
        print(f"[market_news] ✓ sentiment via {used}: {result.get('sentiment')} ({result.get('score')})")
        # Cache it
        try:
            scache.write_text(json.dumps(result))
        except Exception:
            pass
        return result
    except Exception as e:
        print(f"[market_news] JSON parse error from {used}: {e}")
        print(f"[market_news] raw text was: {raw_text[:300]}")
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
