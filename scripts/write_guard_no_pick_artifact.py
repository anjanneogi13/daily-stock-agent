#!/usr/bin/env python3
"""Write formal official no-pick artifacts for workflow guard skips.

This script is used before main.py runs, when the daily-picks workflow guard
decides the official premarket decision cannot proceed due to session/timing
constraints.

Supported guard causes:

- NO_PICK_MARKET_CLOSED
- NO_PICK_WINDOW_MISSED

Safety:

- no market data provider calls,
- no LLM calls,
- no Telegram/GitHub issue sends,
- no paper trading,
- no live trading.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.validate_daily_no_pick import validate_no_pick_report
from src.github_observability import github_observability_metadata
from src.market_calendar import next_trading_day, reason_market_closed
from src.premarket_decision_contract import (
    CONTRACT_VERSION,
    DECISION_OFFICIAL_NO_PICK,
    SCORING_VERSION,
    STRATEGY_LANE,
    STRATEGY_VERSION,
)


ET = ZoneInfo("America/New_York")

SUPPORTED_GUARD_CAUSES = {
    "NO_PICK_MARKET_CLOSED",
    "NO_PICK_WINDOW_MISSED",
}


def default_et_date() -> str:
    return datetime.now(ET).strftime("%Y-%m-%d")


def _now_utc_and_et() -> tuple[str, str]:
    now_utc = datetime.now(timezone.utc).replace(microsecond=0)
    return now_utc.isoformat().replace("+00:00", "Z"), now_utc.astimezone(ET).isoformat()


def _trace_ids(date_str: str, cause: str) -> dict:
    run_id = os.getenv("GITHUB_RUN_ID", "local")
    commit_sha = os.getenv("GITHUB_SHA", "local")
    short_sha = str(commit_sha or "local")[:12]
    artifact_filename = f"daily_picks_no_pick_report_{date_str}.json"
    return {
        "decision_id": f"{STRATEGY_LANE}:{date_str}:NO_PICK:{cause}:{run_id}:{short_sha}",
        "artifact_id": f"daily_picks_no_pick_report:{date_str}:{cause}",
        "artifact_filename": artifact_filename,
        "artifact_path": str(Path("data") / artifact_filename),
    }


def _status_for_cause(cause: str) -> tuple[str, str, str]:
    if cause == "NO_PICK_MARKET_CLOSED":
        return "not_ready_market_closed", "healthy", "market_closed"
    if cause == "NO_PICK_WINDOW_MISSED":
        return "not_ready_window_missed", "healthy", "official_window_missed"
    return "readiness_uncertain", "unknown", "guard_skip"


def _default_reason(cause: str, date_str: str) -> str:
    if cause == "NO_PICK_MARKET_CLOSED":
        closed_reason = reason_market_closed(date_str) or "market calendar closed"
        try:
            next_open = next_trading_day(date_str).isoformat()
        except Exception:
            next_open = "unknown"
        return (
            f"No official premarket pick was generated because the US market is closed "
            f"for {date_str} ({closed_reason}). Next trading day: {next_open}."
        )

    if cause == "NO_PICK_WINDOW_MISSED":
        return (
            "No official premarket pick was generated because the workflow ran after "
            "the 09:20 ET official cutoff. The system must not fabricate a normal "
            "daily pick after the official window is missed."
        )

    return f"No official premarket pick was generated due to guard cause {cause}."


def build_guard_no_pick_artifact(
    *,
    date_str: str,
    cause: str,
    reason: str | None = None,
) -> dict:
    if cause not in SUPPORTED_GUARD_CAUSES:
        raise ValueError(f"unsupported guard no-pick cause: {cause}")

    timestamp_utc, selection_time_et = _now_utc_and_et()
    observability = github_observability_metadata()
    data_readiness_status, provider_status, market_session_status = _status_for_cause(cause)
    summary = reason or _default_reason(cause, date_str)
    trace = _trace_ids(date_str, cause)

    pipeline = {
        "guard_skip": True,
        "guard_cause": cause,
        "universe_count": 0,
        "fetched_count": 0,
        "scored_count": 0,
        "filtered_count": 0,
        "capped_count": 0,
        "final_pick_count": 0,
    }
    diagnostics = {
        "guard_skip": True,
        "guard_cause": cause,
        "guard_reason": summary,
        "workflow_run_id": os.getenv("GITHUB_RUN_ID", "local"),
    }

    payload = {
        "artifact": "daily_picks_no_pick_report",
        "date": date_str,
        "timestamp_utc": timestamp_utc,
        "decision": DECISION_OFFICIAL_NO_PICK,
        **trace,
        "strategy_lane": STRATEGY_LANE,
        "contract_version": CONTRACT_VERSION,
        "strategy_version": STRATEGY_VERSION,
        "scoring_version": SCORING_VERSION,
        "config_version": os.getenv("CONFIG_VERSION", "config.yaml"),
        "selection_time_et": selection_time_et,
        "workflow_run_id": os.getenv("GITHUB_RUN_ID", "local"),
        "commit_sha": os.getenv("GITHUB_SHA", "local"),
        **observability,
        "mode": "monitoring_only",
        "official_premarket_pick": False,
        "primary_no_pick_cause": cause,
        "secondary_causes": [],
        "human_readable_summary": summary,
        "reason": summary,
        "data_readiness_status": data_readiness_status,
        "provider_status": provider_status,
        "market_session_status": market_session_status,
        "pipeline": pipeline,
        "candidate_diagnostics": diagnostics,
        "diagnostics": diagnostics,
        "watch_only_available": False,
        "next_action": "Do not fabricate official picks. Treat this as a valid official no-pick decision.",
        "paper_trading_enabled": False,
        "live_trading_enabled": False,
        "ready_for_paper_trading": False,
    }
    return payload


def write_guard_no_pick_artifact(
    *,
    date_str: str,
    cause: str,
    data_dir: Path = Path("data"),
    reason: str | None = None,
) -> dict:
    data_dir.mkdir(parents=True, exist_ok=True)
    payload = build_guard_no_pick_artifact(date_str=date_str, cause=cause, reason=reason)

    errors = validate_no_pick_report(payload)
    if errors:
        raise RuntimeError("guard no-pick artifact failed validation: " + "; ".join(errors))

    json_path = data_dir / f"daily_picks_no_pick_report_{date_str}.json"
    payload["artifact_path"] = str(json_path)
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    md_path = data_dir / f"daily_picks_no_pick_report_{date_str}.md"
    md_path.write_text(
        "\n".join([
            "# Daily Picks Official No-Pick Guard Decision",
            "",
            "Monitoring-only official no-pick artifact. Not buy instructions.",
            "",
            f"- Date: **{date_str}**",
            f"- Primary no-pick cause: **{cause}**",
            f"- Decision ID: `{payload['decision_id']}`",
            f"- Artifact ID: `{payload['artifact_id']}`",
            f"- Summary: **{payload['human_readable_summary']}**",
            "- Paper trading enabled: **false**",
            "- Live trading enabled: **false**",
            "",
        ]),
        encoding="utf-8",
    )

    return {
        "date": date_str,
        "cause": cause,
        "json_path": str(json_path),
        "markdown_path": str(md_path),
        "decision_id": payload["decision_id"],
        "artifact_id": payload["artifact_id"],
        "valid": True,
        "paper_trading_enabled": False,
        "live_trading_enabled": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default=default_et_date(), help="ET date, YYYY-MM-DD")
    parser.add_argument("--cause", required=True, choices=sorted(SUPPORTED_GUARD_CAUSES))
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--reason", default="")
    args = parser.parse_args()

    try:
        result = write_guard_no_pick_artifact(
            date_str=args.date,
            cause=args.cause,
            data_dir=Path(args.data_dir),
            reason=args.reason or None,
        )
    except Exception as exc:
        print(f"❌ Failed to write guard no-pick artifact: {exc}")
        return 1

    print("✅ Wrote valid official guard no-pick artifact")
    print(f"- date: {result['date']}")
    print(f"- cause: {result['cause']}")
    print(f"- json_path: {result['json_path']}")
    print(f"- markdown_path: {result['markdown_path']}")
    print(f"- decision_id: {result['decision_id']}")
    print("- paper_trading_enabled: false")
    print("- live_trading_enabled: false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
