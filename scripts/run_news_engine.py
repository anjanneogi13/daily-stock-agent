"""
Master runner: fetch news → classify → update watchlist → Telegram alerts.
Runs every 30 min during market hours and pre/post-market.
"""
import os
import sys
import json
import requests
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.news_engine import fetch_all_news, append_news_log
from src.news_classifier import classify_batch
from src.watchlist_manager import add_from_news, get_watchlist_tickers


TELEGRAM_THRESHOLD = 0.7  # tradeable_score above which we Telegram alert
MAX_ALERTS_PER_RUN = 5    # avoid spamming Telegram


def send_telegram(text: str):
    bot = os.getenv("TELEGRAM_BOT_TOKEN")
    chat = os.getenv("TELEGRAM_CHAT_ID")
    if not bot or not chat:
        print("[news_engine] Telegram not configured — skipping alert")
        return
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{bot}/sendMessage",
            json={"chat_id": chat, "text": text, "parse_mode": "Markdown",
                  "disable_web_page_preview": True},
            timeout=10,
        )
        if r.status_code != 200:
            print(f"[news_engine] Telegram HTTP {r.status_code}: {r.text[:120]}")
    except Exception as e:
        print(f"[news_engine] Telegram send failed: {e}")


def format_alert(item: dict) -> str:
    cls = item["classification"]
    emoji = "🟢" if cls.get("sentiment") == "bullish" else "🔴" if cls.get("sentiment") == "bearish" else "⚪"
    cat = cls.get("category", "other").replace("_", " ").upper()
    score_pct = int(cls.get("tradeable_score", 0) * 100)
    ticker = cls.get("primary_ticker") or "?"

    return (
        f"{emoji} *NEWS ALERT* — *${ticker}*  ({score_pct}/100)\n"
        f"📰 {cat}  ·  {cls.get('action_window', 'next_day').replace('_', ' ')}\n\n"
        f"*{item.get('headline','')[:200]}*\n\n"
        f"💡 {cls.get('rationale','')}\n\n"
        f"🔗 [Read]({item.get('url','')})  · src: {item.get('source','')}"
    )


def main():
    print(f"[news_engine] Run started at {datetime.now().isoformat()}")

    # Pull news from last 60 min, plus Yahoo on current watchlist
    watchlist_tickers = get_watchlist_tickers()[:20]
    items = fetch_all_news(watchlist_tickers=watchlist_tickers, since_minutes=60)
    print(f"[news_engine] Fetched {len(items)} fresh items")

    if not items:
        print("[news_engine] No fresh news this run")
        return

    # Classify (cap at 20 to control Claude costs)
    classified = classify_batch(items, max_items=20)
    append_news_log(classified)
    print(f"[news_engine] Classified {len(classified)} items")

    # Update watchlist
    added = add_from_news(classified)
    print(f"[news_engine] Added {len(added)} new tickers to watchlist")

    # Telegram alerts for high-impact news
    high_impact = [
        c for c in classified
        if c.get("classification", {}).get("tradeable_score", 0) >= TELEGRAM_THRESHOLD
        and c.get("classification", {}).get("primary_ticker")
    ]
    high_impact.sort(key=lambda x: x["classification"]["tradeable_score"], reverse=True)

    for item in high_impact[:MAX_ALERTS_PER_RUN]:
        send_telegram(format_alert(item))
        print(f"[news_engine] Alerted: {item['classification'].get('primary_ticker')} "
              f"({item['classification'].get('tradeable_score'):.2f})")

    # Summary
    wl = get_watchlist_tickers()[:10]
    print(f"[news_engine] Top 10 watchlist: {wl}")
    print(f"[news_engine] Done.")


if __name__ == "__main__":
    main()