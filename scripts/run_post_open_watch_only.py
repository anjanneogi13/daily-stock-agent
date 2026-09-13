#!/usr/bin/env python3
"""Lane 2 v0 runner: post-open / late-daily watch-only opportunity lane.

Roadmap source: docs/planning/MULTI_LANE_IMPLEMENTATION_ROADMAP.md, Phase 3.

Produces exactly one Lane 2 outcome per invocation:

- data/post_open_watchlist_YYYY-MM-DD.json (+ Markdown report), or
- data/post_open_no_opportunity_YYYY-MM-DD.json

and always appends to the run-status ledger:

- data/post_open_run_status_YYYY-MM-DD.jsonl

Session rules (v0):

- only scans between 09:30 ET and 15:15 ET on trading days,
- outside that window a no-opportunity artifact records the honest cause,
- new-opportunity suppression after 15:15 ET matches the intraday lane rule.

Safety:

- watch-only, monitoring-only,
- NOT official picks; never mutates picks_log.csv, journals, or official artifacts,
- no paper trading, no live trading, no buy instructions,
- read-only over inputs; no network calls in v0.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.post_open_artifacts import (
    append_run_status,
    build_no_opportunity_payload,
    build_watchlist_payload,
    write_no_opportunity_artifact,
    write_watchlist_artifacts,
)
from src.post_open_scanner import scan_post_open_opportunities

ET = ZoneInfo("America/New_York")

SESSION_OPEN_ET = (9, 30)
NEW_OPPORTUNITY_CUTOFF_ET = (15, 15)


def classify_session_window(now_et: datetime, *, trading_day: bool) -> str:
    """Classify the ET session window for Lane 2 v0."""
    if not trading_day:
        return "market_closed"
    minutes = now_et.hour * 60 + now_et.minute
    if minutes < SESSION_OPEN_ET[0] * 60 + SESSION_OPEN_ET[1]:
        return "before_open"
    if minutes > NEW_OPPORTUNITY_CUTOFF_ET[0] * 60 + NEW_OPPORTUNITY_CUTOFF_ET[1]:
        return "after_new_opportunity_cutoff"
    return "open_window"


def _default_trading_day_checker(date_str: str) -> bool:
    try:
        from src.market_calendar import is_trading_day

        return bool(is_trading_day(datetime.strptime(date_str, "%Y-%m-%d").date()))
    except Exception:
        # Fail open for observability: the scanner itself is read-only and the
        # artifact records the uncertainty via inputs, never fake evidence.
        return True


def run_post_open_watch_only(
    *,
    date_str: str | None = None,
    now: datetime | None = None,
    data_dir: Path = Path("data"),
    min_score: float | None = None,
    max_results: int | None = None,
    ignore_session_window: bool = False,
    trading_day_checker=None,
    write: bool = True,
) -> dict:
    """Run the Lane 2 v0 scan and write exactly one decision artifact."""
    now_dt = now or datetime.now(timezone.utc)
    now_et = now_dt.astimezone(ET)
    date_str = date_str or now_et.strftime("%Y-%m-%d")

    checker = trading_day_checker or _default_trading_day_checker
    window = classify_session_window(now_et, trading_day=checker(date_str))

    if write:
        append_run_status(
            date_str=date_str,
            event="scan_started",
            data_dir=data_dir,
            session_window=window,
        )

    if window != "open_window" and not ignore_session_window:
        cause = {
            "market_closed": "NO_OPPORTUNITY_MARKET_CLOSED",
            "before_open": "NO_OPPORTUNITY_TOO_LATE_IN_SESSION",
            "after_new_opportunity_cutoff": "NO_OPPORTUNITY_TOO_LATE_IN_SESSION",
        }.get(window, "NO_OPPORTUNITY_TOO_LATE_IN_SESSION")
        summary = (
            f"Post-open watch-only scan skipped: session window is '{window}' at "
            f"{now_et.strftime('%H:%M ET')}. New watch-only opportunities are only "
            "observed between 09:30 and 15:15 ET on trading days."
        )
        payload = build_no_opportunity_payload(
            date_str=date_str,
            cause=cause,
            summary=summary,
            data_readiness={"session_window": window, "scan_performed": False},
            counts={},
        )
        result = {"decision": "no_opportunity", "payload": payload, "session_window": window}
        if write:
            result["paths"] = write_no_opportunity_artifact(payload, data_dir=data_dir)
            append_run_status(
                date_str=date_str,
                event="completed_no_opportunity",
                data_dir=data_dir,
                cause=cause,
                session_window=window,
            )
        return result

    scan_kwargs = {"date_str": date_str, "now": now_dt, "data_dir": data_dir}
    if min_score is not None:
        scan_kwargs["min_score"] = min_score
    if max_results is not None:
        scan_kwargs["max_results"] = max_results
    scan = scan_post_open_opportunities(**scan_kwargs)
    scan["data_readiness"]["session_window"] = window
    scan["data_readiness"]["scan_performed"] = True

    if not scan["opportunities"]:
        inputs_missing = not (
            scan["data_readiness"]["news_signals_available"]
            or scan["data_readiness"]["watchlist_available"]
        )
        if inputs_missing:
            cause = "NO_OPPORTUNITY_INPUTS_MISSING"
            summary = (
                "Post-open watch-only scan found no evidence inputs: news signals and "
                "watchlist artifacts are both missing. This is a data-availability "
                "outcome, not evidence that no opportunities existed."
            )
        elif scan["counts"]["stale_or_expired"] > 0 and scan["counts"]["rejected_or_below_threshold"] == 0:
            cause = "NO_OPPORTUNITY_NO_FRESH_SIGNALS"
            summary = (
                "Post-open watch-only scan found only stale/expired signals. "
                "No fresh post-open evidence qualified for watch-only observation."
            )
        else:
            cause = "NO_OPPORTUNITY_ALL_BELOW_THRESHOLD"
            summary = (
                "Post-open watch-only scan completed with fresh inputs, but no candidate "
                "met the watch-only evidence threshold. A disciplined no-opportunity "
                "outcome is a valid Lane 2 result."
            )
        payload = build_no_opportunity_payload(
            date_str=date_str,
            cause=cause,
            summary=summary,
            data_readiness=scan["data_readiness"],
            counts=scan["counts"],
        )
        result = {
            "decision": "no_opportunity",
            "payload": payload,
            "counts": scan["counts"],
            "session_window": window,
        }
        if write:
            result["paths"] = write_no_opportunity_artifact(payload, data_dir=data_dir)
            append_run_status(
                date_str=date_str,
                event="completed_no_opportunity",
                data_dir=data_dir,
                cause=cause,
                session_window=window,
                counts=scan["counts"],
            )
        return result

    payload = build_watchlist_payload(
        date_str=date_str,
        opportunities=scan["opportunities"],
        data_readiness=scan["data_readiness"],
    )
    result = {
        "decision": "watch_only_opportunities",
        "payload": payload,
        "counts": scan["counts"],
        "session_window": window,
    }
    if write:
        result["paths"] = write_watchlist_artifacts(payload, data_dir=data_dir)
        append_run_status(
            date_str=date_str,
            event="completed_watch_only_opportunities",
            data_dir=data_dir,
            opportunity_count=len(scan["opportunities"]),
            session_window=window,
            counts=scan["counts"],
        )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default=None, help="ET date, YYYY-MM-DD (default: today ET)")
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--min-score", type=float, default=None)
    parser.add_argument("--max-results", type=int, default=None)
    parser.add_argument(
        "--ignore-session-window",
        action="store_true",
        help="Scan even outside 09:30–15:15 ET (for manual evidence review only)",
    )
    parser.add_argument(
        "--no-write",
        action="store_true",
        help="Print the decision payload without writing artifacts",
    )
    args = parser.parse_args()

    result = run_post_open_watch_only(
        date_str=args.date,
        data_dir=Path(args.data_dir),
        min_score=args.min_score,
        max_results=args.max_results,
        ignore_session_window=args.ignore_session_window,
        write=not args.no_write,
    )

    if args.no_write:
        print(json.dumps(result["payload"], indent=2, sort_keys=True))
        return 0

    print("✅ Post-open watch-only lane run complete (Lane 2 v0)")
    print(f"- decision: {result['decision']}")
    print(f"- session_window: {result['session_window']}")
    for key, value in (result.get("paths") or {}).items():
        print(f"- {key}: {value}")
    print("- watch_only: true")
    print("- official_pick_stats_impact: none")
    print("- paper_trading_enabled: false")
    print("- live_trading_enabled: false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
