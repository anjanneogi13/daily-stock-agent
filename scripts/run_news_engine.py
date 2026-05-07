"""
Master runner: fetch news → classify → update watchlist → Telegram alerts.
Runs every 30 min during market hours and pre/post-market.
"""
from __future__ import annotations

import os
import sys
import json
import requests
from pathlib import Path
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.news_engine import fetch_all_news, append_news_log
from src.news_classifier import classify_batch
from src.watchlist_manager import add_from_news, get_watchlist_tickers
from src.news_signals import add_signal_from_classification, stats as signals_stats  # PR #77


TELEGRAM_THRESHOLD = 0.85  # PR #77: raised from 0.7 to cut noise (~60% fewer alerts)
MAX_ALERTS_PER_RUN = 3    # PR #77: lowered from 5 to focus on signal
ET = ZoneInfo("America/New_York")


def news_engine_run_status_path(today: str | None = None, data_dir: Path = Path("data")) -> Path:
    """Return the JSONL run-status artifact path for the US trading session."""
    day = today or datetime.now(timezone.utc).astimezone(ET).strftime("%Y-%m-%d")
    return data_dir / f"news_engine_run_status_{day}.jsonl"


def build_news_engine_run_status(
    *,
    event: str,
    result: str,
    reason: str = "",
    items_fetched: int = 0,
    items_classified: int = 0,
    signals_added: int = 0,
    hard_blocks: int = 0,
    watchlist_added: int = 0,
    high_impact_count: int = 0,
    telegram_enabled: bool = False,
    telegram_attempted: int = 0,
    now: datetime | None = None,
) -> dict:
    """Build an auditable, monitoring-only News Engine run-status row."""
    now_et = (now or datetime.now(timezone.utc)).astimezone(ET)
    return {
        "date": now_et.strftime("%Y-%m-%d"),
        "timestamp_et": now_et.isoformat(timespec="seconds"),
        "timestamp_utc": now_et.astimezone(timezone.utc).isoformat(timespec="seconds"),
        "workflow": "news-engine",
        "event": event,
        "result": result,
        "reason": reason,
        "items_fetched": int(items_fetched or 0),
        "items_classified": int(items_classified or 0),
        "signals_added": int(signals_added or 0),
        "hard_blocks": int(hard_blocks or 0),
        "watchlist_added": int(watchlist_added or 0),
        "high_impact_count": int(high_impact_count or 0),
        "telegram_enabled": bool(telegram_enabled),
        "telegram_attempted": int(telegram_attempted or 0),
        "mode": "monitoring_only",
        "paper_trading_enabled": False,
        "live_trading_enabled": False,
        "official_picks_created": False,
        "github": {
            "workflow": os.getenv("GITHUB_WORKFLOW", ""),
            "event_name": os.getenv("GITHUB_EVENT_NAME", ""),
            "run_id": os.getenv("GITHUB_RUN_ID", ""),
            "run_attempt": os.getenv("GITHUB_RUN_ATTEMPT", ""),
            "sha": os.getenv("GITHUB_SHA", ""),
            "ref": os.getenv("GITHUB_REF", ""),
        },
    }


