"""
News Classifier — uses Claude Sonnet 4.5 to score headlines for trading impact.
Returns: sentiment, urgency, category, tradeable_score, rationale.
"""
import os
import json
from typing import Dict, List
from datetime import datetime

CLASSIFIER_PROMPT = """You are a senior equity analyst. Classify this news headline for trading impact.

Headline: {headline}
Summary: {summary}
Tickers mentioned: {tickers}
Source: {source}
Published: {published}

Respond with ONLY valid JSON, no markdown:
{{
  "sentiment": "bullish" | "bearish" | "neutral",
  "sentiment_score": 0.0 to 1.0,
  "urgency": "high" | "medium" | "low",
  "urgency_score": 0.0 to 1.0,
  "category": "earnings_beat" | "earnings_miss" | "fda_approval" | "fda_rejection" | "ma_acquirer" | "ma_target" | "downgrade" | "upgrade" | "guidance_raise" | "guidance_cut" | "lawsuit" | "product_launch" | "macro" | "rumor" | "other",
  "tradeable_score": 0.0 to 1.0,
  "primary_ticker": "TICKER" or null,
  "rationale": "1-sentence explanation",
  "action_window": "intraday" | "next_day" | "this_week" | "ignore"
}}

tradeable_score guide:
- 0.9-1.0: huge confirmed catalyst (FDA approval, earnings beat by >20%, M&A deal)
- 0.7-0.9: meaningful catalyst worth acting on (earnings beat 5-20%, upgrade by major bank)
- 0.5-0.7: notable but mixed (guidance change, executive change)
- 0.3-0.5: minor news (analyst note, secondary product news)
- 0.0-0.3: noise (rumor, opinion, already priced in)
"""


def classify_news(item: Dict) -> Dict:
    """Classify a single news item using Claude. Returns enriched dict."""
    try:
        import anthropic
    except ImportError:
        return _heuristic_fallback(item)

    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        return _heuristic_fallback(item)

    client = anthropic.Anthropic(api_key=key)
    prompt = CLASSIFIER_PROMPT.format(
        headline=item.get("headline", "")[:300],
        summary=item.get("summary", "")[:500],
        tickers=", ".join(item.get("ticker_list", [])[:5]) or "none",
        source=item.get("source", "unknown"),
        published=item.get("published_at", ""),
    )

    try:
        resp = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}],
        )
        text = resp.content[0].text.strip()
        # Strip markdown fences if present
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        result = json.loads(text.strip())
        return {**item, "classification": result, "classified_at": datetime.now().isoformat()}
    except Exception as e:
        print(f"[news_classifier] Claude failed: {type(e).__name__}: {str(e)[:120]}")
        return _heuristic_fallback(item)


def _heuristic_fallback(item: Dict) -> Dict:
    """Cheap keyword-based fallback when Claude unavailable."""
    h = (item.get("headline", "") + " " + item.get("summary", "")).lower()

    bullish_kw = ["beats", "surge", "soars", "approval", "upgrade", "raises guidance",
                  "record", "all-time high", "acquire", "acquired", "wins contract"]
    bearish_kw = ["miss", "plunge", "drops", "downgrade", "cuts guidance", "lawsuit",
                  "investigation", "recall", "fraud", "warning"]
    high_urgency_kw = ["fda", "earnings", "merger", "acquisition", "halted"]

    sentiment_score = 0.5
    if any(kw in h for kw in bullish_kw):
        sentiment_score = 0.75
        sentiment = "bullish"
    elif any(kw in h for kw in bearish_kw):
        sentiment_score = 0.25
        sentiment = "bearish"
    else:
        sentiment = "neutral"

    urgency_score = 0.7 if any(kw in h for kw in high_urgency_kw) else 0.4
    tradeable = round((abs(sentiment_score - 0.5) * 2) * urgency_score, 2)

    return {
        **item,
        "classification": {
            "sentiment": sentiment,
            "sentiment_score": sentiment_score,
            "urgency": "high" if urgency_score > 0.6 else "medium",
            "urgency_score": urgency_score,
            "category": "other",
            "tradeable_score": tradeable,
            "primary_ticker": (item.get("ticker_list") or [None])[0],
            "rationale": "heuristic classification (Claude unavailable)",
            "action_window": "next_day" if tradeable < 0.6 else "intraday",
        },
        "classified_at": datetime.now().isoformat(),
    }


def classify_batch(items: List[Dict], max_items: int = 20) -> List[Dict]:
    """Classify up to max_items news items. Skips low-priority sources first."""
    # Prioritize Alpaca over Yahoo (Alpaca = pre-vetted)
    items_sorted = sorted(items, key=lambda x: 0 if x.get("source") == "alpaca" else 1)
    return [classify_news(it) for it in items_sorted[:max_items]]


if __name__ == "__main__":
    # Smoke test
    test_item = {
        "headline": "MaxLinear beats Q1 EPS estimates by 25%, raises full-year guidance",
        "summary": "MaxLinear (MXL) reported Q1 EPS of $0.45 vs estimate of $0.36, beating by 25%. Company also raised FY guidance citing strong demand in connectivity products.",
        "ticker_list": ["MXL"],
        "source": "alpaca",
        "published_at": datetime.now().isoformat(),
    }
    result = classify_news(test_item)
    print(json.dumps(result["classification"], indent=2))