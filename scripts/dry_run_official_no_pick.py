#!/usr/bin/env python3
"""Synthetic official no-pick dry-run validation for Lane 1.

This script validates the official no-pick artifact path without calling market
data providers, LLMs, Telegram, or GitHub.

It can validate one no-pick cause or all allowed no-pick causes.

Safety:
- no live data calls,
- no real picks,
- no alerts,
- no paper/live trading,
- writes only to an isolated dry-run directory unless explicitly configured.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.validate_daily_no_pick import validate_no_pick_report
from src.premarket_decision_contract import (
    CONTRACT_VERSION,
    DECISION_OFFICIAL_NO_PICK,
    OFFICIAL_NO_PICK_ALLOWED_PRIMARY_CAUSES,
    SCORING_VERSION,
    STRATEGY_LANE,
    STRATEGY_VERSION,
)


ET = ZoneInfo("America/New_York")


def _default_date() -> str:
    return datetime.now(ET).strftime("%Y-%m-%d")


def _status_for_cause(cause: str) -> tuple[str, str]:
    if cause == "NO_PICK_DATA_PROVIDER_DEGRADED":
        return "not_ready_data_provider_degraded", "degraded"
    if cause == "NO_PICK_DATA_READINESS_FAILED":
        return "not_ready_data_readiness_failed", "unknown"
    if cause in {"NO_PICK_NO_SCORED_CANDIDATES", "NO_PICK_FILTERS_REMOVED_ALL"}:
        return "ready_no_qualified_candidates", "healthy"
    if cause == "NO_PICK_ALL_FINALISTS_HARD_BLOCKED":
        return "ready_all_finalists_hard_blocked", "healthy"
    if cause == "NO_PICK_PREMARKET_SANITY_BLOCKED_ALL":
        return "ready_all_finalists_blocked_by_premarket_sanity", "healthy"
    if cause == "NO_PICK_RISK_GATE_BLOCKED_ALL":
        return "ready_all_finalists_blocked_by_portfolio_risk", "healthy"
    if cause == "NO_PICK_MARKET_CLOSED":
        return "not_ready_market_closed", "healthy"
    if cause == "NO_PICK_WINDOW_MISSED":
        return "not_ready_window_missed", "healthy"
    if cause == "NO_PICK_RUNTIME_FAILURE":
        return "not_ready_runtime_failure", "unknown"
    return "readiness_uncertain", "unknown"


def _summary_for_cause(cause: str) -> str:
    summaries = {
        "NO_PICK_DATA_PROVIDER_DEGRADED": "No official picks were generated because synthetic provider health was degraded.",
        "NO_PICK_DATA_READINESS_FAILED": "No official picks were generated because synthetic data readiness failed.",
        "NO_PICK_MARKET_CLOSED": "No official picks were generated because the synthetic market session was closed.",
        "NO_PICK_WINDOW_MISSED": "No official picks were generated because the synthetic official window was missed.",
        "NO_PICK_NO_SCORED_CANDIDATES": "No official picks were generated because no synthetic candidates survived scoring.",
        "NO_PICK_FILTERS_REMOVED_ALL": "No official picks were generated because synthetic filters removed all candidates.",
        "NO_PICK_ALL_FINALISTS_HARD_BLOCKED": "No official picks were generated because all synthetic finalists were hard-blocked.",
        "NO_PICK_PREMARKET_SANITY_BLOCKED_ALL": "No official picks were generated because all synthetic finalists failed premarket sanity.",
        "NO_PICK_RISK_GATE_BLOCKED_ALL": "No official picks were generated because all synthetic finalists failed portfolio risk.",
        "NO_PICK_RUNTIME_FAILURE": "No official picks were generated because a synthetic runtime failure was recorded.",
        "NO_PICK_UNKNOWN_POST_FILTER_GATING": "No official picks were generated because synthetic post-filter gating removed all picks.",
    }
    return summaries.get(cause, f"Synthetic official no-pick fixture for {cause}.")


def _fixture_pipeline_and_diagnostics(cause: str) -> tuple[dict, dict]:
    pipeline = {
        "dry_run": True,
        "universe_count": 3,
        "fetched_count": 3,
        "scored_count": 3,
        "filtered_count": 3,
        "capped_count": 2,
        "pre_hard_block_pick_count": 2,
        "hard_blocked_count": 0,
        "post_hard_block_pick_count": 2,
        "pre_premarket_sanity_pick_count": 2,
        "premarket_sanity_blocked_count": 0,
        "pre_portfolio_risk_pick_count": 2,
        "portfolio_risk_blocked_count": 0,
        "pre_missing_data_pick_count": 2,
        "missing_data_blocked_count": 0,
        "final_pick_count": 0,
    }
    diagnostics: dict = {
        "dry_run": True,
        "fixture_cause": cause,
        "selected_picks": [],
        "rejected_candidates": [],
    }

    if cause == "NO_PICK_DATA_PROVIDER_DEGRADED":
        pipeline.update({"fetched_count": 0, "scored_count": 0, "filtered_count": 0, "capped_count": 0})
        diagnostics["market_data_health"] = {
            "providers": {"synthetic": {"attempts": 3, "successes": 0, "errors": 3}},
        }
    elif cause == "NO_PICK_DATA_READINESS_FAILED":
        diagnostics["readiness_gate"] = {
            "passed": False,
            "primary_no_pick_cause": cause,
            "human_readable_summary": _summary_for_cause(cause),
        }
    elif cause == "NO_PICK_MARKET_CLOSED":
        diagnostics["market_session"] = {"is_open": False, "reason": "synthetic market holiday"}
    elif cause == "NO_PICK_WINDOW_MISSED":
        diagnostics["market_session"] = {"window_missed": True, "cutoff_et": "09:20"}
    elif cause == "NO_PICK_NO_SCORED_CANDIDATES":
        pipeline.update({"scored_count": 0, "filtered_count": 0, "capped_count": 0})
    elif cause == "NO_PICK_FILTERS_REMOVED_ALL":
        pipeline.update({"filtered_count": 0, "capped_count": 0})
        diagnostics["rejected_candidates"] = [{"ticker": "DRY1", "rejection_stage": "filters", "reason": "synthetic filter"}]
    elif cause == "NO_PICK_ALL_FINALISTS_HARD_BLOCKED":
        pipeline.update({"hard_blocked_count": 2, "post_hard_block_pick_count": 0})
        diagnostics["pre_hard_block_candidates"] = [{"ticker": "DRY1"}, {"ticker": "DRY2"}]
        diagnostics["hard_blocked_candidates"] = [
            {"ticker": "DRY1", "block_type": "synthetic_hard_block", "reason": "fixture"},
            {"ticker": "DRY2", "block_type": "synthetic_hard_block", "reason": "fixture"},
        ]
    elif cause == "NO_PICK_PREMARKET_SANITY_BLOCKED_ALL":
        pipeline.update({"premarket_sanity_blocked_count": 2})
        diagnostics["pre_premarket_sanity_candidates"] = [{"ticker": "DRY1"}, {"ticker": "DRY2"}]
        diagnostics["premarket_sanity_blocked_candidates"] = [
            {"ticker": "DRY1", "rejection_stage": "premarket_sanity", "action": "SKIP_TODAY", "reason": "fixture"},
            {"ticker": "DRY2", "rejection_stage": "premarket_sanity", "action": "WATCH_ONLY", "reason": "fixture"},
        ]
    elif cause == "NO_PICK_RISK_GATE_BLOCKED_ALL":
        pipeline.update({"portfolio_risk_blocked_count": 2})
        diagnostics["pre_portfolio_risk_candidates"] = [{"ticker": "DRY1"}, {"ticker": "DRY2"}]
        diagnostics["portfolio_risk_blocked_candidates"] = [
            {"ticker": "DRY1", "rejection_stage": "portfolio_risk", "block_type": "risk_limit", "reason": "fixture"},
            {"ticker": "DRY2", "rejection_stage": "portfolio_risk", "block_type": "max_positions", "reason": "fixture"},
        ]
    elif cause == "NO_PICK_RUNTIME_FAILURE":
        diagnostics["runtime_failure"] = True
        diagnostics["runtime_error"] = "synthetic runtime failure fixture"
    elif cause == "NO_PICK_UNKNOWN_POST_FILTER_GATING":
        diagnostics["unknown_post_filter_gating"] = True

    return pipeline, diagnostics


def build_no_pick_fixture(cause: str, date_str: str) -> dict:
    if cause not in OFFICIAL_NO_PICK_ALLOWED_PRIMARY_CAUSES:
        raise ValueError(f"unsupported no-pick cause: {cause}")

    data_readiness_status, provider_status = _status_for_cause(cause)
    pipeline, diagnostics = _fixture_pipeline_and_diagnostics(cause)
    summary = _summary_for_cause(cause)

    return {
        "artifact": "daily_picks_no_pick_report",
        "date": date_str,
        "timestamp_utc": f"{date_str}T12:30:00Z",
        "decision": DECISION_OFFICIAL_NO_PICK,
        "strategy_lane": STRATEGY_LANE,
        "contract_version": CONTRACT_VERSION,
        "strategy_version": STRATEGY_VERSION,
        "scoring_version": SCORING_VERSION,
        "config_version": "dry-run",
        "selection_time_et": f"{date_str}T08:30:00-04:00",
        "workflow_run_id": "dry-run",
        "commit_sha": "dry-run",
        "mode": "dry_run",
        "official_premarket_pick": False,
        "primary_no_pick_cause": cause,
        "secondary_causes": [],
        "human_readable_summary": summary,
        "reason": summary,
        "data_readiness_status": data_readiness_status,
        "provider_status": provider_status,
        "market_session_status": "premarket_dry_run",
        "pipeline": pipeline,
        "candidate_diagnostics": diagnostics,
        "diagnostics": diagnostics,
        "watch_only_available": False,
        "next_action": "Dry run only; do not fabricate official picks.",
        "paper_trading_enabled": False,
        "live_trading_enabled": False,
        "ready_for_paper_trading": False,
    }


def write_no_pick_fixture(cause: str, *, date_str: str, output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = build_no_pick_fixture(cause, date_str)
    path = output_dir / f"daily_picks_no_pick_report_{date_str}.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    md_path = output_dir / f"daily_picks_no_pick_report_{date_str}.md"
    md_path.write_text(
        "\n".join([
            "# Daily Picks Synthetic No-Pick Dry Run",
            "",
            "Dry-run artifact. Not a real official market decision.",
            "",
            f"- Date: **{date_str}**",
            f"- Primary cause: **{cause}**",
            f"- Summary: **{payload['human_readable_summary']}**",
            "- Paper trading enabled: **false**",
            "- Live trading enabled: **false**",
            "",
        ]),
        encoding="utf-8",
    )

    errors = validate_no_pick_report(payload)
    result = {
        "cause": cause,
        "date": date_str,
        "path": str(path),
        "markdown_path": str(md_path),
        "validation_errors": errors,
        "valid": not errors,
    }
    if errors:
        raise RuntimeError(f"{cause} no-pick fixture failed validation: {errors}")
    return result


def run_dry_run(*, output_dir: Path, date_str: str, cause: str = "all", keep: bool = False) -> dict:
    causes = (
        sorted(OFFICIAL_NO_PICK_ALLOWED_PRIMARY_CAUSES)
        if cause == "all"
        else [cause]
    )

    results = []
    for item in causes:
        cause_dir = output_dir / item if len(causes) > 1 else output_dir
        results.append(write_no_pick_fixture(item, date_str=date_str, output_dir=cause_dir))

    summary = {
        "dry_run": True,
        "date": date_str,
        "output_dir": str(output_dir),
        "cause": cause,
        "validated_cause_count": len(results),
        "allowed_cause_count": len(OFFICIAL_NO_PICK_ALLOWED_PRIMARY_CAUSES),
        "results": results,
        "paper_trading_enabled": False,
        "live_trading_enabled": False,
        "kept_output": keep,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / f"dry_run_official_no_pick_{date_str}.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=_default_date(), help="ET date for validation; defaults to today")
    parser.add_argument("--output-dir", default="", help="Directory for dry-run artifacts; defaults to a temporary directory")
    parser.add_argument("--cause", default="all", help="No-pick cause to validate, or 'all'")
    parser.add_argument("--keep", action="store_true", help="Keep temporary output directory")
    args = parser.parse_args()

    temp_dir = None
    if args.output_dir:
        output_dir = Path(args.output_dir)
        keep = True
    else:
        temp_dir = tempfile.mkdtemp(prefix="lane1-official-no-pick-dry-run-")
        output_dir = Path(temp_dir)
        keep = args.keep

    try:
        summary = run_dry_run(
            output_dir=output_dir,
            date_str=args.date,
            cause=args.cause,
            keep=keep,
        )
        print("✅ Lane 1 official no-pick dry-run passed")
        print(f"- date: {summary['date']}")
        print(f"- output_dir: {summary['output_dir']}")
        print(f"- cause: {summary['cause']}")
        print(f"- validated_cause_count: {summary['validated_cause_count']}")
        print("- paper_trading_enabled: false")
        print("- live_trading_enabled: false")
        for result in summary["results"]:
            print(f"- {result['cause']}: {result['path']}")
        return 0
    except Exception as exc:
        print(f"❌ Lane 1 official no-pick dry-run failed: {exc}")
        return 1
    finally:
        if temp_dir and not keep:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
