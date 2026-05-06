#!/usr/bin/env python3
"""Generate late watch-only daily ideas after the official premarket window.

This is a monitoring-only fallback for missed official daily picks.

It intentionally does NOT:
- create official picks,
- write to data/picks_log.csv,
- write to data/signal_journal.jsonl as official picks,
- create paper trades,
- enable live trading.

Output:
- data/late_daily_ideas_YYYY-MM-DD.jsonl
- data/late_daily_ideas_YYYY-MM-DD.md
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo


ET = ZoneInfo("America/New_York")
DATA_DIR = Path("data")


def _as_float(value, default: float = 0.0) -> float:
    try:
        if value in (None, "", "None"):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _now_et(now: datetime | None = None) -> datetime:
    return (now or datetime.now(timezone.utc)).astimezone(ET)


def late_ideas_path(date_str: str, data_dir: Path = DATA_DIR) -> Path:
    return data_dir / f"late_daily_ideas_{date_str}.jsonl"


def late_ideas_markdown_path(date_str: str, data_dir: Path = DATA_DIR) -> Path:
    return data_dir / f"late_daily_ideas_{date_str}.md"


def load_json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def _candidate_from_payload(payload: dict, *, source: str, now: datetime, min_score: float) -> dict | None:
    ticker = str(payload.get("ticker") or payload.get("primary_ticker") or "").strip().upper()
    if not ticker:
        return None

    sentiment = str(payload.get("sentiment") or "").strip().lower()
    if sentiment and sentiment != "bullish":
        # v1 only surfaces long-side watch-only ideas. No short architecture yet.
        return None

    action_window = payload.get("action_window")
    if str(action_window or "").strip().lower() == "ignore":
        return None

    if payload.get("hard_block") is True:
        return None

    tradeable_score = _as_float(payload.get("tradeable_score"), 0.0)
    score_delta = _as_float(payload.get("score_delta"), 0.0)

    # Normalize to a 0-100 display score. Keep it simple and auditable.
    score = round(max(0.0, min(100.0, tradeable_score * 100.0 + max(0.0, score_delta) * 100.0)), 2)
    if tradeable_score < min_score:
        return None

    headline = str(payload.get("headline") or "").strip()
    rationale = str(payload.get("rationale") or "").strip()
    reason = rationale or headline or f"{source} late watch-only idea"

    generated_at = _now_et(now)
    date_str = generated_at.strftime("%Y-%m-%d")

    return {
        "date": date_str,
        "generated_at_et": generated_at.isoformat(timespec="seconds"),
        "idea_type": "late_daily_watch_only",
        "mode": "monitoring_only",
        "watch_only": True,
        "official_premarket_pick": False,
        "paper_trading_enabled": False,
        "live_trading_enabled": False,
        "ticker": ticker,
        "source": source,
        "score": score,
        "tradeable_score": tradeable_score,
        "score_delta": score_delta,
        "sentiment": sentiment or "unknown",
        "action_window": action_window,
        "headline": headline,
        "reason": reason,
        "url": payload.get("url") or "",
        "warning": (
            "Generated after the official 09:20 ET premarket cutoff. "
            "Monitoring-only. Not a buy instruction. Not an official daily pick."
        ),
    }


def build_late_ideas(
    *,
    news_signals_path: Path = DATA_DIR / "news_signals.json",
    watchlist_path: Path = DATA_DIR / "watchlist.json",
    max_results: int = 5,
    min_score: float = 0.40,
    now: datetime | None = None,
) -> list[dict]:
    now_dt = now or datetime.now(timezone.utc)
    by_ticker: dict[str, dict] = {}

    news_signals = load_json(news_signals_path, {})
    if isinstance(news_signals, dict):
        for payload in news_signals.values():
            if not isinstance(payload, dict):
                continue
            cand = _candidate_from_payload(payload, source="news_signal", now=now_dt, min_score=min_score)
            if cand and cand["score"] > by_ticker.get(cand["ticker"], {}).get("score", -1):
                by_ticker[cand["ticker"]] = cand

    watchlist = load_json(watchlist_path, {})
    items = []
    if isinstance(watchlist, dict):
        raw = watchlist.get("items", [])
        if isinstance(raw, list):
            items = raw
    elif isinstance(watchlist, list):
        items = watchlist

    for payload in items:
        if not isinstance(payload, dict):
            continue
        cand = _candidate_from_payload(payload, source="watchlist", now=now_dt, min_score=min_score)
        if cand and cand["score"] > by_ticker.get(cand["ticker"], {}).get("score", -1):
            by_ticker[cand["ticker"]] = cand

    out = sorted(
        by_ticker.values(),
        key=lambda x: (
            -float(x.get("score") or 0),
            str(x.get("ticker") or ""),
        ),
    )
    return out[:max_results]


def format_markdown(ideas: list[dict], *, now: datetime | None = None) -> str:
    now_et = _now_et(now)
    lines = [
        "⚠️ *LATE WATCH-ONLY DAILY IDEAS*",
        "",
        f"Generated: {now_et.strftime('%Y-%m-%d %H:%M ET')}",
        "",
        "*Important:* These are NOT official premarket daily picks.",
        "They were generated after the 09:20 ET cutoff.",
        "Monitoring-only. Not buy instructions. Not paper trades.",
        "",
    ]

    if not ideas:
        lines.extend([
            "No qualified late watch-only ideas were found from current news/watchlist evidence.",
            "",
            "_Educational only. Not financial advice._",
        ])
        return "\n".join(lines)

    for i, idea in enumerate(ideas, 1):
        action = idea.get("action_window") or "unspecified"
        headline = idea.get("headline") or idea.get("reason") or ""
        lines.extend([
            f"{i}. *{idea['ticker']}* — score {idea['score']:.1f}/100",
            f"   Source: {idea.get('source', 'unknown')} | Window: {action}",
            f"   {headline[:220]}",
            "   WATCH ONLY — do not treat as an official pick or buy instruction.",
            "",
        ])

    lines.append("_Educational only. Not financial advice._")
    msg = "\n".join(lines)
    return msg[:3950] + "\n\n_(truncated)_" if len(msg) > 4000 else msg


def write_outputs(ideas: list[dict], *, data_dir: Path = DATA_DIR, now: datetime | None = None) -> tuple[Path, Path]:
    now_et = _now_et(now)
    date_str = now_et.strftime("%Y-%m-%d")
    data_dir.mkdir(parents=True, exist_ok=True)

    jsonl = late_ideas_path(date_str, data_dir=data_dir)
    with jsonl.open("w", encoding="utf-8") as f:
        for idea in ideas:
            f.write(json.dumps(idea, sort_keys=True) + "\n")

    md = late_ideas_markdown_path(date_str, data_dir=data_dir)
    md.write_text(format_markdown(ideas, now=now), encoding="utf-8")
    return jsonl, md


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-results", type=int, default=5)
    parser.add_argument("--min-score", type=float, default=0.40)
    args = parser.parse_args(argv)

    ideas = build_late_ideas(max_results=args.max_results, min_score=args.min_score)
    jsonl, md = write_outputs(ideas)
    count_file = Path("/tmp/late_daily_ideas_count")
    count_file.write_text(str(len(ideas)))

    print(f"[late-ideas] wrote {len(ideas)} idea(s) to {jsonl}")
    print(f"[late-ideas] markdown: {md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
