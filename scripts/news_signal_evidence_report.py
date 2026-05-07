#!/usr/bin/env python3
"""Build a read-only News Signal Evidence Report.

This report explains how news artifacts influenced the agent without mutating
official pick stats or learning journals.

Reads:
- data/news_log.jsonl
- data/news_signals.json
- data/watchlist.json
- data/news_engine_run_status_YYYY-MM-DD.jsonl
- data/late_daily_ideas_YYYY-MM-DD.jsonl
- data/news_signal_outcomes_YYYY-MM-DD.jsonl
- data/picks_log.csv

Writes, unless --no-write:
- data/news_signal_evidence_report_YYYY-MM-DD.json
- data/news_signal_evidence_report_YYYY-MM-DD.md
"""
from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo


ET = ZoneInfo("America/New_York")
DATA_DIR = Path("data")


def _today_et() -> str:
    return datetime.now(timezone.utc).astimezone(ET).strftime("%Y-%m-%d")


def _safe_float(value, default: float = 0.0) -> float:
    try:
        if value in (None, "", "None"):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def load_json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def load_jsonl(path: Path) -> tuple[list[dict], int]:
    rows: list[dict] = []
    invalid = 0
    if not path.exists():
        return rows, invalid
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
            if isinstance(obj, dict):
                rows.append(obj)
            else:
                invalid += 1
        except Exception:
            invalid += 1
    return rows, invalid


def load_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    try:
        with path.open(newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))
    except Exception:
        return []


def _news_log_summary(rows: list[dict]) -> dict:
    by_source: dict[str, int] = {}
    by_sentiment: dict[str, int] = {}
    by_category: dict[str, int] = {}
    tickers: set[str] = set()
    high_tradeable = 0

    for row in rows:
        src = str(row.get("source") or "unknown")
        by_source[src] = by_source.get(src, 0) + 1

        cls = row.get("classification") or {}
        if isinstance(cls, dict):
            sent = str(cls.get("sentiment") or "unknown")
            cat = str(cls.get("category") or "unknown")
            by_sentiment[sent] = by_sentiment.get(sent, 0) + 1
            by_category[cat] = by_category.get(cat, 0) + 1
            if _safe_float(cls.get("tradeable_score")) >= 0.85:
                high_tradeable += 1
            tk = cls.get("primary_ticker")
            if tk:
                tickers.add(str(tk).upper())

        for tk in row.get("ticker_list") or []:
            if tk:
                tickers.add(str(tk).upper())

    return {
        "count": len(rows),
        "by_source": dict(sorted(by_source.items())),
        "by_sentiment": dict(sorted(by_sentiment.items())),
        "by_category": dict(sorted(by_category.items())),
        "unique_tickers": sorted(tickers),
        "unique_ticker_count": len(tickers),
        "high_tradeable_count": high_tradeable,
    }


def _signals_summary(signals) -> dict:
    if not isinstance(signals, dict):
        signals = {}

    active = []
    hard_blocks = []
    bullish = []
    bearish = []

    for ticker, sig in signals.items():
        if not isinstance(sig, dict):
            continue
        row = {
            "ticker": str(ticker).upper(),
            "score_delta": _safe_float(sig.get("score_delta")),
            "catalyst": sig.get("catalyst") or "",
            "sentiment": sig.get("sentiment") or "",
            "tradeable_score": _safe_float(sig.get("tradeable_score")),
            "action_window": sig.get("action_window") or "",
            "hard_block": bool(sig.get("hard_block")),
            "headline": sig.get("headline") or "",
            "added_at": sig.get("added_at") or "",
            "expires": sig.get("expires") or "",
        }
        active.append(row)
        if row["hard_block"]:
            hard_blocks.append(row["ticker"])
        elif row["score_delta"] > 0:
            bullish.append(row["ticker"])
        elif row["score_delta"] < 0:
            bearish.append(row["ticker"])

    active.sort(key=lambda x: (-abs(x["score_delta"]), x["ticker"]))

    return {
        "count": len(active),
        "bullish_count": len(bullish),
        "bearish_count": len(bearish),
        "hard_block_count": len(hard_blocks),
        "bullish_tickers": sorted(bullish),
        "bearish_tickers": sorted(bearish),
        "hard_blocks": sorted(hard_blocks),
        "items": active,
    }


