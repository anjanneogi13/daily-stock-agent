#!/usr/bin/env python3
"""Append a daily-picks workflow/run-status event.

Monitoring-only operational observability.

This script records whether the daily-picks workflow/watchdog started, skipped,
missed the premarket window, logged picks, sent Telegram, or failed a persistence
step. It does not generate picks, send trades, enable paper trading, or mutate
trading state.

Output:
    data/daily_picks_run_status_YYYY-MM-DD.jsonl
"""
from __future__ import annotations

import argparse
import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo


ET = ZoneInfo("America/New_York")


def today_picks_count(date_str: str, picks_path: Path = Path("data/picks_log.csv")) -> int:
    if not picks_path.exists():
        return 0
    try:
        with picks_path.open(newline="") as f:
            return sum(1 for row in csv.DictReader(f) if (row.get("pick_date") or "").strip() == date_str)
    except Exception:
        return 0


def status_path(date_str: str, data_dir: Path | None = None) -> Path:
    data_dir = data_dir or Path(os.getenv("DAILY_PICKS_STATUS_DATA_DIR", "data"))
    return data_dir / f"daily_picks_run_status_{date_str}.jsonl"


def _parse_bool(value: str | None):
    if value is None or value == "":
        return None
    return str(value).strip().lower() in {"1", "true", "yes", "y", "sent", "success"}


def build_record(
    *,
    event: str,
    result: str,
    reason: str = "",
    picks_logged: int | None = None,
    telegram_sent: str | None = None,
    late_ideas_count: int | None = None,
    workflow: str = "daily-picks",
    mode: str = "monitoring_only",
    now: datetime | None = None,
) -> dict:
    now_et = now.astimezone(ET) if now else datetime.now(ET)
    date_str = now_et.strftime("%Y-%m-%d")
    if picks_logged is None:
        picks_logged = today_picks_count(date_str)

    return {
        "date": date_str,
        "timestamp_et": now_et.isoformat(),
        "timestamp_utc": now_et.astimezone(timezone.utc).isoformat(),
        "workflow": workflow,
        "event": event,
        "result": result,
        "reason": reason,
        "picks_logged": int(picks_logged),
        "telegram_sent": _parse_bool(telegram_sent),
        "late_ideas_count": late_ideas_count,
        "mode": mode,
        "paper_trading_enabled": False,
        "live_trading_enabled": False,
        "official_premarket_pick": event in {
            "guard_passed",
            "agent_started",
            "agent_completed",
            "verify_csv_success",
            "telegram_daily_success",
        },
        "github": {
            "workflow": os.getenv("GITHUB_WORKFLOW", ""),
            "event_name": os.getenv("GITHUB_EVENT_NAME", ""),
            "run_id": os.getenv("GITHUB_RUN_ID", ""),
            "run_attempt": os.getenv("GITHUB_RUN_ATTEMPT", ""),
            "sha": os.getenv("GITHUB_SHA", ""),
            "ref": os.getenv("GITHUB_REF", ""),
        },
    }


def append_record(record: dict, data_dir: Path | None = None) -> Path:
    path = status_path(record["date"], data_dir=data_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, sort_keys=True) + "\n")
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--event", required=True)
    parser.add_argument("--result", required=True)
    parser.add_argument("--reason", default="")
    parser.add_argument("--picks-logged", type=int, default=None)
    parser.add_argument("--telegram-sent", default=None)
    parser.add_argument("--late-ideas-count", type=int, default=None)
    parser.add_argument("--workflow", default="daily-picks")
    parser.add_argument("--mode", default="monitoring_only")
    args = parser.parse_args(argv)

    record = build_record(
        event=args.event,
        result=args.result,
        reason=args.reason,
        picks_logged=args.picks_logged,
        telegram_sent=args.telegram_sent,
        late_ideas_count=args.late_ideas_count,
        workflow=args.workflow,
        mode=args.mode,
    )
    path = append_record(record)
    print(
        "[daily-picks-status] "
        f"{record['workflow']} {record['event']}={record['result']} "
        f"picks_logged={record['picks_logged']} -> {path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
