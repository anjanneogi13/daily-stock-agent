#!/usr/bin/env python3
"""Daily watch-only learning evidence report.

This is a read-only, monitoring-only inventory/report over non-official ideas:
late daily watch-only ideas, intraday monitor fingerprints, and opening-range
observations.

It intentionally does NOT:
- create official picks,
- write data/picks_log.csv,
- write data/signal_journal.jsonl,
- write data/learning_journal.jsonl,
- create paper trades,
- enable paper/live trading,
- affect readiness gates.

Outputs:
- data/watch_only_learning_report_YYYY-MM-DD.json
- data/watch_only_learning_report_YYYY-MM-DD.md
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo


ET = ZoneInfo("America/New_York")
DATA_DIR = Path("data")


def today_et() -> str:
    return datetime.now(timezone.utc).astimezone(ET).strftime("%Y-%m-%d")


def load_jsonl(path: Path) -> tuple[list[dict], int]:
    rows: list[dict] = []
    invalid = 0
    if not path.exists():
        return rows, invalid
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            invalid += 1
            continue
        if isinstance(payload, dict):
            rows.append(payload)
        else:
            invalid += 1
    return rows, invalid


def load_json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _safe_float(value):
    try:
        if value in (None, "", "None"):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _dedupe_fingerprints(path: Path) -> list[str]:
    raw = load_json(path, [])
    if not isinstance(raw, list):
        return []
    return sorted(str(x) for x in raw if isinstance(x, str) and x)


def _fingerprint_prefix_counts(fingerprints: list[str]) -> dict:
    counts = Counter()
    for fp in fingerprints:
        prefix = fp.split("|", 1)[0] if "|" in fp else "UNKNOWN"
        counts[prefix] += 1
    return dict(sorted(counts.items()))


def _momentum_fingerprints(fingerprints: list[str]) -> list[str]:
    return [fp for fp in fingerprints if fp.startswith("NEW|")]


def _opening_range_fingerprints(fingerprints: list[str]) -> list[str]:
    return [fp for fp in fingerprints if fp.startswith("OR|")]


def summarize_late_ideas(rows: list[dict]) -> dict:
    tickers = sorted({str(r.get("ticker") or "").upper() for r in rows if r.get("ticker")})
    unsafe = [
        r.get("ticker")
        for r in rows
        if r.get("watch_only") is not True
        or r.get("mode") != "monitoring_only"
        or r.get("paper_trading_enabled") is not False
        or r.get("live_trading_enabled") is not False
    ]
    return {
        "count": len(rows),
        "tickers": tickers,
        "unsafe_count": len(unsafe),
        "invalid_safety_tickers": unsafe,
        "with_observation_levels": sum(
            1 for r in rows
            if r.get("watch_buy_price") is not None
            and r.get("watch_stop_loss") is not None
            and r.get("watch_take_profit") is not None
        ),
        "items": [
            {
                "ticker": r.get("ticker"),
                "company_name": r.get("company_name") or "",
                "idea_type": r.get("idea_type"),
                "source": r.get("source"),
                "score": _safe_float(r.get("score")),
                "action_window": r.get("action_window"),
                "entry_observe": r.get("watch_buy_price"),
                "stop_loss_observe": r.get("watch_stop_loss"),
                "take_profit_observe": r.get("watch_take_profit"),
                "risk_reward": r.get("risk_reward"),
                "reason": r.get("reason") or r.get("headline") or "",
            }
            for r in rows
        ],
    }


def summarize_opening_range(rows: list[dict]) -> dict:
    tickers = sorted({str(r.get("ticker") or "").upper() for r in rows if r.get("ticker")})
    unsafe = [
        r.get("ticker")
        for r in rows
        if r.get("watch_only") is not True
        or r.get("mode") != "monitoring_only"
        or r.get("scanner") != "opening_range"
    ]
    return {
        "count": len(rows),
        "tickers": tickers,
        "unsafe_count": len(unsafe),
        "invalid_safety_tickers": unsafe,
        "with_observation_levels": sum(
            1 for r in rows
            if r.get("entry_observe") is not None
            and r.get("stop_loss_observe") is not None
            and r.get("take_profit_observe") is not None
        ),
        "items": [
            {
                "ticker": r.get("ticker"),
                "scanner": r.get("scanner"),
                "score": _safe_float(r.get("score")),
                "entry_observe": r.get("entry_observe"),
                "stop_loss_observe": r.get("stop_loss_observe"),
                "take_profit_observe": r.get("take_profit_observe"),
                "breakout_pct": r.get("breakout_pct"),
                "volume_ratio": r.get("volume_ratio"),
                "reason": r.get("reason") or "",
            }
            for r in rows
        ],
    }


def summarize_intraday_momentum(rows: list[dict]) -> dict:
    tickers = sorted({str(r.get("ticker") or "").upper() for r in rows if r.get("ticker")})
    unsafe = [
        r.get("ticker")
        for r in rows
        if r.get("watch_only") is not True
        or r.get("mode") != "monitoring_only"
        or r.get("scanner") != "momentum"
        or r.get("paper_trading_enabled") is not False
        or r.get("live_trading_enabled") is not False
    ]
    return {
        "count": len(rows),
        "tickers": tickers,
        "unsafe_count": len(unsafe),
        "invalid_safety_tickers": unsafe,
        "with_observation_levels": sum(
            1 for r in rows
            if r.get("entry_observe") is not None
            and r.get("stop_loss_observe") is not None
            and r.get("take_profit_observe") is not None
        ),
        "items": [
            {
                "ticker": r.get("ticker"),
                "scanner": r.get("scanner"),
                "score": _safe_float(r.get("score")),
                "entry_observe": r.get("entry_observe"),
                "stop_loss_observe": r.get("stop_loss_observe"),
                "take_profit_observe": r.get("take_profit_observe"),
                "reason": r.get("reason") or "",
            }
            for r in rows
        ],
    }


def summarize_run_status(rows: list[dict]) -> dict:
    events = Counter(str(r.get("event") or "unknown") for r in rows)
    results = Counter(str(r.get("result") or "unknown") for r in rows)
    latest = rows[-1] if rows else {}
    return {
        "count": len(rows),
        "events": dict(sorted(events.items())),
        "results": dict(sorted(results.items())),
        "latest_event": latest.get("event"),
        "latest_result": latest.get("result"),
        "latest_github_run_id": (latest.get("github") or {}).get("run_id", ""),
        "latest_github_sha": (latest.get("github") or {}).get("sha", ""),
    }


def build_summary(date_str: str, data_dir: Path = DATA_DIR) -> dict:
    late_path = data_dir / f"late_daily_ideas_{date_str}.jsonl"
    or_path = data_dir / f"opening_range_observations_{date_str}.jsonl"
    status_path = data_dir / f"opening_range_run_status_{date_str}.jsonl"
    momentum_path = data_dir / f"intraday_momentum_observations_{date_str}.jsonl"
    dedupe_path = data_dir / f"intraday_alerts_{date_str}.json"
    markdown_path = data_dir / f"intraday_alert_{date_str}.md"

    late_rows, late_invalid = load_jsonl(late_path)
    or_rows, or_invalid = load_jsonl(or_path)
    status_rows, status_invalid = load_jsonl(status_path)
    momentum_rows, momentum_invalid = load_jsonl(momentum_path)
    fingerprints = _dedupe_fingerprints(dedupe_path)

    momentum = _momentum_fingerprints(fingerprints)
    opening_range_fp = _opening_range_fingerprints(fingerprints)

    return {
        "artifact": "watch_only_learning_report",
        "date": date_str,
        "mode": "monitoring_only",
        "watch_only": True,
        "official_pick_stats_included": False,
        "paper_trading_enabled": False,
        "live_trading_enabled": False,
        "ready_for_paper_trading": False,
        "safety_note": (
            "Watch-only evidence only. Not official picks, not paper trades, "
            "not live trades, not buy instructions."
        ),
        "inputs": {
            "late_daily_ideas": str(late_path),
            "opening_range_observations": str(or_path),
            "opening_range_run_status": str(status_path),
            "intraday_momentum_observations": str(momentum_path),
            "intraday_alerts_dedupe": str(dedupe_path),
            "intraday_alert_markdown": str(markdown_path),
        },
        "input_presence": {
            "late_daily_ideas": late_path.exists(),
            "opening_range_observations": or_path.exists(),
            "opening_range_run_status": status_path.exists(),
            "intraday_momentum_observations": momentum_path.exists(),
            "intraday_alerts_dedupe": dedupe_path.exists(),
            "intraday_alert_markdown": markdown_path.exists(),
        },
        "invalid_json_lines": {
            "late_daily_ideas": late_invalid,
            "opening_range_observations": or_invalid,
            "opening_range_run_status": status_invalid,
            "intraday_momentum_observations": momentum_invalid,
        },
        "late_daily_watch_only": summarize_late_ideas(late_rows),
        "opening_range_watch_only": summarize_opening_range(or_rows),
        "intraday_momentum_watch_only": summarize_intraday_momentum(momentum_rows),
        "intraday_dedupe_fingerprints": {
            "count": len(fingerprints),
            "prefix_counts": _fingerprint_prefix_counts(fingerprints),
            "momentum_count": len(momentum),
            "momentum_fingerprints": momentum,
            "opening_range_count": len(opening_range_fp),
            "opening_range_fingerprints": opening_range_fp,
            "structured_momentum_observations_available": False,
            "note": (
                "Momentum fingerprints prove alerts existed, but v1 lacks a "
                "structured momentum-observation artifact after Telegram send."
            ),
        },
        "opening_range_run_status": summarize_run_status(status_rows),
        "learning_gaps": [
            "No official P&L is counted in this report.",
            "Late watch-only ideas have observation levels but no outcome join yet.",
            "Opening-range observations need bar artifacts before backtest outcomes can evaluate.",
            "Generic intraday momentum alerts now have structured persistence when the latest monitor code runs; older days may only have dedupe fingerprints.",
        ],
    }


def format_markdown(summary: dict) -> str:
    late = summary["late_daily_watch_only"]
    opening = summary["opening_range_watch_only"]
    momentum = summary["intraday_momentum_watch_only"]
    dedupe = summary["intraday_dedupe_fingerprints"]
    status = summary["opening_range_run_status"]

    lines = [
        f"# Watch-Only Learning Report — {summary['date']}",
        "",
        "**Mode:** monitoring-only  ",
        "**Paper trading:** disabled  ",
        "**Live trading:** disabled  ",
        "**Official P&L counted:** no",
        "",
        "> Watch-only evidence only. Not official picks, not paper trades, not live trades, not buy instructions.",
        "",
        "## Summary",
        "",
        f"- Late daily watch-only ideas: **{late['count']}**",
        f"- Opening-range observations: **{opening['count']}**",
        f"- Structured intraday momentum observations: **{momentum['count']}**",
        f"- Intraday dedupe fingerprints: **{dedupe['count']}**",
        f"- Momentum fingerprints: **{dedupe['momentum_count']}**",
        f"- Opening-range run-status rows: **{status['count']}**",
        "",
        "## Late daily watch-only ideas",
        "",
    ]

    if late["items"]:
        for item in late["items"]:
            lines.append(
                f"- **{item['ticker']}** score={item['score']} "
                f"entry={item['entry_observe']} SL={item['stop_loss_observe']} "
                f"TP={item['take_profit_observe']} R/R={item['risk_reward']}"
            )
    else:
        lines.append("- None found.")

    lines += [
        "",
        "## Opening-range observations",
        "",
    ]
    if opening["items"]:
        for item in opening["items"]:
            lines.append(
                f"- **{item['ticker']}** score={item['score']} "
                f"entry={item['entry_observe']} SL={item['stop_loss_observe']} "
                f"TP={item['take_profit_observe']} breakout={item['breakout_pct']}% "
                f"volume={item['volume_ratio']}x"
            )
    else:
        lines.append("- None found.")

    lines += [
        "",
        "## Intraday momentum observations",
        "",
    ]
    if momentum["items"]:
        for item in momentum["items"]:
            lines.append(
                f"- **{item['ticker']}** score={item['score']} "
                f"entry={item['entry_observe']} SL={item['stop_loss_observe']} "
                f"TP={item['take_profit_observe']} reason={item['reason']}"
            )
    else:
        lines.append("- No structured momentum observations found.")

    lines += [
        "",
        "## Intraday momentum dedupe evidence",
        "",
    ]
    if dedupe["momentum_fingerprints"]:
        lines.append("Dedupe fingerprints found:")
        for fp in dedupe["momentum_fingerprints"]:
            lines.append(f"- `{fp}`")
    else:
        lines.append("- No momentum fingerprints found.")

    lines += [
        "",
        "## Run-status evidence",
        "",
        f"- Latest event: `{status['latest_event']}`",
        f"- Latest result: `{status['latest_result']}`",
        f"- Latest GitHub run id: `{status['latest_github_run_id']}`",
        "",
        "## Learning gaps / next steps",
        "",
    ]
    for gap in summary["learning_gaps"]:
        lines.append(f"- {gap}")

    lines += [
        "",
        "## Safety",
        "",
        "- `watch_only=true`",
        "- `mode=monitoring_only`",
        "- `paper_trading_enabled=false`",
        "- `live_trading_enabled=false`",
        "- `ready_for_paper_trading=false`",
        "- Do not treat this report as buy/sell instructions.",
        "",
    ]

    return "\n".join(lines)


def write_outputs(summary: dict, data_dir: Path = DATA_DIR) -> tuple[Path, Path]:
    data_dir.mkdir(parents=True, exist_ok=True)
    date_str = summary["date"]
    json_path = data_dir / f"watch_only_learning_report_{date_str}.json"
    md_path = data_dir / f"watch_only_learning_report_{date_str}.md"

    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(format_markdown(summary) + "\n", encoding="utf-8")
    return json_path, md_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default=today_et())
    parser.add_argument("--data-dir", default=str(DATA_DIR))
    parser.add_argument("--no-write", action="store_true", help="Print summary JSON without writing report artifacts.")
    args = parser.parse_args(argv)

    summary = build_summary(args.date, data_dir=Path(args.data_dir))
    if args.no_write:
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0

    json_path, md_path = write_outputs(summary, data_dir=Path(args.data_dir))
    print(f"[watch-only-report] wrote {json_path}")
    print(f"[watch-only-report] wrote {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