def _watchlist_summary(watchlist) -> dict:
    items = []
    if isinstance(watchlist, dict):
        raw = watchlist.get("items", [])
        if isinstance(raw, list):
            items = [x for x in raw if isinstance(x, dict)]
    elif isinstance(watchlist, list):
        items = [x for x in watchlist if isinstance(x, dict)]

    tickers = sorted({str(x.get("ticker") or "").upper() for x in items if x.get("ticker")})
    bullish = sorted({str(x.get("ticker") or "").upper() for x in items if x.get("sentiment") == "bullish" and x.get("ticker")})
    bearish = sorted({str(x.get("ticker") or "").upper() for x in items if x.get("sentiment") == "bearish" and x.get("ticker")})

    return {
        "count": len(items),
        "tickers": tickers,
        "bullish_count": len(bullish),
        "bearish_count": len(bearish),
        "bullish_tickers": bullish,
        "bearish_tickers": bearish,
        "top_items": sorted(
            [
                {
                    "ticker": x.get("ticker"),
                    "tradeable_score": _safe_float(x.get("tradeable_score")),
                    "sentiment": x.get("sentiment") or "",
                    "category": x.get("category") or "",
                    "action_window": x.get("action_window") or "",
                    "headline": x.get("headline") or "",
                    "added_at": x.get("added_at") or "",
                    "updated_at": x.get("updated_at") or "",
                }
                for x in items
            ],
            key=lambda x: (-x["tradeable_score"], str(x["ticker"] or "")),
        )[:20],
    }


def _late_ideas_summary(rows: list[dict]) -> dict:
    news_rows = [r for r in rows if r.get("source") in {"news_signal", "watchlist"}]
    return {
        "count": len(rows),
        "news_or_watchlist_count": len(news_rows),
        "tickers": sorted({str(r.get("ticker") or "").upper() for r in rows if r.get("ticker")}),
        "news_or_watchlist_tickers": sorted({str(r.get("ticker") or "").upper() for r in news_rows if r.get("ticker")}),
        "items": [
            {
                "ticker": r.get("ticker"),
                "source": r.get("source"),
                "score": _safe_float(r.get("score")),
                "tradeable_score": _safe_float(r.get("tradeable_score")),
                "score_delta": _safe_float(r.get("score_delta")),
                "action_window": r.get("action_window") or "",
                "watch_only": r.get("watch_only") is True,
                "mode": r.get("mode") or "",
                "headline": r.get("headline") or "",
            }
            for r in rows
        ],
    }


def _run_status_summary(rows: list[dict]) -> dict:
    latest = rows[-1] if rows else {}
    totals = {
        "items_fetched": sum(int(r.get("items_fetched") or 0) for r in rows),
        "items_classified": sum(int(r.get("items_classified") or 0) for r in rows),
        "signals_added": sum(int(r.get("signals_added") or 0) for r in rows),
        "hard_blocks": sum(int(r.get("hard_blocks") or 0) for r in rows),
        "watchlist_added": sum(int(r.get("watchlist_added") or 0) for r in rows),
    }
    return {
        "count": len(rows),
        "totals": totals,
        "latest_result": latest.get("result") or "",
        "latest_timestamp_et": latest.get("timestamp_et") or "",
        "latest_github_run_id": (latest.get("github") or {}).get("run_id", ""),
        "lookback_minutes_latest": latest.get("lookback_minutes"),
    }