def append_news_engine_run_status(
    *,
    event: str,
    result: str,
    reason: str = "",
    items_fetched: int = 0,
    items_classified: int = 0,
    signals_added: int = 0,
    hard_blocks: int = 0,
    watchlist_added: int = 0,
    high_impact_count: int = 0,
    telegram_enabled: bool = False,
    telegram_attempted: int = 0,
    path: Path | None = None,
    now: datetime | None = None,
) -> Path:
    """Append one News Engine run-status row and return the path written."""
    record = build_news_engine_run_status(
        event=event,
        result=result,
        reason=reason,
        items_fetched=items_fetched,
        items_classified=items_classified,
        signals_added=signals_added,
        hard_blocks=hard_blocks,
        watchlist_added=watchlist_added,
        high_impact_count=high_impact_count,
        telegram_enabled=telegram_enabled,
        telegram_attempted=telegram_attempted,
        now=now,
    )
    out = path or news_engine_run_status_path(record["date"])
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, sort_keys=True) + "\n")
    return out


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

    counters = {
        "items_fetched": 0,
        "items_classified": 0,
        "signals_added": 0,
        "hard_blocks": 0,
        "watchlist_added": 0,
        "high_impact_count": 0,
        "telegram_enabled": False,
        "telegram_attempted": 0,
    }

    append_news_engine_run_status(
        event="news_engine_started",
        result="started",
        reason="News Engine workflow started",
    )

    try:
        # Pull news from last 60 min, plus Yahoo on current watchlist
        watchlist_tickers = get_watchlist_tickers()[:20]
        items = fetch_all_news(watchlist_tickers=watchlist_tickers, since_minutes=60)
        counters["items_fetched"] = len(items)
        print(f"[news_engine] Fetched {len(items)} fresh items")

        if not items:
            print("[news_engine] No fresh news this run")
            append_news_engine_run_status(
                event="news_engine_completed",
                result="no_fresh_news",
                reason="No fresh news items returned by sources",
                **counters,
            )
            return

        # Classify (cap at 20 to control Claude costs)
        classified = classify_batch(items, max_items=20)
        counters["items_classified"] = len(classified)
        append_news_log(classified)
        print(f"[news_engine] Classified {len(classified)} items")

        # ─── PR #77: Extract trading signals from classifications ────
        signals_added = 0
        hard_blocks = 0
        for item in classified:
            sig = add_signal_from_classification(item)
            if sig:
                signals_added += 1
                if sig.get("hard_block"):
                    hard_blocks += 1
                    print(f"[news_signals] 🚨 HARD BLOCK: {sig['ticker']} ({sig['catalyst']})")
                else:
                    arrow = "⬆" if sig['score_delta'] > 0 else "⬇"
                    print(f"[news_signals] {arrow} {sig['ticker']:6s} "
                          f"{sig['score_delta']:+.2f} ({sig['catalyst']})")

        counters["signals_added"] = signals_added
        counters["hard_blocks"] = hard_blocks

        if signals_added > 0:
            s = signals_stats()
            print(f"[news_signals] State: {s['total_active']} active "
                  f"({s['bullish_count']} bull, {s['bearish_count']} bear, "
                  f"{len(s['hard_blocks'])} blocks)")
            if s['hard_blocks']:
                print(f"[news_signals] Hard blocks: {s['hard_blocks']}")

        # Update watchlist
        added = add_from_news(classified)
        counters["watchlist_added"] = len(added)
        print(f"[news_engine] Added {len(added)} new tickers to watchlist")

        # Telegram alerts for high-impact news
        high_impact = [
            c for c in classified
            if c.get("classification", {}).get("tradeable_score", 0) >= TELEGRAM_THRESHOLD
            and c.get("classification", {}).get("primary_ticker")
        ]
        high_impact.sort(key=lambda x: x["classification"]["tradeable_score"], reverse=True)
        counters["high_impact_count"] = len(high_impact)

        # GATE: news Telegram alerts are INTERNAL by default (per founder design intent).
        # News is for the agent's brain to digest, not the user's phone.
        # To re-enable for power-user mode, set ENABLE_NEWS_TELEGRAM=true in env.
        news_telegram_enabled = os.getenv("ENABLE_NEWS_TELEGRAM", "false").lower() == "true"
        counters["telegram_enabled"] = news_telegram_enabled
        for item in high_impact[:MAX_ALERTS_PER_RUN]:
            ticker = item['classification'].get('primary_ticker')
            score = item['classification'].get('tradeable_score', 0)
            if news_telegram_enabled:
                counters["telegram_attempted"] += 1
                send_telegram(format_alert(item))
                print(f"[news_engine] Alerted (TELEGRAM): {ticker} ({score:.2f})")
            else:
                print(f"[news_engine] Alerted (INTERNAL only): {ticker} ({score:.2f})")

        # Summary
        wl = get_watchlist_tickers()[:10]
        print(f"[news_engine] Top 10 watchlist: {wl}")
        print(f"[news_engine] Done.")

        append_news_engine_run_status(
            event="news_engine_completed",
            result="completed",
            reason="News Engine completed successfully",
            **counters,
        )

    except Exception as exc:
        append_news_engine_run_status(
            event="news_engine_failed",
            result="failed",
            reason=f"{type(exc).__name__}: {str(exc)[:200]}",
            **counters,
        )
        raise


if __name__ == "__main__":
    main()