def _official_picks_news_summary(rows: list[dict], date_str: str) -> dict:
    date_rows = [r for r in rows if r.get("pick_date") == date_str]
    with_news = []
    watch_only = []

    for r in date_rows:
        has_news = bool(
            r.get("news_action_window")
            or _safe_float(r.get("news_boost"), 0.0)
            or r.get("watch_only_reason")
        )
        if str(r.get("watch_only") or "").lower() == "true":
            watch_only.append(r.get("ticker"))
        if has_news:
            with_news.append({
                "ticker": r.get("ticker"),
                "trade_type": r.get("trade_type"),
                "watch_only": str(r.get("watch_only") or "").lower() == "true",
                "watch_only_reason": r.get("watch_only_reason") or "",
                "news_action_window": r.get("news_action_window") or "",
                "score": _safe_float(r.get("score")),
            })

    return {
        "date": date_str,
        "official_pick_rows": len(date_rows),
        "with_news_fields_count": len(with_news),
        "watch_only_count": len(watch_only),
        "watch_only_tickers": sorted([str(x).upper() for x in watch_only if x]),
        "items": with_news,
    }


def _outcomes_summary(rows: list[dict]) -> dict:
    by_status: dict[str, int] = {}
    evaluated = []

    for row in rows:
        status = str(row.get("status") or "unknown")
        by_status[status] = by_status.get(status, 0) + 1
        if status == "evaluated":
            evaluated.append(row)

    one_d_vals = [
        _safe_float(r.get("one_d_return_pct"), None)
        for r in evaluated
        if _safe_float(r.get("one_d_return_pct"), None) is not None
    ]
    horizon_vals = [
        _safe_float(r.get("horizon_return_pct"), None)
        for r in evaluated
        if _safe_float(r.get("horizon_return_pct"), None) is not None
    ]

    avg_one_d = round(sum(one_d_vals) / len(one_d_vals), 4) if one_d_vals else None
    avg_horizon = round(sum(horizon_vals) / len(horizon_vals), 4) if horizon_vals else None

    top_evaluated = sorted(
        [
            {
                "ticker": r.get("ticker") or "",
                "source": r.get("source") or "",
                "signal_timestamp": r.get("signal_timestamp") or "",
                "sentiment": r.get("sentiment") or "",
                "category": r.get("category") or "",
                "tradeable_score": _safe_float(r.get("tradeable_score")),
                "score_delta": _safe_float(r.get("score_delta")),
                "one_d_return_pct": _safe_float(r.get("one_d_return_pct"), None),
                "horizon_return_pct": _safe_float(r.get("horizon_return_pct"), None),
                "headline": r.get("headline") or "",
            }
            for r in evaluated
        ],
        key=lambda x: (
            -abs(x["horizon_return_pct"] or 0),
            -abs(x["one_d_return_pct"] or 0),
            str(x["ticker"]),
        ),
    )[:20]

    return {
        "count": len(rows),
        "by_status": dict(sorted(by_status.items())),
        "evaluated_count": len(evaluated),
        "avg_one_d_return_pct": avg_one_d,
        "avg_horizon_return_pct": avg_horizon,
        "top_evaluated": top_evaluated,
    }


def build_report(date_str: str, data_dir: Path = DATA_DIR) -> dict:
    news_log_path = data_dir / "news_log.jsonl"
    signals_path = data_dir / "news_signals.json"
    watchlist_path = data_dir / "watchlist.json"
    run_status_path = data_dir / f"news_engine_run_status_{date_str}.jsonl"
    late_ideas_path = data_dir / f"late_daily_ideas_{date_str}.jsonl"
    outcomes_path = data_dir / f"news_signal_outcomes_{date_str}.jsonl"
    picks_path = data_dir / "picks_log.csv"

    news_rows, news_invalid = load_jsonl(news_log_path)
    status_rows, status_invalid = load_jsonl(run_status_path)
    late_rows, late_invalid = load_jsonl(late_ideas_path)
    outcome_rows, outcome_invalid = load_jsonl(outcomes_path)

    report = {
        "artifact": "news_signal_evidence_report",
        "date": date_str,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "mode": "monitoring_only",
        "read_only": True,
        "official_pick_stats_mutated": False,
        "paper_trading_enabled": False,
        "live_trading_enabled": False,
        "paths": {
            "news_log": str(news_log_path),
            "news_signals": str(signals_path),
            "watchlist": str(watchlist_path),
            "news_engine_run_status": str(run_status_path),
            "late_daily_ideas": str(late_ideas_path),
            "news_signal_outcomes": str(outcomes_path),
            "picks_log": str(picks_path),
        },
        "exists": {
            "news_log": news_log_path.exists(),
            "news_signals": signals_path.exists(),
            "watchlist": watchlist_path.exists(),
            "news_engine_run_status": run_status_path.exists(),
            "late_daily_ideas": late_ideas_path.exists(),
            "news_signal_outcomes": outcomes_path.exists(),
            "picks_log": picks_path.exists(),
        },
        "invalid_json_lines": {
            "news_log": news_invalid,
            "news_engine_run_status": status_invalid,
            "late_daily_ideas": late_invalid,
            "news_signal_outcomes": outcome_invalid,
        },
        "news_log": _news_log_summary(news_rows),
        "active_news_signals": _signals_summary(load_json(signals_path, {})),
        "watchlist": _watchlist_summary(load_json(watchlist_path, {})),
        "news_engine_run_status": _run_status_summary(status_rows),
        "late_daily_ideas": _late_ideas_summary(late_rows),
        "news_signal_outcomes": _outcomes_summary(outcome_rows),
        "official_picks_news_usage": _official_picks_news_summary(load_csv(picks_path), date_str),
    }

    return report


def format_markdown(report: dict) -> str:
    lines = [
        f"# News Signal Evidence Report — {report['date']}",
        "",
        "Read-only monitoring report. Does not mutate official picks, journals, paper trading, or live trading.",
        "",
        "## Safety",
        "",
        f"- Mode: **{report['mode']}**",
        f"- Read-only: **{str(report['read_only']).lower()}**",
        f"- Official pick stats mutated: **{str(report['official_pick_stats_mutated']).lower()}**",
        f"- Paper trading enabled: **{str(report['paper_trading_enabled']).lower()}**",
        f"- Live trading enabled: **{str(report['live_trading_enabled']).lower()}**",
        "",
        "## Run status",
        "",
    ]

    status = report["news_engine_run_status"]
    lines.extend([
        f"- Run-status rows for date: **{status['count']}**",
        f"- Items fetched total: **{status['totals']['items_fetched']}**",
        f"- Items classified total: **{status['totals']['items_classified']}**",
        f"- Signals added total: **{status['totals']['signals_added']}**",
        f"- Watchlist additions total: **{status['totals']['watchlist_added']}**",
        f"- Latest result: **{status['latest_result'] or 'n/a'}**",
        f"- Latest lookback minutes: **{status['lookback_minutes_latest'] or 'n/a'}**",
        "",
        "## News log",
        "",
    ])

    news = report["news_log"]
    lines.extend([
        f"- Classified news rows: **{news['count']}**",
        f"- Unique tickers mentioned: **{news['unique_ticker_count']}**",
        f"- High-tradeable rows (>=0.85): **{news['high_tradeable_count']}**",
        f"- Sources: `{news['by_source']}`",
        f"- Sentiment: `{news['by_sentiment']}`",
        "",
        "## Active news signals",
        "",
    ])

    signals = report["active_news_signals"]
    lines.extend([
        f"- Active signals: **{signals['count']}**",
        f"- Bullish: **{signals['bullish_count']}**",
        f"- Bearish: **{signals['bearish_count']}**",
        f"- Hard blocks: **{signals['hard_block_count']}**",
    ])
    if signals["items"]:
        for item in signals["items"][:20]:
            lines.append(
                f"- **{item['ticker']}** {item['score_delta']:+.3f} "
                f"{item['catalyst']} window={item['action_window']} "
                f"hard_block={str(item['hard_block']).lower()}"
            )
    else:
        lines.append("- No active news signals found.")

    watchlist = report["watchlist"]
    lines.extend([
        "",
        "## Watchlist",
        "",
        f"- Watchlist items: **{watchlist['count']}**",
        f"- Bullish watchlist items: **{watchlist['bullish_count']}**",
        f"- Bearish watchlist items: **{watchlist['bearish_count']}**",
    ])
    if watchlist["top_items"]:
        for item in watchlist["top_items"][:20]:
            lines.append(
                f"- **{item['ticker']}** score={item['tradeable_score']:.2f} "
                f"sentiment={item['sentiment']} category={item['category']} "
                f"window={item['action_window']}"
            )
    else:
        lines.append("- No watchlist items found.")

    outcomes = report["news_signal_outcomes"]
    lines.extend([
        "",
        "## News signal outcomes",
        "",
        f"- Outcome rows: **{outcomes['count']}**",
        f"- Evaluated rows: **{outcomes['evaluated_count']}**",
        f"- Status counts: `{outcomes['by_status']}`",
        f"- Average 1D return: **{outcomes['avg_one_d_return_pct'] if outcomes['avg_one_d_return_pct'] is not None else 'n/a'}**",
        f"- Average horizon return: **{outcomes['avg_horizon_return_pct'] if outcomes['avg_horizon_return_pct'] is not None else 'n/a'}**",
    ])
    if outcomes["top_evaluated"]:
        for item in outcomes["top_evaluated"][:10]:
            lines.append(
                f"- **{item['ticker']}** 1D={item['one_d_return_pct']}% "
                f"horizon={item['horizon_return_pct']}% source={item['source']}"
            )
    else:
        lines.append("- No evaluated news signal outcomes found for this date.")

    late = report["late_daily_ideas"]
    official = report["official_picks_news_usage"]
    lines.extend([
        "",
        "## Late daily ideas",
        "",
        f"- Late ideas: **{late['count']}**",
        f"- From news/watchlist: **{late['news_or_watchlist_count']}**",
        f"- News/watchlist tickers: `{late['news_or_watchlist_tickers']}`",
        "",
        "## Official picks news usage",
        "",
        f"- Official pick rows for date: **{official['official_pick_rows']}**",
        f"- Rows with news fields: **{official['with_news_fields_count']}**",
        f"- Watch-only rows: **{official['watch_only_count']}**",
    ])
    if official["items"]:
        for item in official["items"]:
            lines.append(
                f"- **{item['ticker']}** type={item['trade_type']} "
                f"watch_only={str(item['watch_only']).lower()} "
                f"news_window={item['news_action_window'] or 'n/a'}"
            )
    else:
        lines.append("- No official pick rows with news fields found for this date.")

    lines.extend([
        "",
        "## Next evidence gap",
        "",
        "This report inventories news evidence. It does not yet join signal timestamps to future price outcomes.",
    ])

    return "\n".join(lines) + "\n"


def write_outputs(report: dict, data_dir: Path = DATA_DIR) -> tuple[Path, Path]:
    data_dir.mkdir(parents=True, exist_ok=True)
    date_str = report["date"]
    json_path = data_dir / f"news_signal_evidence_report_{date_str}.json"
    md_path = data_dir / f"news_signal_evidence_report_{date_str}.md"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(format_markdown(report), encoding="utf-8")
    return json_path, md_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default=_today_et())
    parser.add_argument("--data-dir", default=str(DATA_DIR))
    parser.add_argument("--no-write", action="store_true")
    args = parser.parse_args(argv)

    report = build_report(args.date, data_dir=Path(args.data_dir))
    if args.no_write:
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0

    json_path, md_path = write_outputs(report, data_dir=Path(args.data_dir))
    print(f"[news-evidence] wrote {json_path}")
    print(f"[news-evidence] wrote {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
